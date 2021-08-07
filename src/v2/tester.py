import logging
from enum import Enum
from uuid import uuid1
from typing import List, Iterable
from asyncio import shield
from dataclasses import dataclass, field

from marshmallow_dataclass import class_schema

from .publisher import Publisher
from .testset import Test
from .testing_strategy import TestingStrategy, TestResult


class Status(Enum):

    Waiting = "waiting"
    Compilation = "compilation"
    CompilationFailed = "compilation failed"
    Running = "running"
    Failed = "failed"
    Finished = "finished"


@dataclass
class Report:

    status: Status = Status.Waiting
    messages: List[str] = field(default_factory=list)
    test_results: List[TestResult] = field(default_factory=list)


class Tester:
    
    _id: str
    _strategy: TestingStrategy
    _publisher: Publisher
    _report: Report
    _source: str
    _tests: Iterable[Test]

    @property
    def id(self):
        return self._id

    def __init__(self, strategy: object, 
            source: str, tests: Iterable[Test]):
        assert isinstance(strategy, (TestingStrategy,))
        self._id = str(uuid1())
        self._strategy = strategy
        self._source = source
        self._tests = tests
        self._report = Report()
        reportView = class_schema(Report)().dump
        self._publisher = Publisher(reportView, self._report)

    async def subscribe(self, *argv, **kwargs):
        await self._publisher.subscribe(*argv, **kwargs)

    async def __call__(self) -> Report:
        if errs := (await shield(self._strategy.prepare(self._source))):
            self._report.status = Status.Failed
            self._report.message = errs
            await self._publisher.update(self._report)
            return self._report

        self._report.status = Status.Compilation
        await self._publisher.update(self._report)
            
        if errs := (await shield(self._strategy.compile())):
            self._report.status = Status.CompilationFailed
            self._report.messages = errs
            await self._publisher.update(self._report)
            return self._report

        self._report.status = Status.Running 
        await self._publisher.update(self._report)

        for test in self._tests:
            tr = await shield(self._strategy.run(test))
            self._report.test_results.append(tr)
            await self._publisher.update(self._report)

        self._report.status = Status.Finished
        await self._publisher.update(self._report)
        return self._report
