import sys

import numpy as np
from PyQt5.QtWidgets import QApplication
import shell_struct
import constraints
import forces
from Visualizer import StructureViewerWidget
import element
import node
import structure
import shell


def main():
    # setup structure with nodes
    node0 = node.Node(0, 0, 0)
    node1 = node.Node(0, 1, 0)
    node2 = node.Node(0, 2, 0)
    node3 = node.Node(1, 0, 0.1)
    node4 = node.Node(1, 1, 0.1)
    node5 = node.Node(1, 2, 0.1)
    node6 = node.Node(2, 0, 0.3)
    node7 = node.Node(2, 1, 0.3)
    node8 = node.Node(2, 2, 0.3)

    ref_sys = np.array([1,0,0])

    node0.constraints = constraints.Constraint(False, False, False)
    node1.constraints = constraints.Constraint(False, True, False)
    node2.constraints = constraints.Constraint(True, False, False)


    element0 = shell.Shell(node0, node1, node4, node3, ref=ref_sys)
    element1 = shell.Shell(node1, node2, node5, node4, ref=ref_sys)
    element2 = shell.Shell(node3, node4, node7, node6, ref=ref_sys)
    element3 = shell.Shell(node4, node5, node8, node7, ref=ref_sys)


    shell_struct_1 = shell_struct.ShellStructure()

    shell_struct_1.add_element(element0)
    shell_struct_1.add_element(element1)
    shell_struct_1.add_element(element2)
    shell_struct_1.add_element(element3)

    app = QApplication(sys.argv) # Initialize Qt app
    window = StructureViewerWidget(shell_struct_1)
    window.setWindowTitle("OOP_FEM")
    window.resize(900,600)
    window.show()
    sys.exit(app.exec_()) #kills the app when closed

if __name__ == '__main__':
    main()
