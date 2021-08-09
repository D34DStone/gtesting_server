import unittest

from aiohttp import web

from src.application import create_app, app_context
from src.modules import redis_client


class RedisClientTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(["--config", "config:TestingConfig"])
        redis_client.init_app(self.app)

    def test_redis_available(self):
        with app_context(self.app):
            r = redis_client.get_redis()
            r.ping()

    def test_redis_wno_context(self):
        with self.assertRaises(AssertionError):
            r = redis_client.get_redis()
