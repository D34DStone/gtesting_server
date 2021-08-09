import enum
from typing import Tuple

from marshmallow_dataclass import class_schema
from marshmallow import Schema, fields

from .testset import Test, TestSet


TestSetSchema = class_schema(TestSet, Schema)


class SubmitReqSchema(Schema):

    testset_id = fields.Str()
    language = fields.Str()
    source = fields.Str()


class SubmitRespSchema(Schema):

    id = fields.Str()


class SubcribeReqSchema(Schema):

    submition_id = fields.Str()
    callback_url = fields.Url()
