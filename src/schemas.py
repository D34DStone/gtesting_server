import enum
from typing import Tuple

from marshmallow_dataclass import class_schema
from marshmallow import Schema, fields

from .runner import RunnerReport
from .tests import Test, TestSet


TestSetSchema = class_schema(TestSet, Schema)


class SubmitReqSchema(Schema):
    testset_id = fields.Str()
    language = fields.Str()
    source = fields.Str()


SubmitRespSchema = class_schema(RunnerReport)
