import unittest
import asyncio
import warnings

from aiohttp import web, ClientSession

from src.schemas import *
from src.routes import routes
from src.application import create_app
from src.application.tasks_pool import init_tasks_pool


PROT = "http"
HOST = "localhost"
PORT = 8080
URL = f"{PROT}://{HOST}:{PORT}"


class RoutesTest(unittest.IsolatedAsyncioTestCase):

    app: web.Application
    runner: web.AppRunner

    async def asyncSetUp(self):
        self.app = create_app(["--config", "config:TestingConfig"], routes)
        init_tasks_pool(self.app)
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, HOST, PORT)
        await site.start()

    async def asyncTearDown(self):
        await self.runner.cleanup()

    async def test_upload_testset(self):
        testset = {
            "tests": [
                {
                    "input": ["1", "2"],
                    "output": ["3"],
                },
                {
                    "input": ["100", "201"],
                    "output": ["301"]
                }
            ]}
        
        async with ClientSession() as s:
            async with s.post(f"{URL}/testset", json=testset) as resp:
                self.assertEqual(resp.status, 200)
                resp_obj = await resp.json()
                if errs := TestSetSchema().validate(resp_obj):
                    self.fail(f"Wrong response: {errs}")


    async def test_upload_testset_wrong(self):
        testset = {
            "tests": [
                {
                    "input": ["1", "2"],
                    "output": ["3"],
                },
                {
                    "input": ["100", "201"],
                    "output": ["301"],
                    "hello": "I am wrong piece of data"
                }
            ],
            "I Love Julia": "she is my first gf"
        }

        async with ClientSession() as s:
            async with s.post(f"{URL}/testset", json=testset) as resp:
                self.assertEqual(resp.status, 500)

    async def test_upload_testet_empty_body(self):
        async with ClientSession() as s:
            async with s.post(f"{URL}/testset") as resp:
                self.assertEqual(resp.status, 500)

    async def test_submit(self):
        testset = {
            "tests": [
                {
                    "input": ["1", "2"],
                    "output": ["3"],
                },
                {
                    "input": ["100", "201"],
                    "output": ["301"]
                }
            ]}
        async with ClientSession() as s:
            async with s.post(f"{URL}/testset", json=testset) as resp:
                self.assertEqual(resp.status, 200)
                resp_obj = await resp.json()
                testset_id = TestSetSchema().load(resp_obj).id

        source = ( 
            "a, b, *_ = (int(s) for s in input().split())\n"
            "print(a + b)" )
        submition = {
            "testset_id": testset_id,
            "language": "python3",
            "source": source
        }
        async with ClientSession() as s:
            async with s.post(f"{URL}/submit", json=submition) as resp:
                self.assertEqual(resp.status, 200)
                resp_obj = await resp.json()
                if errs := SubmitRespSchema().validate(resp_obj):
                    self.fail(f"Wrong response: {errs}")

    async def test_submit_wrong_testet(self):
        source = ( 
            "a, b, *_ = (int(s) for s in input().split())\n"
            "print(a + b)" )
        submition = {
            "testset_id": "[ 404 TEST SET ]",
            "language": "python3",
            "source": source
        }
        async with ClientSession() as s:
            async with s.post(f"{URL}/submit", json=submition) as resp:
                self.assertEqual(resp.status, 404)

    async def test_submit_wrong_request(self):
        source = ( 
            "a, b, *_ = (int(s) for s in input().split())\n"
            "print(a + b)" )
        submition = {
            "testset_id": "[ 404 TEST SET ]",
            "source": source,
            "hello": 123
        }
        async with ClientSession() as s:
            async with s.post(f"{URL}/submit", json=submition) as resp:
                self.assertEqual(resp.status, 500)

    async def test_submit_empty_body(self):
        async with ClientSession() as s:
            async with s.post(f"{URL}/submit") as resp:
                self.assertEqual(resp.status, 500)

    async def test_submit_post_only(self):
        protos = ("get", "put", "delete", "options")
        for proto in protos:
            async with ClientSession() as s:
                async with getattr(s, proto)(f"{URL}/submit") as resp:
                    self.assertEqual(resp.status, 405)
