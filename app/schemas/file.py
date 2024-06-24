from marshmallow import Schema, fields


class FileSchema(Schema):
    id = fields.Number()
    fileName = fields.Str()
    slot = fields.Str()
    size = fields.Number()

    createdAt = fields.Str()
    updatedAt = fields.Str()


class FileCreateSchema(Schema):
    slot = fields.Str(required=True)
