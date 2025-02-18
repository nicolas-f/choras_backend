from marshmallow import Schema, ValidationError, fields


class ExportSchema(Schema):
    id = fields.Number()
    zipFileName = fields.Str()
    preCsvFileName = fields.Str()
    simulationId = fields.Number()

class GetUrlSchema(Schema):
    id = fields.String(dump_only=True)
    uploadUrl = fields.String(dump_only=True)

