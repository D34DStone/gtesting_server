import logging
from typing import Dict, List, Callable, TypeVar

import aiohttp


__all__ = ("Publisher")


T = TypeVar("T")


class Publisher:

    data: T
    view: Callable[T, Dict]
    subscribers: List[str]

    def __init__(self, view: Callable[T, Dict], data: T):
        self.view = view
        self.data = data
        self.subscribers = list()

    async def subscribe(self, url: str):
        self.subscribers.append(url)
        await self.__notify_single(url)

    async def update(self, data: T):
        self.data = data
        for sub in self.subscribers:
            await self.__notify_single(sub)

    async def __notify_single(self, url: str):
        data_view = self.view(self.data)
        async with aiohttp.ClientSession() as s:
            try:
                async with s.post(url, json=data_view):
                    pass
            except aiohttp.client_exceptions.ClientConnectorError:
                logging.warning(f"Couldn't notify the host {url}")
