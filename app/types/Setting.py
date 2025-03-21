from enum import Enum


class Setting(Enum):
    Default = "Default"
    Advanced = "Advanced"
    
class SettingType(Enum):
    SimulationSettings = "simulationSettings"