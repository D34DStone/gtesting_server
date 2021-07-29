import os
import argparse
import logging
import importlib

from .routes import routes
from .application import Application


def get_config(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=False)
    args = parser.parse_args(argv)
    if args.config:
        config_obj = args.config
    else:
        config_obj = os.environ.get("APP_CONFIG", "config:ConfigDevelopment")
    logging.debug(f"Config object: {config_obj}")
    mod_path, obj_name = config_obj.split(":")
    mod = importlib.import_module(mod_path)
    return getattr(mod, obj_name)


def get_app(argv):
    config = get_config(argv)
    app = Application(config)
    app.aiohttp_app.add_routes(routes)
    app.aiohttp_app.on_startup.append(app.make_context)
    return app.aiohttp_app
