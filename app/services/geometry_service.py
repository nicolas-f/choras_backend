import logging
import os
import zipfile
from typing import Dict, List, Set, Tuple, Union, Optional

import rhino3dm
from flask_smorest import abort

import config
from app.db import db
from app.models import File, Geometry, Task
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


def format_coord(value: float) -> Union[int, float]:
    """
    Format coordinate value to match the desired output style.
    If value is a whole number, return as integer, otherwise round to 1 decimal place.
    """
    rounded = round(value, 1)
    return int(rounded) if rounded.is_integer() else rounded


def get_material_mappings(
    model: rhino3dm.File3dm, map_materials: bool
) -> Tuple[Dict[str, List[str]], Dict[str, str], Dict[str, List[int]]]:
    """
    Extract material mappings from the Rhino model.

    Args:
        model: The Rhino 3DM model
        map_materials: Whether to map materials from the 3dm file

    Returns:
        Tuple containing:
        - material_name_to_ids: Mapping from material name to list of object IDs
        - object_to_material: Mapping from object ID to material ID
        - material_to_surfaces: Mapping from material ID to list of surface indices
    """
    material_name_to_ids: Dict[str, List[str]] = {}
    object_to_material: Dict[str, str] = {}
    material_to_surfaces: Dict[str, List[int]] = {}

    if map_materials:
        material_to_id: Dict[str, str] = {}
        for obj in model.Objects:
            if isinstance(obj.Geometry, rhino3dm.Mesh):
                material_name = obj.Geometry.GetUserString("material_name")
                if material_name:
                    material_to_id[f"{obj.Attributes.Id}"] = material_name

        # Reverse the mapping to be from material name to list of IDs
        for id_val, material_name in material_to_id.items():
            if material_name not in material_name_to_ids:
                material_name_to_ids[material_name] = []
            material_name_to_ids[material_name].append(id_val)

    # Identify materials/layers for all objects
    for obj in model.Objects:
        if not isinstance(obj.Geometry, rhino3dm.Mesh):
            continue

        # Material assignment logic
        if obj.Attributes.MaterialIndex > 0:
            material_id = f"M_{obj.Attributes.MaterialIndex}"
        elif obj.Attributes.LayerIndex > 0:
            material_id = f"M_{obj.Attributes.LayerIndex}"
        else:
            material_id = "M_1"

        object_to_material[obj.Attributes.Id] = material_id

        if material_id not in material_to_surfaces:
            material_to_surfaces[material_id] = []

    return material_name_to_ids, object_to_material, material_to_surfaces


def process_mesh_vertices(
    mesh: rhino3dm.Mesh,
) -> Tuple[Dict[int, str], Dict[Tuple[Union[int, float], ...], int], Dict[int, int]]:
    """
    Process mesh vertices and create Gmsh points.

    Args:
        mesh: The Rhino mesh

    Returns:
        Tuple containing:
        - points: Dictionary mapping point index to point definition
        - coord_to_point_index: Mapping from coordinates to point index
        - vertex_map: Mapping from mesh vertex index to Gmsh point index
    """
    points: Dict[int, str] = {}
    coord_to_point_index: Dict[Tuple[Union[int, float], ...], int] = {}
    vertex_map: Dict[int, int] = {}
    point_index = 1

    for i, vertex in enumerate(mesh.Vertices):
        rounded_x = format_coord(vertex.X)
        rounded_y = format_coord(vertex.Y)
        rounded_z = format_coord(vertex.Z)

        coord = (rounded_x, rounded_y, rounded_z)
        if coord not in coord_to_point_index:
            points[point_index] = f"Point({point_index}) = {{ {rounded_x}, {rounded_y}, " f"{rounded_z}, 1.0 }};\n"
            coord_to_point_index[coord] = point_index
            point_index += 1
        vertex_map[i] = coord_to_point_index[coord]

    return points, coord_to_point_index, vertex_map


