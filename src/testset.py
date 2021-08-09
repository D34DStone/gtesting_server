import uuid
import json
from typing import List, Union
from dataclasses import dataclass, field

from marshmallow_dataclass import class_schema

from src.modules import redis_client


@dataclass
class Test():

    input: List[str]
    output: List[str]


@dataclass
class TestSet():

    tests: List[Test] = field(default_factory=list)
    _id: str = field(default_factory=lambda: str(uuid.uuid1()))


TestSetSchema = class_schema(TestSet)


class TestSetExists(Exception):

    pass


def load(_id: str) -> Union[TestSet]:
    r = redis_client.get_redis()
    if ts_bytes := r.get(_id):
        ts_obj = json.loads(ts_bytes)
        return TestSetSchema().load(ts_obj)
    return None



def save(ts: TestSet):
    r = redis_client.get_redis()
    if load(ts._id):
        raise TestSetExists()
    ts_obj = TestSetSchema().dump(ts)
    r.set(ts._id, json.dumps(ts_obj))
