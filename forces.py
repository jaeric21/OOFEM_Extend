# Force class
import numpy as np

class Force:
    def __init__(self, fx=0, fy=0, fz=0, mx=0, my=0):
        self._components = np.array([fx, fy, fz, mx, my], dtype=float)

    def get_components(self)->np.array:
        return self._components

    def set_components(self, components:np.ndarray)->None:
        self._components = components

    def print(self)->None:
        print(self._components)
