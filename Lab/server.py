from abc import abstractmethod
import asyncio
import io
import logging
import tarfile
from typing import Any, Self, Generator
import docker
from docker.models.containers import Container

class Server():
    __docker_client: docker.DockerClient = docker.from_env(timeout = 600, max_pool_size = 10_000)
    try:
        __docker_client.networks.create("streamslab")
    except:
        ...

    def __init__(
        self,
        *,
        image: str,
        command: str | list[str],
        environment: dict[str, str] | None = None,
        rpc_port: int | None
    ) -> None:
        self.__container: Container | None = None
        self.__image: str = image
        self.__command: str | list[str] = command
        self.__environment: dict[str, str] | None = environment
        self.__internal_rpc_port: int | None = rpc_port

    def __await__(self) -> Generator[Any, None, Self]:
        return self.start().__await__()

    async def start(self) -> Self:
        if not self.__container:
            self.__container = await asyncio.to_thread(
                self.__docker_client.containers.run,
                image = self.__image,
                command = self.__command,
                detach = True,
                network = "streamslab",
                environment = self.__environment,
                ports = {f"{self.__internal_rpc_port}/tcp": None} if self.__internal_rpc_port else None,
                mem_limit = "256m",
                memswap_limit = "256m",
                remove = True
            )
            self.__host_rpc_port: int = 0
        return self

    @property
    def is_running(self) -> bool:
        return bool(self.__container)
    
    @property
    def name(self) -> str:
        if not self.container.name:
            raise
        else:
            return self.container.name
    
    @property
    def container(self) -> Container:
        if not self.__container:
            raise RuntimeError("Server is not running")
        else:
            return self.__container
    
    @property
    def host_rpc_port(self) -> int:
        if not self.__host_rpc_port:
            self.container.reload()
            if not self.__internal_rpc_port:
                raise ValueError("No ports are exposed to host")
            self.__host_rpc_port = int(self.container.attrs["NetworkSettings"]["Ports"][f"{self.__internal_rpc_port}/tcp"][0]["HostPort"])
        return self.__host_rpc_port

    async def execute(self, *command: str, **kwargs) -> Any:
        ...

    @abstractmethod
    async def connect(self, destination: Self) -> None:
        ...

    @abstractmethod
    async def new_address(self) -> str:
        ...

    async def read_file(self, file_path: str) -> str:
        data_stream, stat = await asyncio.to_thread(self.container.get_archive, file_path)

        file_bytes = io.BytesIO()
        for chunk in data_stream:
            file_bytes.write(chunk)

        file_bytes.seek(0)

        with tarfile.open(fileobj = file_bytes) as tar:
            member = tar.getmembers()[0]
            extracted_file = tar.extractfile(member)
            if extracted_file:
                file_contents: str = extracted_file.read().decode("utf-8")
                return file_contents
            else:
                raise FileNotFoundError(f"Unable to read {file_path} from {self.name}")
    
    def __block_until(self, text: str) -> None:
        for line in self.container.logs(stream = True, follow = True):
            if text in line.decode():
                return
    
    async def wait_for(self, text: str) -> None:
        await asyncio.to_thread(self.__block_until, text)
    
    async def stop(self) -> None:
        await asyncio.to_thread(self.container.stop)