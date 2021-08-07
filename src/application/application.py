import os
import argparse
import importlib
from asyncio import coroutine
from contextlib import contextmanager

from redis import Redis
from aiohttp import web

from .context_vars import config_var, app_var
from .tasks_pool import init_tasks_pool


def set_app_context(app):
    app_var.set(app)
    config_var.set(app["config"])


@contextmanager
def app_context(app):
    set_app_context(app)
    yield


def load_module(path: str):
    module_name, object_name = path.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def get_config(argv):
    """ Loads a configuration class. Priority of the inferring a config:
    1. From CLI parameter `--config`
    2. From the encironment variable `APP_CONFIG`
    3. Use the default one `config:DevelopmentConfig`
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=False)
    args = parser.parse_args(argv)
    if args.config:
        return load_module(args.config)
    if path := os.environ.get("APP_CONFIG"):
        return load_module(path)
    return load_module("config:DevelopmentConfig")


def create_app(argv, routes=[]) -> web.Application:
    config = get_config(argv)
    app = web.Application()
    app.add_routes(routes)
    app["config"] = config
    app["global"] = dict()

    init_tasks_pool(app)

    async def on_startup(app):
        set_app_context(app)

    app.on_startup.append(on_startup)
    return app
