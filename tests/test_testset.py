import unittest

from aiohttp import web

from src.testset import *
from src.modules import redis_client
from src.application import create_app, app_context


class TestSetTestCase(unittest.TestCase):

    app: web.Application

    test_ts = TestSet([
            Test(
                input=["1", "2"],
                output=["3"]),
            Test(
                input=["4", "5"],
                output=["6"])
            ]) 

    def setUp(self):
        self.app = create_app(["--config", "config:TestingConfig"])
        redis_client.init_app(self.app)

    def tearDown(self):
        with app_context(self.app):
            r = redis_client.get_redis()
            for key in r.keys("*"):
                r.delete(key)

    def test_save(self):
        with app_context(self.app):
            save(self.test_ts)

    def test_save_wno_context(self):
        with self.assertRaises(AssertionError):
            save(self.test_ts)

    def test_save_dupliacation(self):
        with app_context(self.app):
            save(self.test_ts)
            with self.assertRaises(TestSetExists):
                save(self.test_ts)

    def test_save_load(self):
        with app_context(self.app):
            save(self.test_ts)
            test_ts2 = load(self.test_ts._id)
        self.assertEqual(test_ts2, self.test_ts)

    def test_load_wrong(self):
        with app_context(self.app):
            r1 = load(self.test_ts._id)
            r2 = load("hello-world")
        self.assertEqual(r1, None)
        self.assertEqual(r2, None)
