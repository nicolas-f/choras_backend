import logging
from flask_smorest import abort
from app.services import model_service, file_service
import rhino3dm
import os
import config
import gmsh
import re
from app.db import db
from app.types import TaskType, Status

from Diffusion.FiniteVolumeMethod.CreateMeshFVM import generate_mesh

from app.models import Mesh, Task, Simulation

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


def get_mesh_result_by_id(mesh_id):
    pass


def attach_geo_file(model_id, file_input_id):
    model_Model = model_service.get_model(model_id)
    directory = config.DefaultConfig.UPLOAD_FOLDER
    geo_file = file_service.get_file_by_id(file_input_id)
    model_file = file_service.get_file_by_id(model_Model.outputFileId)
    file_name, file_extension = os.path.splitext(
        os.path.basename(model_file.fileName)
    )
    file3dm = rhino3dm.File3dm()
    model = file3dm.Read(os.path.join(directory, model_file.fileName))

    with open(os.path.join(directory, geo_file.fileName), 'r') as file:
        geo_content = file.readlines()

    # Create a mapping of material_name to obj.Attributes.Id
    material_to_id = {}
    for obj in model.Objects:
        if isinstance(obj.Geometry, rhino3dm.Mesh):
            material_name = obj.Geometry.GetUserString('material_name')
            if material_name:
                material_to_id[f"{obj.Attributes.Id}"] = material_name

    # Reverse the mapping to be from material name to list of IDs
    material_name_to_ids = {}
    for id, material_name in material_to_id.items():
        if material_name not in material_name_to_ids:
            material_name_to_ids[material_name] = []
        material_name_to_ids[material_name].append(id)

    def pop_and_update_braces(content):
        pattern = re.compile(r'{\s*(\d+(?:\s*,\s*\d+)*)\s*}')
        match = pattern.search(content)
        if match:
            numbers = match.group(1).split(',')
            numbers = [num.strip() for num in numbers]
            if numbers:
                return numbers
        return []

    # Replace physical surface keys in the geo file content
    new_geo_content = []
    for line in geo_content:
        if line.strip().startswith('Physical Surface'):
            parts = line.split('"')
            if len(parts) > 1:
                material_name = parts[1].strip()
                if material_name in material_name_to_ids:
                    ids = material_name_to_ids[material_name]
                    numbers = pop_and_update_braces(line)
                    for i, number in enumerate(numbers):
                        new_geo_content.append(
                            f'Physical Surface("{ids.pop(0)}") = {{ {number} }};\n'
                        )
                else:
                    return {
                        'status': False,
                        'message': f'Mismatch between name of the material and the boundary name {material_name}'

                    }
                    new_geo_content.append(line)
            else:
                new_geo_content.append(line)
        else:
            new_geo_content.append(line)

    with open(os.path.join(directory, f'{file_name}.geo'), 'w') as file:
        file.writelines(new_geo_content)

    try:
        model_Model.hasGeo = True
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not attach the geo file to the model! Error: {ex}")
        abort(400, message=f"Can not attach the geo file to the model! Error: {ex}")

    return {
        'status': True,
        'message': 'geo file added to the model successfully!'
    }


def start_mesh_task(model_id):
    model_db = model_service.get_model(model_id)
    file = file_service.get_file_by_id(model_db.outputFileId)

    directory = config.DefaultConfig.UPLOAD_FOLDER
    file_name, file_extension = os.path.splitext(
        os.path.basename(file.fileName)
    )
    geo_path = os.path.join(directory, f"{file_name}.geo")
    msh_path = os.path.join(directory, f"{file_name}.msh")
    try:
        Mesh.query.filter_by(modelId=model_id).delete()
        db.session.commit()
        task = Task(
            taskType=TaskType.Mesh,
        )
        db.session.add(task)
        db.session.commit()
        mesh = Mesh(
            modelId=model_id,
            taskId=task.id
        )

        db.session.add(mesh)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.error(f"Error in mesh generation (db)! Error: {ex}")
        abort(400, message=f"Error in mesh generation (db)! Error: {ex}")

    try:
        generate_mesh(geo_path, msh_path, 1)
    except Exception as ex:
        logger.error(f"Error in mesh generation (msh)! Error: {ex}")
        abort(400, message=f"Error in mesh generation (msh)! Error: {ex}")

    if os.path.exists(msh_path):
        try:
            task.status = Status.Completed
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            logger.error(f"Error in mesh generation (db)! Error: {ex}")
            abort(400, message=f"Error in mesh generation (db)! Error: {ex}")
    else:
        try:
            task.status = Status.Error
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            logger.error(f"Error in mesh generation (db)! Error: {ex}")
            abort(400, message=f"Error in mesh generation (db)! Error: {ex}")

    return mesh


