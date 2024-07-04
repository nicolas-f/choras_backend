from marshmallow import Schema, fields, post_load
from app.services import file_service


# class ProjectSchemaInModel(Schema):
#     id = fields.Integer(data_key="projectId")
#     name = fields.Str(required=True, data_key="projectName")
#     group = fields.Str(required=True, data_key="projectTag")
#

class ModelSchema(Schema):
    id = fields.Number()
    name = fields.Str(required=True)
    sourceFileId = fields.Integer()
    outputFileId = fields.Integer()
    hasGeo = fields.Boolean()

    projectId = fields.Integer()

    createdAt = fields.Str()
    updatedAt = fields.Str()


class ModelInfoSchema(Schema):
    id = fields.Integer(data_key="id")
    hasGeo = fields.Boolean(data_key='hasGeo')
    name = fields.String(data_key="modelName")
    sourceFileId = fields.Integer(data_key="modelUploadId")
    modelUrl = fields.Method("get_model_url", dump_only=True)

    projectTag = fields.String(data_key="projectTag", attribute="project.group")
    projectId = fields.Integer(data_key="projectId", attribute="project.id")
    projectName = fields.String(data_key="projectName", attribute="project.name")
    meshId = fields.String(data_key="meshId", attribute="mesh.id")

    simulationCount = fields.Function(lambda obj: obj.simulation_count)

    def get_model_url(self, obj):
        # obj here is the object being serialized
        return file_service.get_file_url(obj.sourceFileId)


class ModelCreateSchema(Schema):
    name = fields.Str(required=True)
    projectId = fields.Integer(required=True)
    sourceFileId = fields.Integer(required=True)


class ModelUpdateSchema(Schema):
    name = fields.Str(required=True)