def process_mesh_faces(
    mesh: rhino3dm.Mesh,
    vertex_map: Dict[int, int],
    material_id: str,
    object_id: str,
    material_to_surfaces: Dict[str, List[int]],
    obj_id_to_surfaces: Dict[str, List[int]],
    surface_index: int,
) -> Tuple[Set[Tuple[int, int]], Dict[int, List[Tuple[int, int]]], int, List[int]]:
    """
    Process mesh faces and collect edges and face information.

    Args:
        mesh: The Rhino mesh
        vertex_map: Mapping from mesh vertex index to Gmsh point index
        material_id: The material ID for this mesh
        object_id: The object ID for this mesh
        material_to_surfaces: Mapping from material ID to surface indices
        obj_id_to_surfaces: Mapping from object ID to surface indices
        surface_index: The current surface index

    Returns:
        Tuple containing:
        - edges: Set of unique edges
        - face_to_edges: Mapping from face index to face edges
        - surface_index: The updated surface index
        - object_surface_indices: List of surface indices for this object
    """
    edges: Set[Tuple[int, int]] = set()
    face_to_edges: Dict[int, List[Tuple[int, int]]] = {}
    object_surface_indices: List[int] = []

    for i in range(mesh.Faces.Count):
        face = mesh.Faces[i]

        # Get face indices based on face type (triangle or quad)
        face_indices: Optional[List[int]] = None
        if len(face) == 4:
            face_indices = [face[0], face[1], face[2], face[3]]
        elif len(face) == 3:
            face_indices = [face[0], face[1], face[2]]

        if not face_indices:
            continue  # Skip non-triangle/quad faces

        # Collect the edges for this face
        face_edges: List[Tuple[int, int]] = []
        face_vertices: List[int] = []

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
            edges.add(edge)  # type: ignore

        # Store the face edges for later line loop creation
        face_to_edges[surface_index] = face_edges

        # Add to material surface list
        material_to_surfaces[material_id].append(surface_index)

        # Also track by object ID for material mapping
        obj_id_to_surfaces[object_id].append(surface_index)

        object_surface_indices.append(surface_index)
        surface_index += 1

    return edges, face_to_edges, surface_index, object_surface_indices


# flake8: noqa: E501
def create_lines_from_edges(
    edges: Set[Tuple[int, int]]
) -> Tuple[Dict[int, str], Dict[Tuple[int, int], int], List[int]]:
    """
    Create Gmsh lines from collected edges.

    Args:
        edges: Set of unique edges

    Returns:
        Tuple containing:
        - lines: Dictionary mapping line index to line definition
        - edge_to_line_index: Mapping from edge to line index
        - physical_lines: List of line indices for physical line group
    """
    lines: Dict[int, str] = {}
    edge_to_line_index: Dict[Tuple[int, int], int] = {}
    physical_lines: List[int] = []

    line_index = 1
    for edge in sorted(edges):  # Sort edges for consistent ordering
        a, b = edge
        lines[line_index] = f"Line({line_index}) = {{ {a}, {b} }};\n"
        edge_to_line_index[edge] = line_index
        physical_lines.append(line_index)
        line_index += 1

    return lines, edge_to_line_index, physical_lines


def create_line_loops(
    face_to_edges: Dict[int, List[Tuple[int, int]]],
    edge_to_line_index: Dict[Tuple[int, int], int],
) -> Tuple[Dict[int, str], Dict[int, str]]:
    """
    Create line loops and plane surfaces from face edges.

    Args:
        face_to_edges: Mapping from face index to face edges
        edge_to_line_index: Mapping from edge to line index

    Returns:
        Tuple containing:
        - line_loops: Dictionary mapping loop index to line loop definition
        - plane_surfaces: Dictionary mapping surface index to surface definition
    """
    line_loops: Dict[int, str] = {}
    plane_surfaces: Dict[int, str] = {}

    for face_idx, face_edges in face_to_edges.items():
        # Extract ordered vertices from face edges
        edge_vertices: List[int] = []
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
        line_loop_indices: List[int] = []
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

    return line_loops, plane_surfaces


def create_physical_surfaces(
    map_materials: bool,
    material_name_to_ids: Dict[str, List[str]],
    obj_id_to_surfaces: Dict[str, List[int]],
    material_to_surfaces: Dict[str, List[int]],
) -> Dict[str, str]:
    """
    Create physical surface definitions based on materials.

    Args:
        map_materials: Whether to map materials from the 3dm file
        material_name_to_ids: Mapping from material name to list of object IDs
        obj_id_to_surfaces: Mapping from object ID to surface indices
        material_to_surfaces: Mapping from material ID to surface indices

    Returns:
        Dictionary mapping physical surface ID to physical surface definition
    """
    physical_surfaces: Dict[str, str] = {}

    if map_materials and material_name_to_ids:
        # If mapping materials, create physical surfaces based on material names
        for obj_id, surfaces in obj_id_to_surfaces.items():
            if surfaces:
                physical_surfaces[obj_id] = (
                    f"Physical Surface(\"{obj_id}\") = " f"{{ {', '.join(map(str, surfaces))} }};\n"
                )
    else:
        # Otherwise use the material/layer based groups
        for material_id, surface_list in material_to_surfaces.items():
            if surface_list:
                physical_surfaces[material_id] = (
                    f"Physical Surface(\"{material_id}\") = " f"{{ {', '.join(map(str, surface_list))} }};\n"
                )

    return physical_surfaces


