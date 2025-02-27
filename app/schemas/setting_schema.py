from marshmallow import Schema, fields


class SettingSchema(Schema):
    simulationType = fields.String()
    path = fields.String(load_only=True)
    name = fields.String(load_only=True)
    description = fields.String()
    createdAt = fields.String()
    updatedAt = fields.String()