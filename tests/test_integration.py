import os
import io
import sys
import json
import asyncio
import warnings
import unittest
import contextlib

import requests
from aiohttp import web, ClientSession, FormData
from marshmallow import ValidationError

from src import main
from src.schemas import *


class IntgrationTest(unittest.IsolatedAsyncioTestCase):

    HOST = "localhost:8080"

    async def asyncSetUp(self):
        os.environ["APP_CONFIG"] = "config:TestingConfig"
        self.app = main.get_app([])
        self.config = main.get_config([])
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, *self.HOST.split(":"))
        warnings.simplefilter("ignore")
        await site.start()

    async def asyncTearDown(self):
        await self.runner.cleanup()

    async def __upload_testset(self, testset) -> (int, bytes):
        url = f"http://{self.HOST}/testset"
        async with ClientSession() as s:
            async with s.post(url, json=testset) as resp:
                return (resp.status, await resp.content.read())

    async def __submit(self, testset_id: str, source: str) -> (int, bytes):
        url = f"http://{self.HOST}/submit"
        request_data = dict(
            testset_id=testset_id, 
            language="python3",
            source=source)
        request_json = SubmitReqSchema().dump(request_data)
        async with ClientSession() as s:
            async with s.post(url, json=request_json) as resp:
                return (resp.status, await resp.content.read())

    async def test_upload_testset(self):
        status, content = await self.__upload_testset({
            "tests": [
                {
                    "input": ["1", "2"],
                    "output": ["19"]
                },
                {
                    "input": ["5", "6"],
                    "output": ["heeelp" * 100]
                }
            ]})
        self.assertEqual(status, 200)
        content_obj = json.loads(content)
        try:
            upload_resp = TestSetSchema().load(content_obj)
        except ValidationError as err:
            self.fail(f"Failed to load the response: {err}")

    async def __test_submit(self):
        source = """
a, b, *_ = (int(n) for n in input().split())
print(a + b)
        """
        testset = [
            {
                "input": ["1", "2"],
                "output": ["3"]
            },
            {
                "input": ["5", "6"],
                "output": ["11"]
            },
            {
                "input": ["7", "8"],
                "output": ["16"]
            },
        ]
        _, upload_content = await self.__upload_testset(testset)
        testset_id = UploadTestsetRespSchema().load(json.loads(upload_content))["testset_id"]
        _, submit_content = await self.__submit(testset_id, source)
