import enum
import asyncio
import dataclasses
from typing import List, Union, BinaryIO
from pathlib import Path


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
    message: str
    test_results: List[TestResult]


class Environment(object):

    def __init__(self, runners_dir: Path, source_name: str, source_stream: BinaryIO):
        self.runners_dir = runners_dir
        self.source_name = source_name
        self.source_stream = source_stream

    def __enter__(self) -> (str, Path):
        raise NotImplementedError

    def __exit__(self):
        raise NotImplementedError


class Compiler:

    async def compile(self, source_path: Path) -> CompileResult:
        raise NotImplementedError


class Runner:

    async def run_test(self, exec_path: Path, test) -> [TestResult]:
        raise NotImplementedError


async def run_tests(
    runner_dir: Path, 
    source_name: str,
    source_stream: BinaryIO,
    environ: Environment, 
    compiler: Compiler, 
    runner: Runner,
    testset) -> RunnerReport:
    with environ(runner_dir, source_name, source_stream) as (sub_id, source_path):
        compilation_result = await compiler.compile(source_path)
        if not compilation_result.succ:
            return RunnerReport(False, compilation_result.error_msg, [])
        test_results = [await runner.run_test(compilation_result.exec_path, test) 
                        for test in testset]
        return RunnerReport(False, None, test_results)
