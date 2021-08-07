from typing import Union
import functools

from aiohttp import web
from marshmallow import ValidationError

from .schemas import *
from .tests import TestSet, save_testset, get_testset

from .application import config_var, tasks_pool
from .v2.tester import Tester
from .v2.testing_strategy import TestingStrategy
from .v2.python3_fs_strategy import Python3FSTestingStrategy
from .v2.testset import Test


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


@routes.post("/testset")
@json_api(TestSetSchema(exclude=("id",)), TestSetSchema())
async def testset(request):
    ts = TestSet(**request)
    save_testset(ts)
    return ts


def get_strategy(language: str, ts: TestSet) -> Union[TestingStrategy, None]:
    execution_dir = config_var.get().RUNNERS_DIR
    if language == "python3":
        return Python3FSTestingStrategy(execution_dir)
    return None


@routes.post("/submit")
@json_api(SubmitReqSchema(), V2.SubmitRespSchema())
async def submit(request):
    if not (testset := get_testset(request["testset_id"])):
        return web.Response(status=404, text="Test set not found.")
    if not (strategy := get_strategy(request["language"], testset)):
        return web.Response(status=500, 
                text="Couldn't find a testing strategy.")
    tester = Tester(strategy, request["source"], testset.tests)
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
