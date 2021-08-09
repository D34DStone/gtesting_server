import redis

from aiohttp import web

from src.application import app_var, config_var

from contextvars import copy_context


def init_app(app: web.Application):
    app["modules"].append("redis_client")
    app["global"]["redis_client"] = redis.Redis(
        host=app["config"].REDIS_HOST,
        port=app["config"].REDIS_PORT)


def get_redis():
    assert app_var in copy_context(), "Not in app context"
    app = app_var.get()
    assert "redis_client" in app["modules"], \
           "redis_client module isn't initialized"
    return app["global"]["redis_client"]
