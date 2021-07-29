import uuid
import shutil
import asyncio
from pathlib import Path

from .runner import Environment, CompileResult, TestResult, Compiler, Runner


class Python3Environment(Environment):

    source_dir: Path

    def __enter__(self):
        sub_id = str(uuid.uuid1())
        self.source_dir = self.runners_dir / sub_id
        self.source_dir.mkdir()
        source_path = self.source_dir / self.source_name
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

    # TODO: Rewrite this shit
    async def run_test(self, exec_path, test):
        (test_input, expected_output) = test
        test_data = " ".join(test_input).encode()
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
        if list(expected_output) != list(real_output):
            return TestResult(TestResult.Verdict.WA)
        return TestResult(TestResult.Verdict.OK)


"""
class PythonCompiler(Compiler):
     
    async def compile(self, source_dir: Path, source_name: str) -> CompileResult:
        command = " ".join(("python3", "-m", "py_compile", source_name))
        with source_dir:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                return CompileResult.succ(source_name)
            return CompileResult.fail(stderr)


class PythonRunner(Runner):

    async def run_test(self, source_dir: Path, source_name: str, test) -> [TestResult]:
        (test_input, expected_output) = test
        test_data = " ".join(test_input).encode()
        command = " ".join(("python3", source_name))
        with source_dir:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate(test_data)
            if proc.returncode != 0:
                return TestResult(TestResult.Verdict.RE, stderr.decode())
            real_output = stdout.decode().strip().split()
            if list(expected_output) != list(real_output):
                return TestResult(TestResult.Verdict.WA)
            return TestResult(TestResult.Verdict.OK)
"""
