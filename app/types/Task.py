from enum import Enum


class TaskType(Enum):
    GeometryCheck = "GeometryCheck"
    Mesh = 'Mesh'
    DE = 'DE'  # Diffusion equation method: @ilaria
    DG = 'DG'  # Galerkin finite element method @Huiqing
