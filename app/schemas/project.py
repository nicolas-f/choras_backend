from marshmallow import Schema, fields


class ProjectSchema(Schema):
    id = fields.Number()
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    group = fields.Str(required=True)
    models = fields.List(fields)
    createdAt = fields.Str()
    updatedAt = fields.Str()


class ProjectCreateSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=False)
    group = fields.Str(required=True)


class ProjectUpdateSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=False)
