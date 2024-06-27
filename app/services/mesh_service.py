import logging
from flask_smorest import abort
from app.services import model_service, file_service
import rhino3dm
import os
import config

from app.models import Mesh

# Create logger for this module
logger = logging.getLogger(__name__)


def get_meshes_by_model_id(model_id):
    return Mesh.query.filter_by(
        modelId=model_id
    ).all()


def get_mesh_by_id(mesh_id):
    mesh = Mesh.query.filter_by(id=mesh_id).first()
    if not mesh:
        abort(404, message="Mesh does not exist")
    return mesh


def start_mesh_task(model_id):
    model = model_service.get_model(model_id)
    file = file_service.get_file_by_id(model.outputFileId)

    directory = config.DefaultConfig.UPLOAD_FOLDER
    file_name, file_extension = os.path.splitext(
        os.path.basename(file.fileName)
    )
    rhino3dm_path = os.path.join(directory, f"{file_name}.3dm")
    geo_path = os.path.join(directory, f"{file_name}.geo")
    generate_geo_file(rhino3dm_path, geo_path)

    # create a new task with type mesh
    # create a mesh
    # in the end you should return mesh model


def generate_geo_file(rhino_file_path, geo_file_path):
    file3dm = rhino3dm.File3dm()
    model = file3dm.Read(rhino_file_path)

    with open(geo_file_path, 'w') as geo_file:
        point_index = 1
        line_index = 1
        surface_index = 1
        physical_surface_counter = 1

        # Iterate over the objects in the 3dm model
        for obj in model.Objects:
            if isinstance(obj.Geometry, rhino3dm.Mesh):
                vertices = obj.Geometry.Vertices
                faces = obj.v.Faces

                # Create a mapping from vertex index to Gmsh point index
                vertex_map = {}

                # Write points to .geo file
                for i, vertex in enumerate(vertices):
                    geo_file.write(f"Point({point_index}) = {{{vertex.X}, {vertex.Y}, {vertex.Z}, 1.0}};\n")
                    vertex_map[i] = point_index
                    point_index += 1

                # Write line loops and plane surfaces for each face
                for i in range(faces.Count):
                    face = faces[i]
                    print(face)

                    if len(face) == 4:  # Quad face
                        face_indices = [face[0], face[1], face[2], face[3]]
                    elif len(face) == 3:  # Triangle face
                        face_indices = [face[0], face[1], face[2]]
                    else:
                        continue

                    # Create line loops for the face
                    line_loop_indices = []
                    for j in range(len(face_indices)):
                        start_point = vertex_map[face_indices[j]]
                        end_point = vertex_map[face_indices[(j + 1) % len(face_indices)]]
                        geo_file.write(f"Line({line_index}) = {{{start_point}, {end_point}}};\n")
                        line_loop_indices.append(line_index)
                        line_index += 1

                    geo_file.write(f"Line Loop({surface_index}) = {{{', '.join(map(str, line_loop_indices))}}};\n")
                    geo_file.write(f"Plane Surface({surface_index}) = {{{surface_index}}};\n")
                    surface_index += 1

                # Write physical surface group
                geo_file.write(
                    f"Physical Surface(\"Surface_{physical_surface_counter}\") = {{{', '.join(map(str, range(1, surface_index)))}}};\n")
                physical_surface_counter += 1

    print(f"Converted {rhino_file_path} to {geo_file_path}")
    return geo_file_path
