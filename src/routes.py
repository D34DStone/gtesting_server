from typing import Union
import functools

from aiohttp import web
from marshmallow import ValidationError

from .schemas import *

from .modules import tasks_pool
from .application import config_var
from .tester import Tester
from .testing_strategy import TestingStrategy
from .python3_fs_strategy import Python3FSTestingStrategy
from . import testset
from .testset import TestSet


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
                    text=f"Couldn't parse the request: {err.msg}")

            if errs := req_schema.validate(request_obj): 
                return web.Response(
                    status=500,
                    text=f"Bad request: {errs}")

            result = await method(request_obj, *args, **kwargs)
            if isinstance(result, (web.Response,)):
                return result
            return web.json_response(resp_schema.dump(result))

        return decorated

    return wrapper


def get_strategy(language: str, ts: TestSet) -> Union[TestingStrategy, None]:
    execution_dir = config_var.get().RUNNERS_DIR
    if language == "python3":
        return Python3FSTestingStrategy(execution_dir)
    return None


@routes.post("/testset")
@json_api(TestSetSchema(exclude=("_id",)), TestSetSchema())
async def testset_handler(request):
    ts = TestSet(**request)
    testset.save(ts)
    return ts


@routes.post("/submit")
@json_api(SubmitReqSchema(), SubmitRespSchema())
async def submit(request):
    if not (ts := testset.load(request["testset_id"])):
        return web.Response(status=404, text="Test set not found.")
    if not (strategy := get_strategy(request["language"], ts)):
        return web.Response(status=500, 
                text="Couldn't find a testing strategy.")
    tester = Tester(strategy, request["source"], ts.tests)
    tasks_pool.schedult(tester)
    return { "id": tester.id }


@routes.post("/subscribe")
@json_api(SubcribeReqSchema(), None)
async def subscribe(request):
    try:
        submition = tasks_pool.get(lambda t: t.id == request["submition_id"])
    except LookupError:
        return web.Response(status=404, text="Submition not found.")
    await submition.subscribe(request["callback_url"])
    return web.Response(status=200)
