# Class for structure
from numpy.ma.extras import unique

import element
import forces
import node
import constraints

import numpy as np
import matplotlib.pyplot as plt

class Structure:
    def __init__(self):
        self._global_stiffness_matrix = None
        self._global_force_vector = None
        self.elements = []
        self._nodes = []
        self._unique_nodes = []
        self._displacements = None

    def add_element(self, e:element.Element)->None:
            self.elements.append(e)

    def print_structure(self)->None:
        for i in self.elements:
            i.print()

    def get_unique_nodes(self)->list:
        self._list_nodes()
        return self._unique_nodes

    def _list_nodes(self) -> None:
        self._nodes = []
        for el in self.elements:
            # Unterstützt jetzt beliebig viele Knoten pro Element
            self._nodes.extend(el.nodes)
        self._unique_nodes = list(dict.fromkeys(self._nodes))

    def _enumerate_dofs(self)->None:
        self._list_nodes()
        self._numberofdofs = 0
        for n in self._unique_nodes:
            self._numberofdofs = n.enumerateDOFs(self._numberofdofs)

    def assemble_global_stiffness_matrix(self)->None:
        self._enumerate_dofs()
        self._global_stiffness_matrix = np.zeros((self._numberofdofs, self._numberofdofs))

        for e in self.elements:
            e.enumerate_dofs()
            for i_local, I in enumerate(e._dofNumbers):
                if I == -1:
                    continue
                for j_local, J in enumerate(e._dofNumbers):
                    if J == -1:
                        continue
                    self._global_stiffness_matrix[I, J] += e.stiffness_matrix_global[i_local, j_local]

        if np.isclose(np.linalg.det(self._global_stiffness_matrix), 0.0):
            missing_constraint = np.where(~self._global_stiffness_matrix.any(axis=1))[0]
            print(missing_constraint)
            for n in self._unique_nodes:
                if any(np.isin(n.getDOFNumbers(), missing_constraint)):
                    print(f'Node ID: {n.id}, DOF to lock: {np.where(np.isin(n.getDOFNumbers(), missing_constraint))[0]}')

    def assemble_forces_matrix(self)->None:

        self._global_force_vector = np.zeros(self._numberofdofs)

        for n in self._unique_nodes:
            for i_local, dof_num in enumerate(n._dofNumbers):
                if dof_num != -1:
                    self._global_force_vector[dof_num] += n.force.get_components()[i_local]
        print(self._global_force_vector)

    def solve(self)->None:
        if self._global_stiffness_matrix is None:
            self.assemble_global_stiffness_matrix()
        if self._global_force_vector is None:
            self.assemble_forces_matrix()

        self._displacements = None
        self._displacements = np.linalg.solve(self._global_stiffness_matrix, self._global_force_vector)
        self._set_nodal_displacements()

    def _set_nodal_displacements(self)->None:
        for n in self._unique_nodes:
            x = n.getDOFNumbers()
            for i_local, dof_num in enumerate(n.getDOFNumbers()):
                if dof_num == -1:
                    n.set_displacement(i_local, 0)
                else:
                    u = self._displacements[dof_num]
                    n.set_displacement(i_local, u)
            n.print_displacement()

def main():
    # main for testing
    # setup structure with nodes
    node0 = node.Node(0, 0, 0)
    node1 = node.Node(0, 1, 0)
    node2 = node.Node(0, 2, 0)
    node3 = node.Node(1, 0, 0)
    node4 = node.Node(1, 1, 0)
    node5 = node.Node(1, 2, 0)
    node6 = node.Node(2, 0, 0)
    node7 = node.Node(2, 1, 0)
    node8 = node.Node(2, 2, 0)

    ref_sys = np.array([1, 0, 0])

    node0.constraints = constraints.Constraint(False, False, False, False, False)
    node1.constraints = constraints.Constraint(False, False, False, False, False)
    node2.constraints = constraints.Constraint(False, False, False, False, False)
    node3.constraints = constraints.Constraint(True, True, False, True, True)
    node4.constraints = constraints.Constraint(True, True, False, True, True)
    node5.constraints = constraints.Constraint(True, True, False, True, True)
    node8.constraints = constraints.Constraint(True, True, False, True, True)
    node6.constraints = constraints.Constraint(True, True, False, True, True)
    node7.constraints = constraints.Constraint(True, True, False, True, True)
    node8.constraints = constraints.Constraint(True, True, False, True, True)

    node6.force = forces.Force(0,100, 0, 0, 0)
    node7.force = forces.Force(0,100, 0, 0, 0)
    node8.force = forces.Force(0,100, 0, 0, 0)

    element0 = element.Element(node0, node1, node4, node3, ref=ref_sys)
    element1 = element.Element(node1, node2, node5, node4, ref=ref_sys)
    element2 = element.Element(node3, node4, node7, node6, ref=ref_sys)
    element3 = element.Element(node4, node5, node8, node7, ref=ref_sys)

    shell_struct_1 = Structure()

    shell_struct_1.add_element(element0)
    shell_struct_1.add_element(element1)
    shell_struct_1.add_element(element2)
    shell_struct_1.add_element(element3)

    shell_struct_1.solve()


if __name__ == "__main__":
    main()
