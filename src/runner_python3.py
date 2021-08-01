import uuid
import shutil
import asyncio
from pathlib import Path

from .application import config

from .tests import Test
from .runner import Environment, CompileResult, TestResult, Compiler, Runner


class Python3Environment(Environment):

    source_dir: Path

    def __enter__(self):
        sub_id = str(uuid.uuid1())
        self.source_dir = config.get().RUNNERS_DIR / sub_id
        self.source_dir.mkdir()
        source_path = self.source_dir / sub_id
        with source_path.open("wb") as f:
            f.write(self.source_stream.read())
        return (sub_id, source_path) 

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(str(self.source_dir))


class Python3Compiler(Compiler):

    async def compile(self, source_path):
        source_dir = source_path.parent
        command = " ".join(("python3", "-m", "py_compile", str(source_path)))
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return CompileResult(False, stderr.decode(), None)
        return CompileResult(True, "", source_path)


class Python3Runner(Runner):

    # TODO: Looks ugly. Rewrite it
    async def run_test(self, exec_path, test):
        test_data = " ".join(test.input).encode()
        command = " ".join(("python3", str(exec_path)))
        proc = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate(test_data)
        if proc.returncode != 0:
            return TestResult(TestResult.Verdict.RE, stderr.decode())
        real_output = stdout.decode().strip().split()
        if list(test.output) != list(real_output):
            return TestResult(TestResult.Verdict.WA)
        return TestResult(TestResult.Verdict.OK)
