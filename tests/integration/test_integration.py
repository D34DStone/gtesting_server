import json
import unittest
import asyncio
from pathlib import Path
from typing import Dict, Tuple

from aiohttp import web, ClientSession
from marshmallow_dataclass import class_schema

from src.schemas import *
from src.routes import routes
from src.application import create_app, app_context
from src.tester import Report, Status
from src.testing_strategy import TestResult
from src.modules import tasks_pool, redis_client

class Config: 

    class Server:
        PROT = "http"
        HOST = "localhost"
        PORT = 8080
        URL = f"{PROT}://{HOST}:{PORT}"

    class Client:
        PROT = "http"
        HOST = "localhost"
        PORT = 8081
        URL = f"{PROT}://{HOST}:{PORT}"


class ClientServerFixture(unittest.IsolatedAsyncioTestCase):

    server: web.Application
    server_runner: web.AppRunner
    client_runner: web.AppRunner

    submition_states: Dict[str, Report]

    async def __run_server(self):
        self.server = create_app(["--config", "config:TestingConfig"], routes)
        tasks_pool.init_app(self.server)
        redis_client.init_app(self.server)
        self.server_runner = web.AppRunner(self.server)
        await self.server_runner.setup()
        site = web.TCPSite(self.server_runner, Config.Server.HOST, Config.Server.PORT)
        await site.start()

    async def __run_client(self):
        app = web.Application()
        app.add_routes([web.post("/{submition_id}", self.__submition_updated)])
        self.client_runner = web.AppRunner(app)
        await self.client_runner.setup()
        site = web.TCPSite(self.client_runner, Config.Client.HOST, Config.Client.PORT)
        await site.start()

    async def __submition_updated(self, request):
        submition_id = request.match_info["submition_id"]
        req_obj = await request.json()
        report = class_schema(Report)().load(req_obj)
        self.submition_states[submition_id] = report
        return web.Response(status=200)

    async def asyncSetUp(self):
        self.submition_states = dict()
        await self.__run_server()
        await self.__run_client()

    async def asyncTearDown(self):
        with app_context(self.server):
            r = redis_client.get_redis()
            for key in r.keys("*"):
                r.delete(key)
        await self.server_runner.cleanup()
        await self.client_runner.cleanup()

    async def _wait_until_report(self, sub_id: str):
        while sub_id not in self.submition_states.keys():
            await asyncio.sleep(0.2)

    async def _wait_unitl_tested(self, sub_id: str):
        terminal_states = [
            Status.Finished,
            Status.CompilationFailed,
            Status.Failed ]
        await self._wait_until_report(sub_id)
        while self.submition_states[sub_id].status not in terminal_states:
            await asyncio.sleep(0.2)


def load_test_source(data_dir: Path) -> Tuple[str, Dict]:
    with (data_dir / "source").open("r") as f:
        source = f.read()
    with (data_dir / "testset.json").open("r") as f:
        ts = json.load(f)
    return (source, ts)


async def upload_testset(ts: Dict) -> TestSet:
    async with ClientSession() as s:
        async with s.post(f"{Config.Server.URL}/testset", json=ts) as resp:
            resp_obj = await resp.json()
            return TestSetSchema().load(resp_obj)


async def submit(submition: Dict) -> str:
    async with ClientSession() as s:
        async with s.post(f"{Config.Server.URL}/submit", json=submition) as resp:
            resp_obj = await resp.json()
            return SubmitRespSchema().load(resp_obj)["id"]


async def subscribe(subscription: Dict) -> str:
    async with ClientSession() as s:
        async with s.post(f"{Config.Server.URL}/subscribe", json=subscription) as resp:
            pass


class IntegrationTest(ClientServerFixture):

    async def _execute_python3(self, data_dir: Path) -> Tuple[str, TestSet]:
        """ Uploads a testset, submits a python3 source, subscribe to 
            it. Returns submition_id and uploaded TestSet. """
        src, ts = load_test_source(data_dir)
        ts = await upload_testset(ts)
        submition = {
            "source": src,
            "language": "python3",
            "testset_id": ts._id,
            "callback_url_template": f"{Config.Client.URL}/$submition_id"
        }
        sub_id = await submit(submition)
        return (sub_id, ts)

    async def test_basic(self):
        data_dir = Path(__file__).resolve().parent / "data" / "matrix_multiplication"
        sub_id, ts = await self._execute_python3(data_dir)
        await asyncio.wait_for(self._wait_unitl_tested(sub_id), timeout=10)
        report = self.submition_states[sub_id]
        self.assertEqual(report.status, Status.Finished)
        self.assertEqual(len(report.test_results), len(ts.tests))
        self.assertTrue(all(test.verdict == TestResult.Verdict.OK 
                            for test in report.test_results))

    async def test_wno_autosubscription(self):
        data_dir = Path(__file__).resolve().parent / "data" / "matrix_multiplication"
        src, ts = load_test_source(data_dir)
        ts = await upload_testset(ts)
        submition = {
            "source": src,
            "language": "python3",
            "testset_id": ts._id,
        }
        sub_id = await submit(submition)
        subscription = {
            "submition_id": sub_id,
            "callback_url": f"{Config.Client.URL}/{sub_id}"
        }
        await subscribe(subscription)
        await asyncio.wait_for(self._wait_unitl_tested(sub_id), timeout=10)
        report = self.submition_states[sub_id]
        self.assertEqual(report.status, Status.Finished)
        self.assertEqual(len(report.test_results), len(ts.tests))
        self.assertTrue(all(test.verdict == TestResult.Verdict.OK 
                            for test in report.test_results))

    async def test_compile_error(self):
        data_dir = Path(__file__).resolve().parent / "data" / "matrix_multiplication_ce"
        sub_id, ts = await self._execute_python3(data_dir)
        await asyncio.wait_for(self._wait_unitl_tested(sub_id), timeout=10)
        report = self.submition_states[sub_id]
        self.assertEqual(report.status, Status.CompilationFailed)
