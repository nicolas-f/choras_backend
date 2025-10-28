# This is the example interface file for connecting CHORAS to your simulation method
from collections import defaultdict
from itertools import combinations
from time import sleep

# Import the relevant functions from your package (/submodule)
import libsimpa
import gmsh
import json
from headless_backend.HelperFunctions import *
import numpy as np

def convertGeoFileToCBINModel(geo_file_path, cbin_file_path, cmbin_file_path):
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
        gmsh.model.mesh.generate()
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
                new_face = libsimpa.ioFace()
                new_face.a = int(face[0])
                new_face.b = int(face[1])
                new_face.c = int(face[2])
                new_face.idEn = 0
                new_face.idMat = 0
                new_face.idRs = 0
                outputModel.faces.append(new_face)
            print("surface_group_name: ", surface_group_name)
        driver = libsimpa.CformatBIN()
        driver.ExportBIN(cbin_file_path, outputModel)
        print("3d model exported to: ", cbin_file_path)
        # Export tetrahedral mesh
        element_types, element_tags, node_tags = gmsh.model.mesh.getElements(dim=3)
        # Assume the first element type is tetrahedron
        tetra_type = element_types[0]
        _, _, _, num_nodes_per_tetra, _, _ = gmsh.model.mesh.getElementProperties(tetra_type)
        tetrahedrons = node_tags[0].reshape(-1,
                                            num_nodes_per_tetra)  # each row corresponds to a tetrahedron's vertices node tags

        tetramesh = libsimpa.trimeshmodel()
        for vertex in coords:
            tetramesh.nodes.append(libsimpa.t_binNode(vertex[0], vertex[1], vertex[2]))
        # First loop to index the relation between faces and tetrahedrons index# Create a dictionary mapping each face to a list of tetrahedron indices
        face_index = defaultdict(list)
        for i, tet in enumerate(tetrahedrons):
            for face in combinations(tet, 3):
                face_index[tuple(sorted(face))].append(i)
        tetrahedron_faces_index = list(reversed(list(combinations(range(4), 3))))
        for id_tetra, tetrahedron in enumerate(tetrahedrons):
            id_volume = 0
            tetra_faces = []
            for id_face in range(0, 4):
                face_vertices = [tetrahedron[tetrahedron_faces_index[id_face][i]] for i in range(3)]
                marker = 0
                neighbor = next((x for x in face_index[tuple(sorted(face_vertices))] if x != id_tetra), -1)
                new_face = libsimpa.bintetraface(int(face_vertices[0]), int(face_vertices[1]), int(face_vertices[2]), marker, neighbor)
                tetra_faces.append(new_face)
            # bintetrahedre(const Intb& _a, const Intb& _b, const Intb& _c, const Intb& _d, const Intb& _idVolume,
            # 			const bintetraface& faceA, const bintetraface& faceB, const bintetraface& faceC, const bintetraface& faceD)
            tetramesh.tetrahedres.append(libsimpa.bintetrahedre(int(tetrahedron[0]), int(tetrahedron[1]),
                                                                int(tetrahedron[2]), int(tetrahedron[3]), id_volume,
                                                                tetra_faces[0], tetra_faces[1], tetra_faces[2],
                                                                tetra_faces[3]))
        libsimpa.CMBIN().SaveMesh(cmbin_file_path, tetramesh)
        print("3D mesh exported to: ", cmbin_file_path)
# This function will be called from app/services/simulation_service.py 
# and the main function below
def mynewmethod_method(json_file_path=None):
    # Read the input configuration
    with open(json_file_path) as json_file:
        data = json.load(json_file)
    dirname = os.path.dirname(__file__)
    cbin_output_path = os.path.join(dirname, "model.cbin")
    cmbin_output_path = os.path.join(dirname, "model.cmbin")
    convertGeoFileToCBINModel(data["geo_path"], cbin_output_path, cmbin_output_path)
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
