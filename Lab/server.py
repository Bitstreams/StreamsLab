from __future__ import annotations
from abc import abstractmethod
import asyncio
import io
import logging
import tarfile
from typing import Any, Self, Generator
import docker
from docker.models.containers import Container
import json
import httpx

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
        control_port: int | None
    ) -> None:
        self.__container: Container = self.__docker_client.containers.create(
            image = image,
            command = command,
            detach = True,
            network = "streamslab",
            environment = environment,
            ports = {f"{control_port}/tcp": None} if control_port else None,
            mem_limit = "256m",
            memswap_limit = "256m",
            auto_remove = True
        )
        self.__control_port: int | None = control_port
        self._rest_client: httpx.AsyncClient

    def __await__(self) -> Generator[Any, None, Self]:
        return self.start().__await__()

    async def start(self) -> Self:
        if not self.is_running:
            await asyncio.to_thread(self.container.start)
            self._rest_client = httpx.AsyncClient(
                base_url = await self.__control_url,
                timeout = 60
            )
        return self
    
    def __str__(self) -> str:
        return self.name

    @property
    def is_running(self) -> bool:
        return self.__container.status == "running"
    
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
    async def __control_url(self) -> str:
        if not self.__control_port:
            raise ValueError("No control port is exposed to host")
        
        self.container.reload()
        while not self.container.attrs["NetworkSettings"]["Ports"][f"{self.__control_port}/tcp"]:
            self.container.reload()
            logging.warning(f"Port was not loaded on {self}. We have {json.dumps(self.container.attrs["NetworkSettings"]["Ports"])}")
            await asyncio.sleep(1)

        host_port = int(self.container.attrs["NetworkSettings"]["Ports"][f"{self.__control_port}/tcp"][0]["HostPort"])

        logging.debug(f"{self} exposes {host_port}")
            
        return f"http://127.0.0.1:{host_port}"

    async def execute(self, *command: str, **kwargs) -> Any:
        ...

    @abstractmethod
    async def connect(self, destination: Server) -> None:
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
        if self.is_running:
            await asyncio.to_thread(self.__container.stop)
            await self._rest_client.aclose()