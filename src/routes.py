import io
import uuid
import json
from typing import Iterable, Tuple, List
from aiohttp import web
from marshmallow import Schema, ValidationError, fields

from .application import config
from .runner import run_tests
from .runner_python3 import Python3Environment, Python3Runner, Python3Compiler 

routes = web.RouteTableDef()

# TODO: move part of test logic to a single file
@routes.post("/upload_testset")
async def upload_testset(request):
    data = await request.post()
    if "testset" not in data.keys():
        raise RuntimeError("`testset file not in the request")
    testsets_dir = config.get().TESTSETS_DIR
    testset_id = str(uuid.uuid1())
    testset_path = testsets_dir / testset_id
    with testset_path.open("wb") as f:
        f.write(data["testset"].file.read())
    return web.json_response({"testset_id": testset_id})


Test = Tuple[List[str], List[str]]
TestSet = Iterable[Test]


def load_testset(testset_id: str) -> TestSet:
    testset_path = config.get().TESTSETS_DIR / testset_id
    with testset_path.open("r") as f:
        testset_obj = json.load(f)
    return ((t["input"], t["output"]) for t in testset_obj)


@routes.post("/submit/{testset_id}")
async def submit(request):
    testset_id = request.match_info["testset_id"]
    data = await request.post()
    try:
        source_file = data["source"]
    except KeyError:
        return web.Response(status=500, text="You have to provide `source` file")
    try:
        testset = load_testset(testset_id)
    except FileNotFoundError:
        raise web.Response(status=500, text="Invalid testset id")
    source_name = source_file.filename
    source_stream = io.BytesIO(source_file.file.read())
    runners_dir = config.get().RUNNERS_DIR
    runner_report = await run_tests(runners_dir, source_name, source_stream, 
                                         Python3Environment, Python3Compiler(), 
                                         Python3Runner(), testset)
    return web.Response(text=str(runner_report))
