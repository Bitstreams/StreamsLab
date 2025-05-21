from __future__ import annotations
from asyncio import Lock, StreamReader, StreamWriter, sleep
import json
from typing import Any, Self, override

import httpx
import logging

logging.getLogger("httpx").setLevel(logging.CRITICAL)

from .miner import Miner
from .server import Server
import asyncio
import uuid
import logging

class Node(Server):
    def __init__(self, *, miner: Miner) -> None:
        super().__init__(
            image = "elementsproject/lightningd:v25.02.2",
            command = [
                f"--bitcoin-rpcuser={miner.username}",
                f"--bitcoin-rpcpassword={miner.password}",
                f"--bitcoin-rpcconnect={miner.name}",
                "--bitcoin-rpcclienttimeout=60",
                "--bitcoin-retry-timeout=3600",
                "--min-capacity-sat=0",
                "--clnrest-port=3010",
                "--clnrest-protocol=http",
                "--clnrest-host=0.0.0.0",
                "--log-level=debug"
            ],
            environment = {
                "LIGHTNINGD_NETWORK": "regtest",
                "EXPOSE_TCP": "true"
            },
            rpc_port = 3010
        )
        self.public_key: str
        self.__fund_channel_lock: Lock = Lock()
    
    def __str__(self) -> str:
        return self.name

    async def start(self) -> Self:
        if not self.is_running:
            await super().start()
            await self.wait_for(
                text = "no longer in startup mode"
            )

            exec_code, output = self.container.exec_run([
                "lightning-cli","--regtest", "commando-rune", "restrictions=[]"
            ])

            result = json.loads(output)

            if exec_code:
                raise result.message

            self.__rest_client: httpx.AsyncClient = httpx.AsyncClient(
                headers = {
                    "Rune": result["rune"]
                },
                timeout = 60
            )

            self.public_key = (await self.get_info())["id"]


            asyncio.create_task(self.__log_stats())

        return self
    
    async def __log_stats(self):
        while True:
            try:
                stats: str = await asyncio.to_thread(self.container.stats, stream = False)
            except Exception as e:
                break
            logging.info(f"STATS {stats}")
            await sleep(10)
    
    async def execute(self, *command: str, **kwargs) -> Any:
        response = None
        try:
            url = f"http://127.0.0.1:{self.host_rpc_port}/v1/{command[0]}"

            headers = {
                "Content-Type": "application/json"
            }

            payload = kwargs or {}

            response = await self.__rest_client.post(
                url=url,
                headers=headers,
                json=payload
            )

            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(response.json() if response else e)

    
    async def get_info(self):
        return await self.execute("getinfo")
    
    async def get_block_height(self) -> int:
        return int((await self.get_info())["blockheight"])
    
    async def wait_for_block_height(self, block_height: int):
        while await self.get_block_height() < block_height:
            await asyncio.sleep(10)

    async def connect(self, destination: Self) -> None:
        return await self.execute("connect", id = destination.public_key, host =destination.name)

    async def new_address(self) -> str:
        return (await self.execute("newaddr", addresstype = "bech32"))["bech32"]
    
    async def list_funds(self):
        return await self.execute("listfunds")

    async def fund_channel(
        self,
        *,
        destination: Self,
        capacity: int,
        balance: int,
        utxo: str
    ) -> str:
        async with self.__fund_channel_lock:
                fund_channel = await self.execute(
                    "fundchannel",
                    id = destination.public_key,
                    amount = int(capacity // 1_000),
                    push_msat = int(capacity) - int(balance),
                    utxos = [utxo]
                )
                return fund_channel["channel_id"]
    
    async def new_invoice(self, *, amount: int, description: str, expiry: int = 604_800):
        return await self.execute(
            "invoice",
            amount_msat = amount,
            label = str(uuid.uuid4()),
            description = description,
            expiry = expiry
        )
    
    async def get_route(self, destination: Node, amount: int):
        return await self.execute(
            "getroute",
            id = destination.public_key,
            amount_msat = amount,
            riskfactor = 10
        )
    
    async def pay_invoice(self, invoice, route = None) -> Any:
        return await self.execute("pay", bolt11 = invoice["bolt11"])