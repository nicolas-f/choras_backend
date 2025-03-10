import logging
import os
import zipfile
from typing import re

import rhino3dm
from flask_smorest import abort

import config
from app.db import db
from app.models import File, Geometry, Task
from app.services import model_service
from app.services.geometry_converter_factory.GeometryConversionFactory import (
    GeometryConversionFactory,
)
from app.types import Status, TaskType

# Create logger for this module
logger = logging.getLogger(__name__)


def get_geometry_by_id(geometry_id):
    results = Geometry.query.filter_by(id=geometry_id).first()
    return results


def start_geometry_check_task(file_upload_id):
    """
    This function is a wrapper over 3dm mapper. It creates a task and geometry given a file upload id.
    Then calls the map_to_3dm function to map the given geometry file format to a rhino model.

    :param file_upload_id: represents an id related to the uploaded file
    :return: Geometry: returns an object of Geometry model corresponding to the uploaded file
    """
    try:
        task = Task(taskType=TaskType.GeometryCheck, status=Status.Created)
        db.session.add(task)
        db.session.commit()
        geometry = Geometry(inputModelUploadId=file_upload_id, taskId=task.id)

        db.session.add(geometry)
        db.session.commit()

        result = map_to_3dm_and_geo(geometry.id)
        if not result:
            task.status = Status.Error
            task.message = "An error is encountered during the geometry processing!"
            db.session.commit()
            abort(500, task.message)

        task.status = Status.Completed

        db.session.commit()

    except Exception as ex:
        db.session.rollback()
        task.status = Status.Error
        task.message = "An error is encountered during the geometry processing!"
        db.session.commit()
        logger.error(f"{task.message}: {ex}")
        abort(400, message=f"Can not start the geometry task! Error: {ex}")

    return geometry


def get_geometry_result(task_id):
    return Geometry.query.filter_by(taskId=task_id).first()


def map_to_3dm_and_geo(geometry_id):
    geometry = Geometry.query.filter_by(id=geometry_id).first()
    file = File.query.filter_by(id=geometry.inputModelUploadId).first()
    task = Task.query.filter_by(id=geometry.taskId).first()

    directory = config.DefaultConfig.UPLOAD_FOLDER
    file_name, file_extension = os.path.splitext(os.path.basename(file.fileName))

    obj_path = os.path.join(directory, file.fileName)
    rhino3dm_path = os.path.join(directory, f"{file_name}.3dm")
    zip_file_path = os.path.join(directory, f"{file_name}.zip")
    geo_path = os.path.join(directory, f"{file_name}.geo")

    try:
        task.status = Status.InProgress
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not update task status! Error: {ex}")

    # Use the new process method to handle both cleaning and conversion
    conversion_factory = GeometryConversionFactory()

    conversion_strategy = conversion_factory.create_strategy(file_extension)

    if not conversion_strategy.generate_3dm(obj_path, rhino3dm_path):
        return False

    if not os.path.exists(rhino3dm_path):
        logger.error("Can not find created a rhino file")
        return False

    try:
        file3dm = File(fileName=f"{file_name}.3dm")
        db.session.add(file3dm)
        db.session.commit()

        geometry.outputModelId = file3dm.id

        # Create a zip file from 3dm
        with zipfile.ZipFile(zip_file_path, "w") as zipf:
            zipf.write(rhino3dm_path, arcname=f"{file_name}.3dm")

        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not create a rhino file: {ex}")
        return False

    try:
        if not generate_geo_file(rhino3dm_path, geo_path):
            logger.error("Can not generate a geo file")
            return False

        file_geo = File(fileName=f"{file_name}.geo")
        db.session.add(file_geo)
        db.session.commit()

        attach_geo_file(rhino3dm_path, geo_path)

    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not attach a geo file: {ex}")
        return False

    return True

