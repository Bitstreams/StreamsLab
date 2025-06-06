import json
from asyncio import Lock, sleep
from typing import Any, Final, Self, overload
from .server import Server
import httpx
import logging

class Miner(Server):
    __mine_lock: Final = Lock()

    def __init__(self) -> None:
        super().__init__(
            image =  "ruimarinho/bitcoin-core",
            command = [
                "-regtest=1",
                "-rpcallowip=0.0.0.0/0",
                f"-rpcbind=0.0.0.0:18443",
                "-server=1",
                "-listen=1",
                "-rest=1",
                "-listenonion=0",
                "-rpcworkqueue=10000"
            ],
            environment = None,
            control_port = 18443
        )

    async def start(self) -> Self:
        if not self.is_running:
            await super().start()

            await self.wait_for("Generated RPC authentication cookie")

            while True:
                try:
                    authentication_cookie: str = await self.read_file("/home/bitcoin/.bitcoin/regtest/.cookie")
                    break
                except Exception as e:
                    logging.warning("Unable to read cookie file", e)
                    await sleep(10)

            self.username, self.password = authentication_cookie.split(":")

            self._rest_client.auth = self.username, self.password
            self._rest_client.headers.update({
                    "Content-Type": "text/plain"
            })
            
            await self.execute("createwallet", "default")

        return self
    
    async def stop(self) -> None:
        return await super().stop()
        
    async def execute(self, *command: str | int, **kwargs) -> Any:

        parameters: list[Any] = []

        if len(command[1:]):
            for argument in command[1:]:
                parameters.append(argument)
        
        for argument in kwargs:
            parameters.append(argument)
        
        try:
            raw_response: httpx.Response = await self._rest_client.post(
                url = "/",
                content = json.dumps({
                    "jsonrpc": "2.0",
                    "method": command[0],
                    "params": parameters
                })
            )
        except Exception as e:
            logging.error(e)
            raise e

        response: Any = json.loads(raw_response.content)

        if response["error"]:
            raise RuntimeError({
                "code": response["error"]["code"],
                "message": response["error"]["message"]
            })

        return response["result"]
    
    async def get_blockchain_info(self) -> Any:
        return await self.execute("getblockchaininfo")
    
    async def get_block_height(self) -> int:
        return (await self.get_blockchain_info())["blocks"]

    async def connect(self, destination: Server) -> None:
        if not isinstance(destination, Miner):
            raise NotImplementedError()
        await self.execute("addnode", destination.name, "add")
        
    async def new_address(self) -> str:
        return await self.execute("getnewaddress")

    @overload
    async def mine(self, block_count: int) -> list[str]:
        ...

    @overload
    async def mine(self, block_count: int, recipient_address: str) -> list[str]:
        ...
    
    async def mine(self, block_count: int, recipient_address: str | None = None) -> list[str]:
        if not recipient_address:
            recipient_address = await self.new_address()
        
        async with Miner.__mine_lock:
            block_hashes: list[str] = await self.execute("generatetoaddress", block_count, recipient_address)
            return block_hashes

    @overload
    async def send(self, recipient_address: str, amount: int) -> str:
        ...
    
    @overload
    async def send(self, recipient_address: str, amount: int, fee_rate: int) -> str:
        ...

    async def send(self, recipient_address: str, amount: int, fee_rate: int = 25_0000) -> str:
        return await self.execute(
            "sendtoaddress",
            address = recipient_address,
            amount = float(amount / 100_000_000_000),
            fee_rate = int(fee_rate / 1_000)
        )