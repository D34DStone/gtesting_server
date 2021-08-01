import enum
import asyncio
import dataclasses
from typing import List, Union, BinaryIO
from pathlib import Path

from .application import config
from .tests import TestSet, Test

@dataclasses.dataclass
class CompileResult:

    succ: bool = True
    error_msg: str = ""
    exec_path: Union[None, Path] = None


@dataclasses.dataclass
class TestResult:

    class Verdict(enum.Enum):
        OK = "Success"
        WA = "Wrong answer"
        RE = "Runtime Error"
        UE = "Undefined Error"

    verdict: Verdict
    message: str = None


@dataclasses.dataclass
class RunnerReport:

    compilation_succ: bool
    message: Union[None, str]
    test_results: List[TestResult]


class Environment(object):

    def __init__(self, runners_dir: Path, source_stream: BinaryIO):
        self.source_stream = source_stream

    def __enter__(self) -> (str, Path):
        raise NotImplementedError

    def __exit__(self):
        raise NotImplementedError


class Compiler:

    async def compile(self, source_path: Path) -> CompileResult:
        raise NotImplementedError


class Runner:

    async def run_testset(self, exec_path: Path, ts: TestSet) -> [TestResult]:
        results = []
        for test in ts.tests:
            results.append(await self.run_test(exec_path, test))
        return results

    async def run_test(self, exec_path: Path, test: Test) -> TestResult:
        raise NotImplementedError


async def run_tests(
    source_stream: BinaryIO,
    environ: Environment, 
    compiler: Compiler, 
    runner: Runner,
    ts: TestSet) -> RunnerReport:
    with environ(config.get().RUNNERS_DIR, source_stream) as (sub_id, source_path):
        compilation_result = await compiler.compile(source_path)
        if not compilation_result.succ:
            return RunnerReport(False, compilation_result.error_msg, [])
        results = await runner.run_testset(compilation_result.exec_path, ts)
        return RunnerReport(False, None, results)
