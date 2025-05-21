from typing import Any, Generator, Self, overload
from .node import Node

class Channel:
    def __init__(self, *,
        id: str,
        source: Node,
        destination: Node
    ) -> None:
        self.id: str = str(id)
        self.source: Node = source
        self.destination: Node = destination
        self.capacity: int
        self.balance: int
        self.base_fee: int
        self.ppm_fee: int

    def __await__(self) -> Generator[Any, None, Self]:
        return self.update().__await__()
    
    async def update(self) -> Self:
        list_funds = await self.source.execute("listfunds")

        return self
    
    @overload
    async def set_fee(self, *, new_base_fee: int):
        ...
    
    @overload
    async def set_fee(self, *, new_ppm_fee: int):
        ...
    
    @overload
    async def set_fee(self, *, new_base_fee: int, new_ppm_fee: int):
        ...

    async def set_fee(self, *, new_base_fee: int | None = None, new_ppm_fee: int | None = None) -> None:
        
        parameters: dict[str, str | int] = {
            "id": self.id
        }

        if new_base_fee is not None:
            parameters["feebase"] = new_base_fee
        
        if new_ppm_fee is not None:
            parameters["feeppm"] = new_ppm_fee

        await self.source.execute(
            "setchannel",
            **parameters
        )