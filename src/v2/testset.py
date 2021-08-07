import uuid
from typing import List
from dataclasses import dataclass, field


@dataclass
class Test():

    input: List[str]
    output: List[str]


@dataclass
class TestSet():

    _id: str = field(default_factory=lambda: str(uuid.uuid1()))
    tests: List[Test] = field(default_factory=list)
