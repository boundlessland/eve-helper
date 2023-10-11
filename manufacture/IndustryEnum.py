from enum import Enum, unique


@unique
class ActivityID(Enum):
    Manufacturing = 1
    Researching_time_efficiency = 3
    Researching_material_efficiency = 4
    Copying = 5
    Invention = 8
    Reaction = 11


class IndustryRigMaterialEfficiency(Enum):
    T1 = 0.02
    T2 = 0.024
    Thukker = 0.02
    ThukkerCapital = 0.057


class IndustryStructureMaterialEfficiency(Enum):
    Sotiyo = 0.01
    Azbel = 0.01
    Raitaru = 0.01


class IndustryRigZoneCoefficient(Enum):
    Highsec = 1
    Lowsec = 1.9
    Zerosec = 2.1
    ThukkerHighsec = 0.1
    ThukkerLowsec = 1.9
    ThukkerZerosec = 0.1


@unique
class IndustryStructureCostEfficiency(Enum):
    Sotiyo = 0.05
    Azbel = 0.04
    Raitaru = 0.03