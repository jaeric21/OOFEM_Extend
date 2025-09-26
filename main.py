import sys

from PyQt5.QtWidgets import QApplication

import constraints
import forces
from Visualizer import StructureViewerWidget
import element
import node
import structure


def main():
    # setup structure with nodes
    node0 = node.Node(0, 1, 0)
    node1 = node.Node(1, 0, 0)
    node2 = node.Node(1, 1, 0)
    node3 = node.Node(0, 0, 0)
    node4 = node.Node(0.5, 0.5, 1)

    node0.constraints = constraints.Constraint(False, False, False)
    node3.constraints = constraints.Constraint(False, True, False)
    node2.constraints = constraints.Constraint(True, False, False)


    node4.force = forces.Force(0, 0, -200)

    A = 10
    E = 200

    element0 = element.Element(E, A, node0, node2)
    element1 = element.Element(E, A, node1, node2)
    element2 = element.Element(E, A, node1, node3)
    element3 = element.Element(E, A, node3, node0)
    element4 = element.Element(E, A, node0, node4)
    element5 = element.Element(E, A, node1, node4)
    element6 = element.Element(E, A, node2, node4)
    element7 = element.Element(E, A, node3, node4)

    struct_1 = structure.Structure()

    struct_1.add_element(element0)
    struct_1.add_element(element1)
    struct_1.add_element(element2)
    struct_1.add_element(element3)
    struct_1.add_element(element4)
    struct_1.add_element(element5)
    struct_1.add_element(element6)
    struct_1.add_element(element7)


    app = QApplication(sys.argv) # Initialize Qt app
    window = StructureViewerWidget(struct_1)
    window.setWindowTitle("OOP_FEM")
    window.resize(900,600)
    window.show()
    sys.exit(app.exec_()) #kills the app when closed

if __name__ == '__main__':
    main()