def write_geo_file(
    geo_file_path: str,
    points: Dict[int, str],
    lines: Dict[int, str],
    line_loops: Dict[int, str],
    plane_surfaces: Dict[int, str],
    physical_surfaces: Dict[str, str],
    physical_lines: List[int],
    volume_name: str,
) -> None:
    """
    Write the Gmsh GEO file.

    Args:
        geo_file_path: Path to output the geo file
        points: Dictionary mapping point index to point definition
        lines: Dictionary mapping line index to line definition
        line_loops: Dictionary mapping loop index to line loop definition
        plane_surfaces: Dictionary mapping surface index to surface definition
        physical_surfaces: Dictionary mapping physical surface ID to definition
        physical_lines: List of line indices for physical line group
        volume_name: Name for the Physical Volume
    """
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
        geo_file.write("Mesh.Optimize = 1; // Gmsh smoother, works with boundary layers.\n")
        geo_file.write("Mesh.CharacteristicLengthFromPoints = 1;\n")
        geo_file.write("// Recombine Surface \"*\";\n")


def convert_3dm_to_geo(
    rhino_file_path: str, geo_file_path: str, volume_name: str = "RoomVolume", map_materials: bool = True
) -> bool:
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
    try:
        model = rhino3dm.File3dm.Read(rhino_file_path)

        # Get material mappings
        material_name_to_ids, object_to_material, material_to_surfaces = get_material_mappings(model, map_materials)

        # Initialize data structures
        master_points: Dict[int, str] = {}
        master_coord_to_point_index: Dict[Tuple[Union[int, float], ...], int] = {}
        master_edges: Set[Tuple[int, int]] = set()
        face_to_edges: Dict[int, List[Tuple[int, int]]] = {}
        obj_id_to_surfaces: Dict[str, List[int]] = {
            obj.Attributes.Id: [] for obj in model.Objects if isinstance(obj.Geometry, rhino3dm.Mesh)
        }

        surface_index = 1

        # Process all meshes
        for obj in model.Objects:
            if not isinstance(obj.Geometry, rhino3dm.Mesh):
                continue

            mesh = obj.Geometry
            mesh.Faces.ConvertTrianglesToQuads(0.5, 0)
            mesh.Vertices.CombineIdentical(True, True)

            # Process vertices for this mesh
            points, coord_to_point_index, vertex_map = process_mesh_vertices(mesh)

            # Update master points dictionary
            point_index_offset = len(master_points)
            for i, point_str in points.items():
                if i > point_index_offset:
                    master_points[i] = point_str

            # Update master coordinates dictionary
            for coord, idx in coord_to_point_index.items():
                if coord not in master_coord_to_point_index:
                    master_coord_to_point_index[coord] = idx

            # Process faces for this mesh
            material_id = object_to_material[obj.Attributes.Id]
            edges, obj_face_to_edges, surface_index, _ = process_mesh_faces(
                mesh,
                vertex_map,
                material_id,
                obj.Attributes.Id,
                material_to_surfaces,
                obj_id_to_surfaces,
                surface_index,
            )

            # Update master edges and face_to_edges
            master_edges.update(edges)
            face_to_edges.update(obj_face_to_edges)

        # Create lines
        lines, edge_to_line_index, physical_lines = create_lines_from_edges(master_edges)

        # Create line loops and plane surfaces
        line_loops, plane_surfaces = create_line_loops(face_to_edges, edge_to_line_index)

        # Create physical surfaces
        physical_surfaces = create_physical_surfaces(
            map_materials, material_name_to_ids, obj_id_to_surfaces, material_to_surfaces
        )

        # Write the GEO file
        write_geo_file(
            geo_file_path,
            master_points,
            lines,
            line_loops,
            plane_surfaces,
            physical_surfaces,
            physical_lines,
            volume_name,
        )

        print(f"Converted {rhino_file_path} to {geo_file_path}")
        return os.path.exists(geo_file_path)

    except Exception as e:
        print(f"Error converting file: {e}")
        return False
