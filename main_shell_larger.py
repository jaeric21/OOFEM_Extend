import sys

import numpy as np
from PyQt5.QtWidgets import QApplication
import structure
import constraints
import forces
from Visualizer import StructureViewerWidget
import element
import node
import random
import Plies
import Laminate as lc
import Material

def main():

    # Here i use my Laminate calculator to make an layup and calc the stiffness matrix
    HR40 = Material.PropertiesComposite.from_yaml('MaterialData/HR40.yaml')
    T300 = Material.PropertiesComposite.from_yaml('MaterialData/T300.yaml')


    Lam_1 = lc.Laminate(entries=[
        Plies.Ply(material=T300, thickness=0.06999999999999999/1000, rotation_angle=np.deg2rad(45.0)),
        Plies.Ply(material=T300, thickness=0.06999999999999999/1000, rotation_angle=np.deg2rad(-45.0)),
        Plies.Ply(material=HR40, thickness=0.42108555560539107/1000, rotation_angle=np.deg2rad(76.41676256745913)),
        Plies.Ply(material=HR40, thickness=0.42108555560539107/1000, rotation_angle=np.deg2rad(-76.41676256745913)),
        Plies.Ply(material=HR40, thickness=0.8079430409060069/1000, rotation_angle=np.deg2rad(0.0))
    ])

    Lam_1.calc_ABD_matrices()


    ref_sys = np.array([1, 0, 0])

    #seting up a plate

    N = 5
    Lx, Ly, Lz = 2, 2, 0.4
    dx, dy, dz = Lx / N, Ly / N, Lz / N



    nodes = []
    for j in range(N + 1):  # N+1 nodes in each direction
        row = []
        for i in range(N + 1):
            row.append(node.Node(i * dx, j * dy,0))
        nodes.append(row)

    elements = []
    for j in range(N):
        for i in range(N):
            n0 = nodes[j][i]
            n1 = nodes[j + 1][i]
            n2 = nodes[j + 1][i + 1]
            n3 = nodes[j][i + 1]
            elements.append(element.Element(n0, n1, n2, n3, Lam_1, ref=ref_sys))

    # clamp on one side x=0 fully but only looking the y direction on one corener
    for row in nodes:
        for n in row:
            if n.node_position[0] == 0 and n.node_position[1] == 0:
                n.constraints = constraints.Constraint(False, False, False, False, False)
            elif n.node_position[0] == 0:
                n.constraints = constraints.Constraint(False, False, False, False, False)
            else:
                n.constraints = constraints.Constraint(True, True, False, True, True)

            if n.node_position[0] == Lx:
                n.force = forces.Force(5000, 1000, 1000, 0, 0)

    shell_struct_1 = structure.Structure()

    for e in elements:
        shell_struct_1.add_element(e)


    app = QApplication(sys.argv) # Initialize Qt app
    window = StructureViewerWidget(shell_struct_1)
    window.setWindowTitle("OOP_FEM")
    window.resize(900,600)
    window.show()
    sys.exit(app.exec_()) #kills the app when closed

if __name__ == '__main__':
    main()
