import numpy as np
from itertools import count
from dataclasses import dataclass
from typing import Optional
import yaml

class Material:
    _material_ids = count(0)

    def __init__(self, material_name, material_parameters):
        self.material_name = material_name
        self.parameters = material_parameters

@dataclass
class PropertiesComposite:
    name: str
    fibre_type: str
    vf: float
    E_1: float
    E_2: float
    G_31: float
    G_32: float
    v_31: float
    v_32: float
    R_1c: float
    R_1t: float
    R_2c: float
    R_2t: float
    R_31: float
    R_32: float
    roh: float
    v_12: Optional[float] = None
    p_13_minus: Optional[float] = None
    p_13_plus: Optional[float] = None
    p_32_minus: Optional[float] = None
    tau_21_c: Optional[float] = None

    @classmethod
    def from_yaml(cls, file_path):
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return cls(**data)