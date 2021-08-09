import os
import argparse
import importlib
from asyncio import coroutine
from contextlib import contextmanager
from contextvars import ContextVar

from redis import Redis
from aiohttp import web


app_var = ContextVar("gtesting:app")
config_var = ContextVar("gtesting:config")


def set_app_context(app):
    app_var.set(app)
    config_var.set(app["config"])


@contextmanager
def app_context(app):
    t_app = app_var.set(app)
    t_config = config_var.set(app["config"])
    try:
        yield
    finally:
        app_var.reset(t_app)
        config_var.reset(t_config)


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


def on_cleanup_custom(app: web.Application):
    for cleanup_cb in app["custom_cleanups"]:
        cleanup_cb(app)


def create_app(argv, routes=[]) -> web.Application:
    config = get_config(argv)
    app = web.Application()
    app.add_routes(routes)
    app["config"] = config
    app["global"] = dict()
    app["modules"] = list()
    app["custom_cleanups"] = list()

    async def on_startup(app):
        set_app_context(app)

    app.on_startup.append(on_startup)
    return app
