# Class for Nodes
import numpy as np
import forces
import constraints

from itertools import count

class Node:
    _node_ids = count(0)
    def __init__(self, x1: float, x2: float, x3: float) -> None:
        self.id = next(self._node_ids)
        self.node_position = np.array([x1, x2, x3], dtype=float)
        self._dofNumbers = np.zeros(5, dtype=int)  # jetzt 5 DOFs
        self.force = forces.Force(0, 0, 0, 0, 0)  # Force-Klasse anpassen
        self.constraints = constraints.Constraint(True, True, True, True, True)  # jetzt 5 DOFs
        self._displacement = np.zeros(5, dtype=float)
        self.displaced= np.zeros(3, dtype=float)

    def print(self) -> None:
        print(self.node_position)

    def enumerateDOFs(self, start:int)->int:
        _number = start
        for i, u in enumerate(self.constraints.get_constraints()):
            if u:
                self._dofNumbers[i] = _number
                _number += 1
            else:
                self._dofNumbers[i] = -1
        return _number

    def getDOFNumbers(self):
        return self._dofNumbers

    def check_forces(self)->bool:
        return any(c != 0 for c in self.force.get_components())

    def check_constraints(self)->bool:
        return not all(self.constraints.get_constraints())

    def print_constraints(self)->str:
        return 'xyz'

    def print_displacement(self)->None:
        print(f'Node ID: {str(self.id)}, {self._displacement[0:3]}')

    def set_displacement(self, xyz, u)->None:
        self._displacement[xyz] = u

    def get_displacement(self):
        return self._displacement

    def calculate_new_position(self):
        self.displaced = self.node_position + self._displacement[0:3]

if __name__ == "__main__":
    node_1 = Node(0, 0, 0)
    node_2 = Node(0, 0, 1)
    node_3 = Node(0, 0, 2)

    force_1 = forces.Force(0, 4, 0)
    node_1.force = force_1

    node_2.constraints = constraints.Constraint(True, True, False)

    print(node_3.check_forces())
    print(node_1.check_forces())
    print(node_2.check_constraints())
    print(node_3.check_constraints())
