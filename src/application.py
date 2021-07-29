from aiohttp import web
from contextvars import ContextVar

config = ContextVar("config")

class Application:

    def __init__(self, config):
        self.aiohttp_app = web.Application()
        self.config = config

    async def make_context(self, _):
        config.set(self.config)
