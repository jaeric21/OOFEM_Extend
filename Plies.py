from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np
import helpers
import Material


@dataclass
class Ply:
    material: Material.PropertiesComposite
    thickness: float
    rotation_angle: float
    local_stiffness_matrix: Optional[np.array] = None
    global_stiffness_matrix: Optional[np.array] = None
    Q_11: Optional[float] = None
    Q_22: Optional[float] = None
    Q_66: Optional[float] = None
    Q_12: Optional[float] = None
    Q_21: Optional[float] = None

    def calc_local_stiffness_matrix(self):
        self.material.v_12 = self.material.E_2 / self.material.E_1 * self.material.v_31
        self.Q_11 = self.material.E_1 / (1 - self.material.v_12 * self.material.v_31)
        self.Q_22 = self.material.E_2 / (1 - self.material.v_12 * self.material.v_31)
        self.Q_66 = self.material.G_31
        self.Q_12 = (self.material.v_31 * self.material.E_1) / (1 - self.material.v_12 * self.material.v_31)
        self.Q_21 = (self.material.v_31 * self.material.E_2) / (1 - self.material.v_12 * self.material.v_31)
        self.local_stiffness_matrix = np.array([
            [self.Q_11, self.Q_21, 0],
            [self.Q_21, self.Q_22, 0],
            [0, 0, self.Q_66]
        ])

    def calc_global_stiffens_matrix(self):
        self.calc_local_stiffness_matrix()
        self.global_stiffness_matrix = (
                helpers.transform_stress_to_global(self.rotation_angle)
                @ self.local_stiffness_matrix
                @ helpers.transform_strains_to_local(self.rotation_angle))