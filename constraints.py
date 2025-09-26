# Class for contraints


import numpy as np


class Constraint:
    def __init__(self, dof1=True, dof2=True, dof3=True, dof4=True, dof5=True):
        self._free = np.array([dof1, dof2, dof3, dof4, dof5], dtype=bool)

    def get_constraints(self) -> np.ndarray:
        return self._free