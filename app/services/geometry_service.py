import logging
import os
import zipfile

import rhino3dm
from flask_smorest import abort

import config
from app.db import db
from app.models import File, Geometry, Task
from app.factory.geometry_converter_factory.GeometryConversionFactory import (
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
        if not convert_3dm_to_geo(rhino3dm_path, geo_path):
            logger.error("Can not generate a geo file")
            return False

        file_geo = File(fileName=f"{file_name}.geo")
        db.session.add(file_geo)
        db.session.commit()

    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not attach a geo file: {ex}")
        return False

    return True


def convert_3dm_to_geo(rhino_file_path, geo_file_path, volume_name="RoomVolume", map_materials=True):  # noqa: C901
    """
    Converts a Rhino 3DM file to a Gmsh GEO file with proper material mapping.

    Args:
        rhino_file_path: Path to the Rhino 3dm file
        geo_file_path: Path to output the geo file
        volume_name: Name for the Physical Volume (default: "RoomVolume")
        map_materials: Whether to map materials from the 3dm file (default: True)

    Returns:
        bool: True if successful, False otherwise
    """
    """
    Converts a Rhino 3DM file to a Gmsh GEO file with proper material mapping.

    Args:
        rhino_file_path: Path to the Rhino 3dm file
        geo_file_path: Path to output the geo file
        volume_name: Name for the Physical Volume (default: "RoomVolume")
        map_materials: Whether to map materials from the 3dm file (default: True)

    Returns:
        bool: True if successful, False otherwise
    """
    model = rhino3dm.File3dm.Read(rhino_file_path)

    # Structures to hold .geo elements
    points = {}
    edges = set()  # Just collect unique edges first
    line_loops = {}
    plane_surfaces = {}
    physical_surfaces = {}

    # Helper tracking
    coord_to_point_index = {}
    face_to_edges = {}  # Maps face index to its edges

    # Material mapping for later use if map_materials is True
    material_name_to_ids = {}
    if map_materials:
        material_to_id = {}
        for obj in model.Objects:
            if isinstance(obj.Geometry, rhino3dm.Mesh):
                material_name = obj.Geometry.GetUserString("material_name")
                if material_name:
                    material_to_id[f"{obj.Attributes.Id}"] = material_name

        # Reverse the mapping to be from material name to list of IDs
        for id, material_name in material_to_id.items():
            if material_name not in material_name_to_ids:
                material_name_to_ids[material_name] = []
            material_name_to_ids[material_name].append(id)

    point_index = 1
    surface_index = 1

    # Maps to store material/layer assignments
    object_to_material = {}
    material_to_surfaces = {}
    obj_id_to_surfaces = {}  # Track surfaces by object ID for material mapping

    # First pass: Identify materials/layers
    for obj in model.Objects:
        if not isinstance(obj.Geometry, rhino3dm.Mesh):
            continue

        # Material assignment logic - try to use these strategies in order:
        # 1. Material index (if available)
        # 2. Layer index (if available)
        # 3. Default to M_1
        if obj.Attributes.MaterialIndex > 0:
            material_id = f"M_{obj.Attributes.MaterialIndex}"
        elif obj.Attributes.LayerIndex > 0:
            material_id = f"M_{obj.Attributes.LayerIndex}"
        else:
            material_id = "M_1"

        object_to_material[obj.Attributes.Id] = material_id

        if material_id not in material_to_surfaces:
            material_to_surfaces[material_id] = []

        # Initialize tracking for this object's surfaces
        obj_id_to_surfaces[obj.Attributes.Id] = []

    # Second pass: Process geometry
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

            def format_coord(value):
                rounded_1 = round(value, 1)
                if rounded_1 == round(value, 2):  # If 1 decimal place is sufficient
                    return f"{rounded_1:.1f}"
                return f"{round(value, 2):.2f}"  # Otherwise, use 2 decimal places

            rounded_x = format_coord(vertex.X)
            rounded_y = format_coord(vertex.Y)
            rounded_z = format_coord(vertex.Z)

            coord = (rounded_x, rounded_y, rounded_z)
            if coord not in coord_to_point_index:
                points[point_index] = f"Point({point_index}) = {{ {rounded_x}, {rounded_y}, {rounded_z}, 1.0 }};\n"
                coord_to_point_index[coord] = point_index
                point_index += 1
            vertex_map[i] = coord_to_point_index[coord]

        # Collect surfaces and edges per object
        object_surface_indices = []

        for i in range(faces.Count):
            face = faces[i]

            # Get face indices based on face type (triangle or quad)
            face_indices = (
                [face[0], face[1], face[2], face[3]]
                if len(face) == 4
                else [face[0], face[1], face[2]] if len(face) == 3 else None
            )
            if not face_indices:
                continue  # Skip non-triangle/quad faces

            # Collect the edges for this face
            face_edges = []
            face_vertices = []

            # First collect all vertices in order
            for j in range(len(face_indices)):
                vertex_idx = vertex_map[face_indices[j]]
                face_vertices.append(vertex_idx)

            # Then create edges from consecutive vertices
            for j in range(len(face_vertices)):
                a = face_vertices[j]
                b = face_vertices[(j + 1) % len(face_vertices)]

                # Store the edge with direction for line loops
                face_edges.append((a, b))

                # Also store unique edges for line creation
                edge = tuple(sorted([a, b]))
                edges.add(edge)

            # Store the face edges for later line loop creation
            face_to_edges[surface_index] = face_edges

            # Add to material surface list
            material_id = object_to_material[obj.Attributes.Id]
            material_to_surfaces[material_id].append(surface_index)

            # Also track by object ID for material mapping
            obj_id_to_surfaces[obj.Attributes.Id].append(surface_index)

            object_surface_indices.append(surface_index)
            surface_index += 1

    # Create lines in a predictable order after collecting all edges
    lines = {}
    edge_to_line_index = {}
    physical_lines = []

    line_index = 1
    for edge in sorted(edges):  # Sort edges for consistent ordering
        a, b = edge
        lines[line_index] = f"Line({line_index}) = {{ {a}, {b} }};\n"
        edge_to_line_index[edge] = line_index
        physical_lines.append(line_index)
        line_index += 1

    # Now create line loops using the line indices
    for face_idx, face_edges in face_to_edges.items():
        # Extract ordered vertices from face edges
        edge_vertices = []
        for a, b in face_edges:
            if not edge_vertices:
                edge_vertices.extend([a, b])
            else:
                # Ensure the next edge continues from the last vertex
                if edge_vertices[-1] == a:
                    edge_vertices.append(b)
                elif edge_vertices[-1] == b:
                    edge_vertices.append(a)
                else:
                    # If not connected, try to insert at the beginning
                    if edge_vertices[0] == a:
                        edge_vertices.insert(0, b)
                    elif edge_vertices[0] == b:
                        edge_vertices.insert(0, a)
                    else:
                        print(f"Warning: Disconnected edge ({a},{b}) in face {face_idx}")

        # Ensure the loop is closed
        if edge_vertices[0] != edge_vertices[-1]:
            face_edges.append((edge_vertices[-1], edge_vertices[0]))

        # Create line loop with correct line directions
        line_loop_indices = []
        for i in range(len(edge_vertices) - 1):
            a = edge_vertices[i]
            b = edge_vertices[i + 1]

            sorted_edge = tuple(sorted([a, b]))
            line_idx = edge_to_line_index[sorted_edge]

            # Check if direction matches
            if (a, b) != sorted_edge:
                line_idx = -line_idx  # Negative for reverse direction

            line_loop_indices.append(line_idx)

        # Format line loop with correct spacing to match example
        line_loops[face_idx] = f"Line Loop({face_idx}) = {{ {', '.join(map(str, line_loop_indices))} }};\n"
        plane_surfaces[face_idx] = f"Plane Surface({face_idx}) = {{ {face_idx} }};\n"

    # Create physical surfaces groups
    if map_materials and material_name_to_ids:
        # If mapping materials, create physical surfaces based on material names
        for obj_id, surfaces in obj_id_to_surfaces.items():
            if surfaces:
                physical_surfaces[obj_id] = f"Physical Surface(\"{obj_id}\") = {{ {', '.join(map(str, surfaces))} }};\n"
    else:
        # Otherwise use the material/layer based groups
        for material_id, surface_list in material_to_surfaces.items():
            if surface_list:
                physical_surfaces[material_id] = (
                    f"Physical Surface(\"{material_id}\") = {{ {', '.join(map(str, surface_list))} }};\n"
                )

    # Write to .geo file
    with open(geo_file_path, "w") as geo_file:
        # Write points first
        for idx in sorted(points):
            geo_file.write(points[idx])
        geo_file.write("\n")

        # Write lines
        for idx in sorted(lines):
            geo_file.write(lines[idx])
        geo_file.write("\n")

        # Write line loops
        for idx in sorted(line_loops):
            geo_file.write(line_loops[idx])
        geo_file.write("\n")

        # Write plane surfaces
        for idx in sorted(plane_surfaces):
            geo_file.write(plane_surfaces[idx])
        geo_file.write("\n")

        # Write Surface Loop and Volume with custom volume name
        surface_ids = sorted(plane_surfaces.keys())
        geo_file.write(f"Surface Loop(1) = {{ {', '.join(map(str, surface_ids))} }};\n")
        geo_file.write("Volume( 1 ) = { 1 };\n")
        geo_file.write(f'Physical Volume("{volume_name}") = {{ 1 }};\n')

        # Write Physical Surface definitions
        for ps in physical_surfaces.values():
            geo_file.write(ps)

        # Add Physical Line group
        geo_file.write(f'Physical Line ("default") = {{{", ".join(map(str, physical_lines))}}};\n')

        # Write mesh parameters at the end
        geo_file.write("Mesh.Algorithm = 6;\n")
        geo_file.write("Mesh.Algorithm3D = 1; // Delaunay3D, works for boundary layer insertion.\n")
        geo_file.write("Mesh.Optimize = 1; // Gmsh smoother, works with boundary layers (netgen version does not).\n")
        geo_file.write("Mesh.CharacteristicLengthFromPoints = 1;\n")
        geo_file.write('// Recombine Surface "*";\n')

    print(f"Converted {rhino_file_path} to {geo_file_path}")
    return os.path.exists(geo_file_path)
