from __future__ import annotations

from enum import IntEnum
import resource
from asyncio import Task
import asyncio
import math
from typing import Any, Generator, Self
import logging
import random

from .mrfh import ManagedRotatingFileHandler
from .miner import Miner
from .node import Node
from .channel import Channel
from .paygraph import PayGraph
from .mtg import ManagedTaskGroup

NODES_PER_MINER: int = 100

class Lab:
    def __init__(self, graph: PayGraph) -> None:
        self.__graph: PayGraph = graph
        self.__miners: list[Miner] = []
        self.__connected_miners: list[str] = []
        self.__nodes: dict[str, Node] = {}
        self.__synced_nodes: list[str] = []
        self.__channel_utxos: dict[str, str] = {}
        self.__channels: dict[str, Channel] = {}

        self.__status: Lab.Status = Lab.Status.STOPPED

        log_handler: ManagedRotatingFileHandler = ManagedRotatingFileHandler(
            f"Logs/{self.name}.log",
            backupCount = 100,
            encoding = "utf-8"
        )
        
        logging.basicConfig(
            handlers = [
                log_handler
            ],
            level = logging.INFO,
            format = "%(asctime)s %(levelname)s %(message)s",
            encoding = "utf-8"
        )

        logging.getLogger("urllib3").setLevel(logging.WARNING)
        
        log_handler.doRollover()
    
    def __await__(self) -> Generator[Any, None, Self]:
        return self.start().__await__()

    @property
    def name(self) -> str:
        return self.__graph.name
    
    @property
    def total_miner_count(self) -> int:
        return math.ceil(len(self.__graph.nodes) / NODES_PER_MINER)
    
    @property
    def created_miner_count(self) -> int:
        return len(self.__miners)
    
    @property
    def connected_miner_count(self) -> int:
        return len(self.__connected_miners)
    
    @property
    def miners(self) -> list[Miner]:
        return self.__miners
    
    @property
    def total_node_count(self) -> int:
        return len(self.__graph.nodes)
    
    @property
    def created_node_count(self) -> int:
        return len(self.__nodes)
    
    @property
    def synced_node_count(self) -> int:
        return len(self.__synced_nodes)

    @property
    def nodes(self) -> dict[str, Node]:
        return self.__nodes
    
    @property
    def total_channel_count(self) -> int:
        return len(self.__graph.edges)
    
    @property
    def funded_channel_count(self) -> int:
        return len(self.__channel_utxos)
    
    @property
    def created_channel_count(self) -> int:
        return len(self.__channels)

    @property
    def channels(self) -> dict[str, Channel]:
        return self.__channels

    async def start(self) -> Self:
        if self.__status == Lab.Status.STOPPED:
            soft_limit = 4096 * 4
            hard_limit = 4096 * 8
            resource.setrlimit(resource.RLIMIT_NOFILE, (soft_limit, hard_limit))
            
            await self.create_miners()
            await self.create_nodes()
            await self.create_channels()
            await self.sync_mine(6)

            self.__status = Lab.Status.READY
        
        return self
    
    class Status(IntEnum):
        STOPPED = 0
        CREATE_MINERS = 1
        CONNECT_MINERS = 2
        CREATE_NODES_FUND_CHANNELS = 3
        CREATE_CHANNELS = 4
        SYNC_NODES = 5
        READY = 6
        STOPPING = 7
    
    @property
    def status(self) -> Status:
        return self.__status
        
    async def sync_mine(self, block_count: int) -> None:
        miner: Miner = random.choice(self.__miners)
        await miner.mine(block_count)
        new_block_height = await miner.get_block_height()

        if self.__status != Lab.Status.READY:
            self.__status = Lab.Status.SYNC_NODES

        self.__synced_nodes.clear()

        try:
            async with ManagedTaskGroup() as task_group:
                for node_key in self.__nodes:
                    node: Node = self.__nodes[node_key]
                    task: Task = task_group.create_task(
                        node.wait_for_block_height(new_block_height),
                        name = f"WAIT_SYNC {node_key}"                
                    )
                    task.add_done_callback(lambda t: self.__synced_nodes.append(t.get_name().split(" ")[1]))
        except ExceptionGroup as eg:
            for e in eg.exceptions:
                logging.error("WAIT_SYNC", eg.message, e)

        if self.__status != Lab.Status.READY:
            self.__status = Lab.Status.READY
    
    async def create_miners(self) -> None:

        self.__status = Lab.Status.CREATE_MINERS

        try:
            async with ManagedTaskGroup() as group:
                for i in range(self.total_miner_count):
                    self.__miners.insert(i, Miner())
                    group.create_task(
                        self.__miners[i].start(),
                        name = f"CREATE_MINER m{i}"
                    )
        except ExceptionGroup as eg:
            for e in eg.exceptions:
                logging.error("CREATE_MINER", eg.message, e)
        
        self.__status = Lab.Status.CONNECT_MINERS

        try:
            async with ManagedTaskGroup() as group:
                for i in range(self.total_miner_count - 1):
                    for j in range(i, self.total_miner_count):
                        task: Task = group.create_task(
                            self.__miners[i].connect(self.__miners[j]),
                            name = f"CONNECT_MINER m{i} m{j}"
                        )
                        task.add_done_callback(lambda t: self.__connected_miners.append(t.get_name().split(" ")[1]))
        except ExceptionGroup as eg:
            for e in eg.exceptions:
                logging.error("CONNECT_MINER", eg.message, e)

    async def create_nodes(self) -> None:
        self.__status = Lab.Status.CREATE_NODES_FUND_CHANNELS
        async def fund_channel(create_node_task: Task[Node], key: str) -> str:
            node: Node = await create_node_task
            node_address: str = await node.new_address()
            block_hash: str = (await self.__miners[0].mine(1, node_address))[0]
            txid: str = (await self.__miners[0].execute("getblock", block_hash))["tx"][0]
            self.__channel_utxos[key] = txid
            return txid
        try:
            async with ManagedTaskGroup() as group:
                for i, n in enumerate(self.__graph.nodes):
                    miner: Miner = self.__miners[i % len(self.__miners)]
                    self.__nodes[n] = Node(miner = miner)
                    create_task: Task = group.create_task(
                        self.__nodes[n].start(),
                        name = f"CREATE_NODE {n}"
                    )
                    for source, target, key in self.__graph.edges(n, keys = True):
                        if PayGraph.is_outbound_edge(key):
                            fund_channel_task: Task = group.create_task(
                                fund_channel(create_task, key),
                                name = f"FUND_CHANNEL {key}"
                            )
        except ExceptionGroup as eg:
            for e in eg.exceptions:
                logging.error("CREATE_NODE_FUND_CHANNEL", eg.message, e)

        await self.sync_mine(100)
    
    async def create_channels(self) -> None:
        self.__status = Lab.Status.CREATE_CHANNELS
        async def create_channel(key: str, source: str, target: str) -> str:
            out_key: str = key
            out_edge = self.__graph[source][target][out_key]
            in_key: str = PayGraph.get_inbound_edge_key(out_key)
            in_edge: Any = self.__graph[target][source][in_key]
            out_node: Node = self.__nodes[source]
            in_node: Node = self.__nodes[target]
            await out_node.connect(in_node)
            channel_id: str = await out_node.fund_channel(
                destination = in_node,
                capacity = out_edge["capacity"],
                balance = out_edge["balance"],
                utxo = f"{self.__channel_utxos[out_key]}:0"
            )
            self.__channels[out_key] = Channel(
                id = channel_id,
                source = out_node,
                destination = in_node
            )
            await self.__channels[out_key].set_fee(
                new_base_fee = out_edge["base_fee"],
                new_ppm_fee = out_edge["ppm_fee"]
            )
            self.__channels[in_key] = Channel(
                id = channel_id,
                source = in_node,
                destination = out_node
            )
            await self.__channels[in_key].set_fee(
                new_base_fee = in_edge["base_fee"],
                new_ppm_fee = in_edge["ppm_fee"]
            )
            return channel_id

        try:
            async with ManagedTaskGroup() as group:
                for source, target, key in self.__graph.edges(keys = True):
                    if PayGraph.is_outbound_edge(key):
                        group.create_task(
                            create_channel(key, source, target),
                            name = f"CREATE_CHANNEL {key}"
                        )
        except ExceptionGroup as eg:
            logging.error(f"CREATE_CHANNEL {eg.message}")
            for e in eg.exceptions:
                logging.error(f"CREATE_CHANNEL {e}")

    async def stop(self) -> None:
        if self.__status == Lab.Status.READY:
            self.__status = Lab.Status.STOPPING
            await self.stop_nodes()
            await self.stop_miners()
            self.__status = Lab.Status.STOPPED
    
    async def stop_nodes(self) -> None:
        try:
            async with ManagedTaskGroup() as group:
                for key, node in self.nodes.items():
                    task: Task = group.create_task(
                        node.stop(),
                        name = f"STOP_NODE {key}"
                    )
                    task.add_done_callback(lambda t: self.nodes.pop(t.get_name().split(" ")[1]))
        except ExceptionGroup as eg:
            for e in eg.exceptions:
                logging.error("STOP_NODES", eg.message, e)

    async def stop_miners(self) -> None:
        try:
            async with ManagedTaskGroup() as group:
                for i, miner in enumerate(self.miners):
                    task: Task = group.create_task(
                        miner.stop(),
                        name = f"STOP_MINER m{i}"
                    )
                    task.add_done_callback(lambda t: self.miners.pop(int(t.get_name().split(" m")[1])))
        except ExceptionGroup as eg:
            for e in eg.exceptions:
                logging.error("STOP_MINERS", eg.message, e)

    
