import io
import uuid
import json
from typing import Iterable, Tuple, List
import functools
import dataclasses

from aiohttp import web
from marshmallow import ValidationError

from .schemas import *
from .runner import run_tests, RunnerReport
from .tests import TestSet, save_testset, get_testset, TestSetNotFound
from .runner_python3 import Python3Environment, Python3Runner, Python3Compiler 


routes = web.RouteTableDef()


def json_api(req_schema, resp_schema):
    def wrapper(method): 
        @functools.wraps(method)
        async def decorated(request, *args, **kwargs):
            try:
                request_obj = await request.json()
            except Exception as err:
                return web.Response(
                    status=500, 
                    text=f"Couldn't parse the request: {err.messages}")

            if errs := req_schema.validate(request_obj): 
                return web.Response(
                    status=500,
                    text=f"Bad request: {errs}")

            result = await method(request_obj, *args, **kwargs)
            return web.json_response(resp_schema.dump(result))

        return decorated

    return wrapper


@routes.post("/testset")
@json_api(TestSetSchema(exclude=("id",)), TestSetSchema())
async def testset(request):
    ts = TestSet(**request)
    save_testset(ts)
    return ts


@routes.post("/submit")
@json_api(SubmitReqSchema(), SubmitRespSchema())
async def submit(request):
    try:
        testset = get_testset(request["testset_id"])
    except TestSetNotFound:
        return web.Response(status=404, text="Test set not found.")

    source_stream = io.BytesIO(request["source"].encode())
    return await run_tests(source_stream, Python3Environment, 
        Python3Compiler(), Python3Runner(), testset)
