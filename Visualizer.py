import sys

import matplotlib
import numpy as np
from PyQt5 import QtWidgets
from pyvistaqt import QtInteractor
import pyvista as pv
import structure
import matplotlib.pyplot as plt
import matplotlib

# TODO: make add node button
# TODO: make remove node and element. If node removed, remove all elemnts

class StructureViewerWidget(QtWidgets.QWidget):
    # makes this class a Qt GUI component. Qt works with inheritance
    def __init__(self, s: structure.Structure):
        super().__init__() #Initializes the Qt
        self.structure = s
        self.plotter = QtInteractor(self) #makes pyvista 3D viewer and embeds it in the pyqt widget

        self.label_visibility = {
            'nodes': False,
            'elements': False,
            'constraints': False,
            'forces': False
        }

        self._build_ui()
        self._draw_elements()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        button_layout = QtWidgets.QHBoxLayout()

        # Makes Button to show Nodes (triggers toggle_node_ids)
        self.btn_nodes = QtWidgets.QPushButton("Show Node IDs") # adds the button with name
        self.btn_nodes.clicked.connect(lambda: self.toggle_labels('nodes')) # assgins the button to the method
        button_layout.addWidget(self.btn_nodes) # adds the button to the layout

        self.btn_elements = QtWidgets.QPushButton("Show Element IDs")
        self.btn_elements.clicked.connect(lambda: self.toggle_labels('elements'))
        button_layout.addWidget(self.btn_elements)

        self.btn_constraints = QtWidgets.QPushButton("Show Constraints")
        self.btn_constraints.clicked.connect(lambda: self.toggle_labels('constraints'))
        button_layout.addWidget(self.btn_constraints)

        self.btn_forces = QtWidgets.QPushButton("Show Forces")
        self.btn_forces.clicked.connect(lambda: self.toggle_labels('forces'))
        button_layout.addWidget(self.btn_forces)

        self.btn_assemble_matrix = QtWidgets.QPushButton("Assemble Stiffnessmatrix")
        self.btn_assemble_matrix.clicked.connect(self._assemble_matrix)
        button_layout.addWidget(self.btn_assemble_matrix)

        self.btn_solve_matrix = QtWidgets.QPushButton("Solve")
        self.btn_solve_matrix.clicked.connect(self._solve_matrix)
        button_layout.addWidget(self.btn_solve_matrix)

        self.btn_show_results = QtWidgets.QPushButton("Show Results")
        self.btn_show_results.clicked.connect(self.show_results)
        button_layout.addWidget(self.btn_show_results)

        layout.addLayout(button_layout)
        layout.addWidget(self.plotter.interactor)
        # conects the viewer

    def _solve_matrix(self):
        self.structure.solve()

    #def show_results(self):
#
    #    sigma_values = [e.get_sigma() for e in self.structure.elements]
    #    sigma_min = min(sigma_values)
    #    sigma_max = max(sigma_values)
#
    #    for e in self.structure.elements:
    #        line = pv.Line(e.node1.node_position, e.node2.node_position)
    #        sigma = e.get_sigma()
#
    #        if sigma_max != sigma_min:
    #            #interpolate color and catch zero division
    #            t = (sigma - sigma_min) / (sigma_max - sigma_min)
    #        else:
    #            t =  0.5
#
    #        # Add colored mesh
    #        self.plotter.add_mesh(
    #            line,
    #            color=matplotlib.cm.get_cmap('viridis')(t)[0:3],
    #            line_width=5,
    #            name="elements_results"
    #        )
#
    #    self.plotter.add_scalar_bar(title="Sigma", n_labels=5)
    #    self.plotter.render()
    def show_results(self):

        # clear prior result
        if hasattr(self, 'result_actor'):
            self.plotter.remove_actor(self.result_actor)


        lines = []
        scalars = []
        for elem in self.structure.elements:
            lines.append(np.vstack([elem.node1.node_position, elem.node2.node_position]))
            scalars.append(elem.get_sigma())

        all_points = np.vstack(lines)
        n_lines = len(lines)

        # Build connectivity for PolyData
        # Each line has 2 points → each line cell is [2, idx0, idx1]
        cells = []
        for i in range(n_lines):
            cells.append([2, 2 * i, 2 * i + 1])
        cells = np.hstack(cells)

        pd = pv.PolyData()
        pd.points = all_points
        pd.lines = cells
        pd["sigma"] = np.repeat(scalars, 2)  # repeat scalar per point for coloring


        tube = pd.tube(radius=0.02)  # adjust radius as needed

        # Add to plotter
        self.result_actor = self.plotter.add_mesh(tube, scalars="sigma", cmap="viridis")
        self.plotter.reset_camera()
        self.plotter.render()


    def _assemble_matrix(self):
        self.structure.assemble_global_stiffness_matrix()
        self.structure.assemble_forces_matrix()

    def _draw_elements(self):
        # draws all elements of the structure separately
        for element in self.structure.elements:
            line = pv.Line(element.node1.node_position, element.node2.node_position)
            self.plotter.add_mesh(line, color="black")
        self.plotter.show_axes()

    def toggle_labels(self, label_type):
        is_visible = self.label_visibility[label_type]
        if is_visible:
            self.plotter.remove_actor(f"{label_type}_labels")
        else:
            if label_type == 'nodes':
                points = [node.node_position for node in self.structure.get_unique_nodes()]
                labels = [f"N{node.id}" for node in self.structure.get_unique_nodes()]
                self.plotter.add_point_labels(
                    points, labels, font_size=12,
                    point_color='white', text_color='black',
                    name=f"{label_type}_labels"
                )

            elif label_type == 'elements':
                points = [(elem.node1.node_position + elem.node2.node_position) / 2 for elem in self.structure.elements]
                labels = [f"E{elem.id}" for elem in self.structure.elements]
                self.plotter.add_point_labels(
                    points, labels, font_size=12,
                    point_color='white', text_color='black',
                    name=f"{label_type}_labels"
                )

            elif label_type == 'constraints':

                points = [node.node_position for node in self.structure.get_unique_nodes() if node.check_constraints()]
                labels = [f"C{node.print_constraints()}" for node in self.structure.get_unique_nodes() if node.check_constraints()]
                self.plotter.add_point_labels(
                    points, labels, font_size=12,
                    point_color='white', text_color='black',
                    name=f"{label_type}_labels"
                )

            elif label_type == 'forces':

                points = [node.node_position for node in self.structure.get_unique_nodes() if node.check_forces()]
                vectors = [node.force.get_components() for node in self.structure.get_unique_nodes() if node.check_forces()]

                self.plotter.add_arrows(np.array(points), np.array(vectors), mag=0.1, name=f"{label_type}_labels")

        self.label_visibility[label_type] = not is_visible
        self.plotter.render()