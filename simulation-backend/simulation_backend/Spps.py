# This is the example interface file for connecting CHORAS to your simulation method
from time import sleep

# Import the relevant functions from your package (/submodule)
import libsimpa
import gmsh
import json
from headless_backend.HelperFunctions import *
import numpy as np

def convertGeoFileToCBINModel(geo_file_path, cbin_file_path):
    outputModel = libsimpa.ioModel()
    gmsh.initialize()
    gmsh.open(geo_file_path)
    for modelName in gmsh.model.list():
        gmsh.model.setCurrent(modelName)
        print("Model name: ", modelName)
        dim = 2
        surface_group_tags = gmsh.model.getPhysicalGroups(dim=dim)
        surface_group_names = [
            gmsh.model.getPhysicalName(element_type, tag)
            for (element_type, tag) in surface_group_tags
        ]
        gmsh.model.mesh.generate(dim)
        node_tags_all, coords_all, _ = gmsh.model.mesh.getNodes()
        coords = coords_all.reshape((len(node_tags_all), 3))
        mesh_kind = 3
        # Push vertices and faces to the cbin model
        for vertex in coords:
            outputModel.vertices.append(libsimpa.t_pos(vertex[0], vertex[1], vertex[2]))
        for surface_group_name in surface_group_names:

            dim_tags = gmsh.model.getEntitiesForPhysicalName(surface_group_name)
            _, node_tags_group = dim_tags[0]

            face_nodes = gmsh.model.mesh.getElementFaceNodes(
                dim, mesh_kind, tag=node_tags_group)
            faces = np.reshape(face_nodes, (len(face_nodes) // mesh_kind, mesh_kind))
            for face in faces:
                # ioFace(indiceV _a, indiceV _b, indiceV _c, indiceMat _idMat, indiceRS _idRs, indiceEN _idEn)
                newface = libsimpa.ioFace()
                newface.a = int(face[0])
                newface.b = int(face[1])
                newface.c = int(face[2])
                newface.idEn = 0
                newface.idMat = 0
                newface.idRs = 0
                outputModel.faces.append(newface)
            print("surface_group_name: ", surface_group_name)
            print(faces)
        driver = libsimpa.CformatBIN()
        driver.ExportBIN(cbin_file_path, outputModel)
        print("3d model exported to: ", cbin_file_path)


# This function will be called from app/services/simulation_service.py 
# and the main function below
def mynewmethod_method(json_file_path=None):
    # Read the input configuration
    with open(json_file_path) as json_file:
        data = json.load(json_file)
    dirname = os.path.dirname(__file__)
    cbin_output_path = os.path.join(dirname, "model.cbin")
    convertGeoFileToCBINModel(data["geo_path"], cbin_output_path)
    print("mynewmethod_method: starting simulation")
    print("mynewmethod_method: simulation done!")


if __name__ == "__main__":
    import os

    # Load the input file
    file_name = find_input_file_in_subfolders(
        os.path.dirname(__file__), "exampleInput_MyNewMethod.json"
    )
    json_tmp_file = create_tmp_from_input(file_name)

    # Run the method
    mynewmethod_method(json_tmp_file)

    # Save the results to a separate file
    save_results(json_tmp_file)