def generate_geo_file(rhino_file_path, geo_file_path):
    model = rhino3dm.File3dm.Read(rhino_file_path)

    # Structures to hold .geo elements
    points = {}
    lines = {}
    line_loops = {}
    plane_surfaces = {}
    physical_surfaces = {}

    # Helper tracking
    coord_to_point_index = {}
    edge_to_line_index = {}

    point_index = 1
    line_index = 1
    surface_index = 1

    for obj in model.Objects:
        if not isinstance(obj.Geometry, rhino3dm.Mesh):
            continue

        mesh = obj.Geometry
        mesh.Faces.ConvertTrianglesToQuads(0.5, 0)
        mesh.Vertices.CombineIdentical(True, True)
        vertices = mesh.Vertices
        faces = mesh.Faces

        vertex_map = {}  # Maps mesh vertex index to Gmsh point index

        for i, vertex in enumerate(vertices):
            coord = (round(vertex.X, 6), round(vertex.Y, 6), round(vertex.Z, 6))
            if coord not in coord_to_point_index:
                points[point_index] = f"Point({point_index}) = {{{vertex.X}, {vertex.Y}, {vertex.Z}, 1.0}};\n"
                coord_to_point_index[coord] = point_index
                point_index += 1
            vertex_map[i] = coord_to_point_index[coord]

        # Collect surfaces per object
        object_surface_indices = []

        for i in range(faces.Count):
            face = faces[i]

            face_indices = (
                [face[0], face[1], face[2], face[3]]
                if len(face) == 4
                else [face[0], face[1], face[2]]
                if len(face) == 3
                else None
            )
            if not face_indices:
                continue

            line_loop_indices = []
            for j in range(len(face_indices)):
                a = vertex_map[face_indices[j]]
                b = vertex_map[face_indices[(j + 1) % len(face_indices)]]
                edge = tuple(sorted((a, b)))
                if edge not in edge_to_line_index:
                    lines[line_index] = f"Line({line_index}) = {{{a}, {b}}};\n"
                    edge_to_line_index[edge] = line_index
                    current_line_index = line_index
                    line_index += 1
                else:
                    current_line_index = edge_to_line_index[edge]

                line_loop_indices.append(current_line_index)

            line_loops[surface_index] = f"Line Loop({surface_index}) = {{{', '.join(map(str, line_loop_indices))}}};\n"
            plane_surfaces[surface_index] = f"Plane Surface({surface_index}) = {{{surface_index}}};\n"
            object_surface_indices.append(surface_index)
            surface_index += 1

        # Group surfaces under the object's physical surface ID
        if object_surface_indices:
            physical_surfaces[obj.Attributes.Id] = (
                f"Physical Surface(\"{obj.Attributes.Id}\") = {{{', '.join(map(str, object_surface_indices))}}};\n"
            )

    # Write to .geo file
    with open(geo_file_path, "w") as geo_file:
        geo_file.write("// Generated from Rhino .3dm file\n")
        geo_file.write("// Mesh Parameters\n")
        geo_file.write("Mesh.Algorithm = 6;\n")
        geo_file.write("Mesh.Algorithm3D = 1;\n")
        geo_file.write("Mesh.Optimize = 1;\n")
        geo_file.write("Mesh.CharacteristicLengthFromPoints = 1;\n\n")

        # Write ordered blocks
        for idx in sorted(points): geo_file.write(points[idx])
        geo_file.write("\n")
        for idx in sorted(lines): geo_file.write(lines[idx])
        geo_file.write("\n")
        for idx in sorted(line_loops): geo_file.write(line_loops[idx])
        for idx in sorted(plane_surfaces): geo_file.write(plane_surfaces[idx])
        geo_file.write("\n")
        for ps in physical_surfaces.values(): geo_file.write(ps)

        # Write Surface Loop and Volume for enclosing geometry
        surface_ids = sorted(plane_surfaces.keys())
        geo_file.write(f"Surface Loop(1) = {{{', '.join(map(str, surface_ids))}}};\n")
        geo_file.write("Volume(1) = {1};\n")
        geo_file.write('Physical Volume("solid") = {1};\n\n')

    print(f"Converted {rhino_file_path} to {geo_file_path}")
    return os.path.exists(geo_file_path)

def attach_geo_file(rhino_file_path, geo_file_path):
    model = rhino3dm.File3dm.Read(rhino_file_path)

    if not os.path.exists(geo_file_path):
        raise FileNotFoundError(f"File not found: {geo_file_path}")

    with open(geo_file_path, "r") as file:
        geo_content = file.readlines()

    # Create a mapping of material_name to obj.Attributes.Id
    material_to_id = {}
    for obj in model.Objects:
        if isinstance(obj.Geometry, rhino3dm.Mesh):
            material_name = obj.Geometry.GetUserString("material_name")
            if material_name:
                material_to_id[f"{obj.Attributes.Id}"] = material_name

    # Reverse the mapping to be from material name to list of IDs
    material_name_to_ids = {}
    for id, material_name in material_to_id.items():
        if material_name not in material_name_to_ids:
            material_name_to_ids[material_name] = []
        material_name_to_ids[material_name].append(id)

    def pop_and_update_braces(content):
        pattern = re.compile(r"{\s*(\d+(?:\s*,\s*\d+)*)\s*}")
        match = pattern.search(content)
        if match:
            numbers = match.group(1).split(",")
            numbers = [num.strip() for num in numbers]
            if numbers:
                return numbers
        return []

    # Replace physical surface keys in the geo file content
    new_geo_content = []
    for line in geo_content:
        if line.strip().startswith("Physical Surface"):
            parts = line.split('"')
            if len(parts) > 1:
                material_name = parts[1].strip()
                if material_name in material_name_to_ids:
                    ids = material_name_to_ids[material_name]
                    numbers = pop_and_update_braces(line)
                    for i, number in enumerate(numbers):
                        new_geo_content.append(f'Physical Surface("{ids.pop(0)}") = {{ {number} }};\n')
                else:
                    return False
            else:
                new_geo_content.append(line)
        else:
            new_geo_content.append(line)

    with open(geo_file_path, "w") as file:
        file.writelines(new_geo_content)

    return True
