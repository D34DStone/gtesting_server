import json
import unittest
import asyncio
from pathlib import Path
from typing import Dict
from marshmallow_dataclass import class_schema

from aiohttp import web, ClientSession

from src.utils import print_report
from src.schemas import *
from src.routes import routes
from src.application import create_app
from src.tester import Report, Status
from src.testing_strategy import TestResult
from src.modules import tasks_pool, redis_client


class SERVER:
    PROT = "http"
    HOST = "localhost"
    PORT = 8080
    URL = f"{PROT}://{HOST}:{PORT}"


class CLIENT:
    PROT = "http"
    HOST = "localhost"
    PORT = 8081
    URL = f"{PROT}://{HOST}:{PORT}"


class ASSETS:
    DIR = Path(__file__).resolve().parent / "matrix_multiplication"
    SOURCE = DIR / "source.py"
    TESTSET = DIR / "testset.json"


class IntegrationTest(unittest.IsolatedAsyncioTestCase):

    server_runner: web.AppRunner
    client_runner: web.AppRunner

    submition_states: Dict[str, Report]

    async def __run_server(self):
        app = create_app(["--config", "config:TestingConfig"], routes)
        tasks_pool.init_app(app)
        redis_client.init_app(app)
        self.server_runner = web.AppRunner(app)
        await self.server_runner.setup()
        site = web.TCPSite(self.server_runner, SERVER.HOST, SERVER.PORT)
        await site.start()

    async def __run_client(self):
        app = web.Application()
        app.add_routes([web.post("/{submition_id}", self.__submition_updated)])
        self.client_runner = web.AppRunner(app)
        await self.client_runner.setup()
        site = web.TCPSite(self.client_runner, CLIENT.HOST, CLIENT.PORT)
        await site.start()

    def setUp(self):
        self.submition_states = dict()

    async def asyncSetUp(self):
        await self.__run_server()
        await self.__run_client()

    async def asyncTearDown(self):
        await self.server_runner.cleanup()
        await self.client_runner.cleanup()

    async def __submition_updated(self, request):
        submition_id = request.match_info["submition_id"]
        req_obj = await request.json()
        report = class_schema(Report)().load(req_obj)
        self.submition_states[submition_id] = report
        return web.Response(status=200)

    
    async def test_integration(self):
        with ASSETS.TESTSET.open("r") as f:
            testset = json.load(f)

        async with ClientSession() as s:
            async with s.post(f"{SERVER.URL}/testset", json=testset) as resp:
                self.assertEqual(resp.status, 200)
                resp_obj = await resp.json()
                testset_id = TestSetSchema().load(resp_obj)._id 

        with ASSETS.SOURCE.open("r") as f:
            source = f.read()
        
        submition = {
            "language": "python3",
            "source": source,
            "testset_id": testset_id
        }

        async with ClientSession() as s:
            async with s.post(f"{SERVER.URL}/submit", json=submition) as resp:
                self.assertEqual(resp.status, 200)
                resp_obj = await resp.json()
                submition_id = SubmitRespSchema().load(resp_obj)["id"]


        subscription = {
            "submition_id": submition_id,
            "callback_url": f"{CLIENT.URL}/{submition_id}"
        }

        async with ClientSession() as s:
            async with s.post(f"{SERVER.URL}/subscribe", json=subscription) as resp:
                self.assertEqual(resp.status, 200)

        while ( submition_id not in self.submition_states.keys() or
                self.submition_states[submition_id].status != Status.Finished ):
            await asyncio.sleep(0.2)

        report = self.submition_states[submition_id]
        self.assertEqual(report.status, Status.Finished)
        self.assertEqual(len(report.test_results), len(testset["tests"]))
        self.assertTrue(all(test.verdict == TestResult.Verdict.OK for test in report.test_results))
