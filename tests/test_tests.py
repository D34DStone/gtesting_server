import os
import unittest

from src.application import redis_ctx

from src.main import get_app
from src.routes import routes

class TestTests(unittest.TestCase):

    def setUp(self):
        self.app = get_app(routes, ["--config", "config:TestingConfig"])

    def test_test(self):
        with self.app["app_context"]():
            redis = redis_ctx.get()
            print(redis)

