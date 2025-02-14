from marshmallow import Schema, fields

class AudioFileSchema(Schema):
    id = fields.Number()
    path = fields.String(load_only=True, required=True)
    name = fields.String(required=True)
    description = fields.String()
    isUserFile = fields.Boolean(required=True)
    createdAt = fields.String()
    updatedAt = fields.String()