def generate_geo_file(rhino_file_path, geo_file_path):
    file3dm = rhino3dm.File3dm()
    model = file3dm.Read(rhino_file_path)

    # Collect points, lines, line loops, and physical surfaces
    points = {}
    lines = {}
    line_loops = {}
    plane_surfaces = {}
    physical_surfaces = {}

    point_index = 1
    line_index = 1
    surface_index = 1
    physical_surface_counter = 1

    # Iterate over the objects in the 3dm model
    for obj in model.Objects:
        if isinstance(obj.Geometry, rhino3dm.Mesh):

            faces = obj.Geometry.Faces
            faces.ConvertTrianglesToQuads(0.5, 0)
            vertices = obj.Geometry.Vertices
            vertices.CombineIdentical(True, True)

            # Create a mapping from vertex index to Gmsh point index
            vertex_map = {}

            # Write points to .geo file
            for i, vertex in enumerate(vertices):
                print(vertex)
                points[point_index] = f"Point({point_index}) = {{{vertex.X}, {vertex.Y}, {vertex.Z}, 1.0}};\n"
                vertex_map[i] = point_index
                point_index += 1

            # Write line loops and plane surfaces for each face
            for i in range(faces.Count):
                face = faces[i]

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
                    lines[line_index] = f"Line({line_index}) = {{{start_point}, {end_point}}};\n"
                    line_loop_indices.append(line_index)
                    line_index += 1

                line_loops[
                    surface_index] = f"Line Loop({surface_index}) = {{{', '.join(map(str, line_loop_indices))}}};\n"
                plane_surfaces[surface_index] = f"Plane Surface({surface_index}) = {{{surface_index}}};\n"
                surface_index += 1

            # Write physical surface group
            physical_surfaces[
                obj.Attributes.Id] = f"Physical Surface(\"{obj.Attributes.Id}\") = {{{', '.join(map(str, range(1, surface_index)))}}};\n"
            physical_surface_counter += 1

    with open(geo_file_path, 'w') as geo_file:
        # Write sorted points
        for point_index in sorted(points.keys()):
            geo_file.write(points[point_index])

        # Write sorted lines
        for line_index in sorted(lines.keys()):
            geo_file.write(lines[line_index])

        # Write sorted line loops
        for line_loop_index in sorted(line_loops.keys()):
            geo_file.write(line_loops[line_loop_index])

        # Write sorted plane surfaces
        for surface_index in sorted(plane_surfaces.keys()):
            geo_file.write(plane_surfaces[surface_index])

        # Write sorted plane surfaces
        for pysical_index in sorted(physical_surfaces.keys()):
            geo_file.write(physical_surfaces[pysical_index])

    print(f"Converted {rhino_file_path} to {geo_file_path}")
    return geo_file_path


gmsh.initialize()


def generate_geo_file_using_gmsh(rhino_file_path, geo_file_path):
    try:
        file3dm = rhino3dm.File3dm()
        model = file3dm.Read(rhino_file_path)

        # Start defining the geometry
        model_geo = gmsh.model.geo

        points = {}
        lines = {}
        line_loops = {}
        plane_surfaces = {}
        physical_surfaces = {}

        point_index = 1
        line_index = 1
        surface_index = 1
        physical_surface_counter = 1

        # Iterate over the objects in the 3dm model
        for obj in model.Objects:
            if isinstance(obj.Geometry, rhino3dm.Mesh):
                faces = obj.Geometry.Faces
                faces.ConvertTrianglesToQuads(0.5, 0)
                vertices = obj.Geometry.Vertices
                vertices.CombineIdentical(True, True)

                # Define vertices as Gmsh points
                gmsh_points = []
                for vertex in vertices:
                    gmsh_point = model_geo.addPoint(vertex.X, vertex.Y, vertex.Z)
                    gmsh_points.append(gmsh_point)
                    points[point_index] = gmsh_point
                    point_index += 1

                # Define lines and line loops for each face
                for i in range(faces.Count):
                    face = faces[i]

                    if len(face) == 4:  # Quad face
                        face_indices = [face[0], face[1], face[2], face[3]]
                    elif len(face) == 3:  # Triangle face
                        face_indices = [face[0], face[1], face[2]]
                    else:
                        continue

                    # Define lines
                    gmsh_lines = []
                    for j in range(len(face_indices)):
                        start_point = gmsh_points[face_indices[j]]
                        end_point = gmsh_points[face_indices[(j + 1) % len(face_indices)]]
                        gmsh_line = model_geo.addLine(start_point, end_point)
                        gmsh_lines.append(gmsh_line)
                        lines[line_index] = gmsh_line
                        line_index += 1

                    # Define line loop and plane surface
                    line_loop = model_geo.addCurveLoop(gmsh_lines)
                    plane_surface = model_geo.addPlaneSurface([line_loop])
                    line_loops[surface_index] = line_loop
                    plane_surfaces[surface_index] = plane_surface
                    surface_index += 1

                # Define physical surface group
                physical_surface = model_geo.addPhysicalGroup(2, [plane_surfaces[surface_index] for surface_index in
                                                                  range(1, surface_index)])
                physical_surfaces[obj.Attributes.Id] = physical_surface
                physical_surface_counter += 1

        # Write the .geo file
        model_geo.synchronize()
        gmsh.write(f"{geo_file_path}_unrolled")

        print(f"Converted {rhino_file_path} to {geo_file_path}")
        return geo_file_path

    finally:
        gmsh.finalize()
