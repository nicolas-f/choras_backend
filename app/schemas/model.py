from marshmallow import Schema, fields


class ModelSchema(Schema):
    id = fields.Number()
    name = fields.Str(required=True)
    sourceFileId = fields.Integer()
    outputFileId = fields.Integer()

    projectId = fields.Integer()
    project = fields.Dict()

    createdAt = fields.Str()
    updatedAt = fields.Str()


class ModelCreateSchema(Schema):
    name = fields.Str(required=True)
    projectId = fields.Integer(required=True)
    sourceFileId = fields.Integer(required=True)


class ModelUpdateSchema(Schema):
    name = fields.Str(required=True)
