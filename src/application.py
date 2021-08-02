import argparse
import importlib
from asyncio import coroutine
from contextvars import ContextVar
from contextlib import contextmanager

from redis import Redis
from aiohttp import web


config_ctx = ContextVar("gtesting:config")
redis_ctx = ContextVar("gtesting:redis")


def set_app_context(app):
    config_ctx.set(app["config"])
    redis_ctx.set(app["redis"])


@contextmanager
def app_context(app):
    set_app_context(app)
    yield


def load_module(path: str):
    module_name, object_name = path.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def get_config(argv):
    """ Loads a configuration class. Priprity of inferring a config path:
    1. From command line arguments: $ ./run --config config:ProductionConfig.
    2. From the encironment: APP_CONFIG.
    3. Use the default one: config:DevelopmentConfig.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=False)
    args = parser.parse_args(argv)
    if args.config:
        return load_module(args.config)
    if path := os.environ.get("APP_CONFIG"):
        return load_module(path)
    return load_module("config:DevelopmentConfig")


def create_app(routes, argv) -> web.Application:
    config = get_config(argv)
    redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    app = web.Application()

    app.add_routes(routes)
    app["config"] = config
    app["redis"] = redis

    async def on_startup(app):
        set_app_context(app)

    app.on_startup.append(on_startup)
    return app
