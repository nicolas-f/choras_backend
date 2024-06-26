from marshmallow import Schema, fields
from app.schemas.model_schema import ModelSchema
from app.models import Project


class ProjectSchema(Schema):
    id = fields.Number()
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    group = fields.Str(required=True)
    createdAt = fields.Str()
    updatedAt = fields.Str()


class ProjectWithModelsSchema(ProjectSchema):
    models = fields.List(fields.Nested(ModelSchema))


class ProjectCreateSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=False)
    group = fields.Str(required=True)


class ProjectUpdateSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str()


class ProjectUpdateByGroupQuerySchema(Schema):
    group = fields.Str(required=True)


class ProjectUpdateByGroupBodySchema(Schema):
    newGroup = fields.Str(required=True)
