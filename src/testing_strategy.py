from enum import Enum
from typing import List, Iterable
from dataclasses import dataclass, field

from .testset import Test


@dataclass
class TestResult:

    class Verdict(Enum):
        
        OK = "Success"
        RE = "Runtime Error"
        WA = "Wrong answer"

    verdict: Verdict
    messages: List[str] = field(default_factory=list)


class TestingStrategy:

    async def prepare(self, source: str) -> List[str]:
        raise NotImplementedError

    async def compile(self) -> List[str]:
        raise NotImplementedError

    async def run(self, test: Test) -> TestResult:
        raise NotImplementedError
