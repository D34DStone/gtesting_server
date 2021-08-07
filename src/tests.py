import uuid
import json
from typing import List, Union
from dataclasses import dataclass, asdict, field

from marshmallow_dataclass import class_schema

from .application import config_var

@dataclass
class Test:

    input: List[str]
    output: List[str]


@dataclass
class TestSet:

    tests: List[Test]
    id: str = field(default_factory=lambda: str(uuid.uuid1()))


def save_testset(ts: TestSet):
    testsets_dir = config_var.get().TESTSETS_DIR
    if not testsets_dir.exists():
        testsets_dir.mkdir(parent=True)
    testset_path = testsets_dir / ts.id
    with testset_path.open("w") as f:
        ts_obj = class_schema(TestSet)().dump(ts)
        json.dump(ts_obj, f)


def get_testset(id: str) -> Union[TestSet, None]:
    testset_path = config_var.get().TESTSETS_DIR / id
    if not testset_path.exists():
        return None
    with testset_path.open("r") as f:
        ts_obj = json.load(f)
        return class_schema(TestSet)().load(ts_obj)
