import uuid
import asyncio
import unittest
from contextlib import contextmanager
from typing import Dict, List, Callable

from aiohttp import web

from src.application import create_app, app_var
from src.modules import tasks_pool


class MockRunner():

    id: str
    executed = False

    def __init__(self):
        self.id = str(uuid.uuid1())

    async def __call__(self):
        self.executed = True


def get_runner(id: str) -> Callable[MockRunner, bool]:
    return lambda r: r.id == id



class TesterPoolTests(unittest.IsolatedAsyncioTestCase):

    runner: MockRunner
    app: web.Application

    @contextmanager
    def __app_context(self):
        app_var.set(self.app)
        yield

    def setUp(self):
        self.runner = MockRunner()
        self.app = create_app(["--config", "config:TestingConfig"])
        tasks_pool.init_app(self.app)

    def test_no_app(self):
        with self.assertRaises(AssertionError):
            tasks_pool.get("fake")
        with self.assertRaises(AssertionError):
            tasks_pool.schedult(MockRunner())

    async def test_schedult(self):
        runner1 = MockRunner()
        runner2 = MockRunner()
        runner3 = MockRunner()
        with self.__app_context():
            tasks_pool.schedult(runner1)
            tasks_pool.schedult(runner2)
        await asyncio.sleep(0.1)
        self.assertTrue(runner1.executed)
        self.assertTrue(runner2.executed)
        self.assertFalse(runner3.executed)

    async def test_get(self):
        runner1 = MockRunner()
        runner2 = MockRunner()
        runner3 = MockRunner()
        with self.__app_context():
            tasks_pool.schedult(runner1)
            tasks_pool.schedult(runner2)
            _t1 = tasks_pool.get(get_runner(runner1.id))
            self.assertEqual(_t1.id, runner1.id)
            _t2 = tasks_pool.get(get_runner(runner2.id))
            self.assertEqual(_t2.id, runner2.id)
            with self.assertRaises(LookupError):
                _t3 = tasks_pool.get(get_runner(runner3.id))

    async def test_get_empty(self):
        with self.__app_context():
            with self.assertRaises(LookupError):
                tasks_pool.get(get_runner("123"))
