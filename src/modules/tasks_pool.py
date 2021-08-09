import logging
from asyncio import coroutine, create_task, CancelledError
from contextlib import contextmanager
from contextvars import copy_context
from typing import Callable, TypeVar

import aiohttp.web

from src.application import app_var


__all__ = ("init_app", "get", "schedult")


async def __cleanup(app: aiohttp.web.Application):
    if "tasks_pool" not in app["global"].keys():
        return
    pool = app["global"]["tasks_pool"]
    for (runner, task) in pool:
        task.cancel()
        try:
            await task
        except CancelledError:
            logging.info(f"Task of {runner} is cancelled.")


def init_app(app: aiohttp.web.Application):
    app["global"]["tasks_pool"] = list()
    app["custom_cleanups"].append(__cleanup)
    app["modules"].append("tasks_pool")


def __get_tasks_pool():
    assert app_var in copy_context(), "Not inside an app context"
    app = app_var.get()
    assert "tasks_pool" in app["modules"], "tasks_pool module wans't loaded"
    return app["global"]["tasks_pool"]


def schedult(runner: Callable[..., coroutine], *argv, **kwargs):
    pool = __get_tasks_pool()
    task = create_task(runner(*argv, **kwargs))
    pool.append((runner, task))


T = TypeVar("T")


def get(pred: Callable[T, bool]) -> T:
    for (runner, _) in __get_tasks_pool():
        if pred(runner):
            return runner
    raise LookupError()
