import logging
import asyncio
from uuid import uuid1
from enum import Enum
from pathlib import Path
from typing import List


from .testset import Test
from .testing_strategy import TestingStrategy, TestResult


class State(Enum):
    INIT = 0
    PREPARED = 1
    COMPILED = 2


class Python3FSTestingStrategy(TestingStrategy):

    testing_dir: Path
    source_path: Path
    state: State = State.INIT

    def __init__(self, testing_dir: Path):
        self.testing_dir = testing_dir

    async def prepare(self, source: str) -> List[str]:
        assert self.state == State.INIT
        if not self.testing_dir.exists():
            logging.debug("Testing directory doesn't exist. Creating "
                f"{self.testing_dir.resolve()}")
            self.testing_dir.mkdir(parents=True)
        source_dir = self.testing_dir / str(uuid1())
        source_dir.mkdir()
        self.source_path = source_dir / "source.py"
        logging.debug(f"Writing the source code to {self.source_path.resolve()}")
        with self.source_path.open("w") as f:
            f.write(source)
        self.state = State.PREPARED
        return list()

    async def compile(self) -> List[str]:
        assert self.state == State.PREPARED
        command = " ".join(["python3", "-m", "py_compile", str(self.source_path)])
        logging.debug(f"Compiling the source: $ {command}")
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return [f"rc: {proc.returncode}", stderr.decode()]
        self.state = State.COMPILED
        return list()

    async def run(self, test: Test) -> TestResult:
        assert self.state == State.COMPILED
        command = " ".join(["python3", str(self.source_path)])
        data = " ".join(test.input)
        proc = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate(data.encode())
        if proc.returncode != 0:
            return TestResult(TestResult.Verdict.RE, stderr.decode())
        real_output = stdout.decode().split()
        if real_output != test.output:
            return TestResult(TestResult.Verdict.WA)
        return TestResult(TestResult.Verdict.OK)
