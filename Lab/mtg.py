from asyncio import TaskGroup as BaseTaskGroup
import asyncio
from asyncio.tasks import Task
from contextvars import Context
import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Any, Coroutine, TypeVar

_T = TypeVar("_T")

class ManagedTaskGroup(BaseTaskGroup):
    def __init__(self, *, retries: int = 3, delay: int = 1, semaphore: int = 200) -> None:
        super().__init__()
        self.__retries: int = retries
        self.__delay: int = delay
        self.__semaphore = asyncio.Semaphore(value=semaphore)

    def create_task(self, coro: Coroutine[Any, Any, _T], *, name: str | None = None, context: Context | None = None) -> Task[_T]:
        async def semaphored_coro() -> _T:
            async with self.__semaphore:
                logging.info(f"TASK_STARTED {task.get_name()}")
                return await coro
        task: Task[_T] = super().create_task(semaphored_coro(), name = name, context = context)
        task.add_done_callback(self.__log_done)
        return task

    def __log_done(self, task: Task[_T]) -> None:
        if task.cancelled():
            logging.warning(f"TASK_CANCELLED {task.get_name()}")
        elif task.exception():

            logging.error(f"TASK_FAILED {task.get_name()} {task.exception()}", stack_info = False)
        else:
            logging.info(f"TASK_DONE {task.get_name()} {task.result()}")
        return super()._on_task_done(task)