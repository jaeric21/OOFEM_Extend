import sys

import matplotlib
import numpy as np
from PyQt5 import QtWidgets
from charset_normalizer.md import annotations
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
        self.force_vector_magnitude = 0.001
        self.force_mag_field.valueChanged.connect(self._update_force_mag)

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

        self.btn_show_displaced = QtWidgets.QPushButton("show_displaced")
        self.btn_show_displaced.clicked.connect(self.show_displaced)
        button_layout.addWidget(self.btn_show_displaced)

        self.force_mag_field = QtWidgets.QDoubleSpinBox()
        self.force_mag_field.setRange(0.01, 10.0)  # reasonable range
        self.force_mag_field.setSingleStep(0.1)
        self.force_mag_field.setValue(0.1)  # default value
        self.force_mag_field.setDecimals(2)
        button_layout.addWidget(QtWidgets.QLabel("Force Vector Magnitude"))
        button_layout.addWidget(self.force_mag_field)

        self.strain_selector = QtWidgets.QComboBox()
        self.strain_selector.addItems(["εx", "εy", "εxy", "γxz", "γyz"])
        button_layout.addWidget(QtWidgets.QLabel("Strain Component"))
        button_layout.addWidget(self.strain_selector)

        self.btn_show_strain = QtWidgets.QPushButton("Show Strain")
        self.btn_show_strain.clicked.connect(self.show_strain)
        button_layout.addWidget(self.btn_show_strain)

        layout.addLayout(button_layout)
        layout.addWidget(self.plotter.interactor)

        # conects the viewer

    def _solve_matrix(self):
        self.structure.solve()

    def show_displaced(self):
        for element in self.structure.elements:
            # collect node coordinates
            points = np.array([n.displaced for n in element.nodes])

            if len(points) == 3:  # triangular shell
                faces = np.hstack([[3, 0, 1, 2]])
            elif len(points) == 4:  # quad shell
                faces = np.hstack([[4, 0, 1, 2, 3]])
            else:
                continue  # skip unsupported

            mesh = pv.PolyData(points, faces)
            self.plotter.add_mesh(mesh, color="lightgray", style="wireframe")  # or surface
        self.plotter.show_axes()

    def show_strain(self):
        # Which strain component to display (0–4)
        comp_idx = self.strain_selector.currentIndex()
        print(comp_idx)

        # Remove old strain meshes if any
        self.plotter.clear()
        self._draw_elements()  # redraw base geometry for context

        # Collect strain values
        for element in self.structure.elements:
            points = np.array([n.node_position for n in element.nodes])
            faces = np.hstack([[4, 0, 1, 2, 3]])

            strain_value = element.get_strain()[comp_idx]

            mesh = pv.PolyData(points, faces)
            mesh.cell_data["strain"] = [strain_value]  # assign strain as scalar
            self.plotter.add_mesh(mesh, scalars="strain", cmap="viridis", show_edges=True)

        self.plotter.add_scalar_bar("Strain")
        self.plotter.render()

    def _assemble_matrix(self):
        self.structure.assemble_global_stiffness_matrix()
        self.structure.assemble_forces_matrix()

    def _draw_elements(self):
        for element in self.structure.elements:
            # collect node coordinates
            points = np.array([n.node_position for n in element.nodes])

            if len(points) == 3:  # triangular shell
                faces = np.hstack([[3, 0, 1, 2]])
            elif len(points) == 4:  # quad shell
                faces = np.hstack([[4, 0, 1, 2, 3]])
            else:
                continue  # skip unsupported

            mesh = pv.PolyData(points, faces)
            self.plotter.add_mesh(mesh, color="lightgray", style="wireframe")  # or surface
        self.plotter.show_axes()

    def _update_force_mag(self, val):
        self.force_vector_magnitude = val
        # if forces are already drawn, refresh them
        if self.label_visibility["forces"]:
            self.toggle_labels("forces")  # remove
            self.toggle_labels("forces")  # re-draw with new scalin

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
                points = [np.mean([n.node_position for n in elem.nodes], axis=0) for elem in self.structure.elements]
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
                # remove old arrows and labels if present
                self.plotter.remove_actor("force_arrows")
                self.plotter.remove_actor("force_labels")

                force_points = []
                force_vectors = []
                force_magnitudes = []

                for n in self.structure.get_unique_nodes():
                    f = n.force.get_components()  # [Fx,Fy,Fz,Mx,My]
                    Fx, Fy, Fz, Mx, My = f
                    p = n.node_position

                    # --- Translational forces ---
                    vec = np.array([Fx, Fy, Fz])
                    if np.linalg.norm(vec) > 0:
                        force_points.append(p)
                        force_vectors.append(vec)
                        force_magnitudes.append(f"{np.linalg.norm(vec):.2f}")

                    # --- Moment about x (double-headed arrow) ---
                    if Mx != 0:
                        vec = np.array([self.force_vector_magnitude * np.sign(Mx) * 0.01, 0, 0])
                        arrow1 = pv.Arrow(start=p - vec, direction=vec)
                        arrow2 = pv.Arrow(start=p + vec, direction=vec)
                        self.plotter.add_mesh(arrow1, color="blue", name=f"moment_x_{n.id}_1")
                        self.plotter.add_mesh(arrow2, color="blue", name=f"moment_x_{n.id}_2")
                        self.plotter.add_point_labels([p], [f"Mx={Mx:.2f}"], text_color="blue",
                                                      name=f"moment_x_label_{n.id}", font_size=10)

                    # --- Moment about y (double-headed arrow) ---
                    if My != 0:
                        vec = np.array([0, self.force_vector_magnitude * np.sign(My) * 0.01, 0])
                        arrow1 = pv.Arrow(start=p - vec, direction=vec,)
                        arrow2 = pv.Arrow(start=p + vec, direction=vec)
                        self.plotter.add_mesh(arrow1, color="green", name=f"moment_y_{n.id}_1")
                        self.plotter.add_mesh(arrow2, color="green", name=f"moment_y_{n.id}_2")
                        self.plotter.add_point_labels([p], [f"My={My:.2f}"], text_color="green",
                                                      name=f"moment_y_label_{n.id}", font_size=10)

                # add translational arrows + tip labels
                if force_points:
                    self.plotter.add_arrows(np.array(force_points), np.array(force_vectors),
                                            mag=self.force_vector_magnitude * 0.01,
                                            name="force_arrows")
                    self.plotter.add_point_labels(np.array(force_points), force_magnitudes,
                                                  font_size=10, text_color="red",
                                                  name="force_labels")

        self.label_visibility[label_type] = not is_visible
        self.plotter.render()