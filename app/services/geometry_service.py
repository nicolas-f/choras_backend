import logging
from flask_smorest import abort
from app.db import db
from app.models import Geometry, Task, File
from app.types import TaskType, Status
import config
import trimesh
import numpy as np
import rhino3dm
import os
import zipfile

# Create logger for this module
logger = logging.getLogger(__name__)


def get_geometry_by_id(geometry_id):
    results = Geometry.query.filter_by(id=geometry_id).first()
    return results


def start_geometry_check_task(file_upload_id):
    try:
        task = Task(
            taskType=TaskType.GeometryCheck,
            status=Status.Created
        )
        db.session.add(task)
        db.session.commit()
        geometry = Geometry(
            inputModelUploadId=file_upload_id,
            taskId=task.id
        )

        db.session.add(geometry)
        db.session.commit()

        result = map_to_3dm(geometry.id)
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


def map_to_3dm(geometry_id):
    geometry = Geometry.query.filter_by(id=geometry_id).first()
    file = File.query.filter_by(id=geometry.inputModelUploadId).first()
    task = Task.query.filter_by(id=geometry.taskId).first()

    directory = config.DefaultConfig.UPLOAD_FOLDER
    file_name, file_extension = os.path.splitext(
        os.path.basename(file.fileName)
    )

    obj_path = os.path.join(directory, file.fileName)
    obj_clean_path = os.path.join(directory, f"{file_name}_clean{file_extension}")
    rhino3dm_path = os.path.join(directory, f"{file_name}.3dm")
    zip_file_path = os.path.join(directory, f"{file_name}.zip")
    try:
        task.status = Status.InProgress
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not update task status! Error: {ex}")

    clean_obj_file(obj_path, obj_clean_path)

    convert_obj_to_3dm(obj_clean_path, rhino3dm_path)

    if not os.path.exists(rhino3dm_path):
        return False

    try:
        file3dm = File(
            fileName=f"{file_name}.3dm"
        )
        db.session.add(file3dm)
        db.session.commit()
        geometry.outputModelId = file3dm.id

        # Create a zip file from 3dm
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            zipf.write(directory, arcname=f"{file_name}.3dm")

        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not create a rhino file: {ex}")

    return True


def clean_obj_file(obj_file_path, obj_clean_path):
    with open(obj_file_path, 'r') as infile, open(obj_clean_path, 'w') as outfile:
        lines = infile.readlines()
        current_material = None
        custom_material_counter = 1

        for line in lines:
            if line.startswith('usemtl'):
                current_material = line.strip()
            elif line.startswith('f'):
                if current_material:
                    outfile.write(current_material + '\n')
                else:
                    custom_material = f'usemtl M_{custom_material_counter}\n'
                    outfile.write(custom_material)
                    current_material = custom_material.strip()
                    custom_material_counter += 1
                outfile.write(line)
            else:
                outfile.write(line)


def convert_obj_to_3dm(obj_clean_path, rhino_path):
    print(rhino_path)
    # Load the OBJ file using trimesh
    scene = trimesh.load(obj_clean_path, group_material=False, skip_materials=False, maintain_order=True)

    # Create a new 3dm file
    model = rhino3dm.File3dm()

    # Check if the loaded object is a scene with multiple geometries
    if isinstance(scene, trimesh.Scene):
        meshes = scene.dump()
    else:
        meshes = [scene]

    # Define a 90-degree rotation matrix around the X-axis
    rotation_matrix = np.array([
        [1, 0, 0],
        [0, 0, -1],
        [0, 1, 0]
    ])

    for mesh in meshes:
        vertices = mesh.vertices
        faces = mesh.faces

        rhino_mesh = rhino3dm.Mesh()

        for vertex in vertices:
            rotated_vertex = np.dot(rotation_matrix, vertex)
            rhino_mesh.Vertices.Add(rotated_vertex[0], rotated_vertex[1], rotated_vertex[2])
            # rhino_mesh.Vertices.Add(vertex[0], vertex[2], vertex[1])  # Swap Y and Z axes
            # rhino_mesh.Vertices.Add(vertex[0], vertex[1], vertex[2]) # X, Y, Z

        for face in faces:
            if len(face) == 3:  # Triangular face
                rhino_mesh.Faces.AddFace(face[0], face[1], face[2])
            elif len(face) == 4:  # Quad face
                rhino_mesh.Faces.AddFace(face[0], face[1], face[2], face[3])

        model.Objects.AddMesh(rhino_mesh)

    # Save the 3dm file
    model.Write(rhino_path)
    return rhino_path
