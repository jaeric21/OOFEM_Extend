# Class for shell elements

import forces
import node
import material
import constraints

import numpy as np
from itertools import count

class Element:
    _element_ids = count(0)
    def __init__(self, n1:node.Node, n2:node.Node, n3:node.Node, n4:node.Node, ref:np.ndarray):
        self._T = np.zeros((20,20))
        self.stiffness_matrix_global = None
        self.stiffness_matrix_local = None
        self.id = next(self._element_ids)
        self.reference_system = ref
        self.node1 = n1
        self.node2 = n2
        self.node3 = n3
        self.node4 = n4
        self.nodes = [self.node1, self.node2, self.node3, self.node4]

        self._dofNumbers = [0] * 20
        self._eps = None
        self._e1 = None
        self._e2 = None
        self._e3 = None
        self._Bm = None
        self._Bm_T = None
        self._Bb = None
        self._Bb_T = None
        self._Bc = None
        self._Bc_T = None
        self._compute_T()
        self.compute_stiffness_matrix()

    @staticmethod
    def _shape_function(xi, eta):
        N1 = 0.25 * (1 - xi) * (1 - eta)
        N2 = 0.25 * (1 + xi) * (1 - eta)
        N3 = 0.25 * (1 + xi) * (1 + eta)
        N4 = 0.25 * (1 - xi) * (1 + eta)
        N = np.array([N1, N2, N3, N4])

        dN_dxi = np.array([
            -0.25 * (1 - eta),
            0.25 * (1 - eta),
            0.25 * (1 + eta),
            -0.25 * (1 + eta),
        ])

        dN_deta = np.array([
            -0.25 * (1 - xi),
            -0.25 * (1 + xi),
            0.25 * (1 + xi),
            0.25 * (1 - xi),
        ])
        return N, dN_dxi, dN_deta

    def compute_stiffness_matrix(self):

        A = np.array([
            [103239, 7287.45, 0],
            [7287.45, 103239, 0],
            [0, 0, 6000]])

        B = np.zeros_like(A)

        D = np.array([
            [15941.3, 874.494, 0],
            [874.494, 8836.03, 0],
            [0, 0, 720]])

        ABD_Matrix = np.block([[A, B],
                               [B, D]])

        Kloc = np.zeros((20, 20))

        # 2x2 Gauss-Punkte
        gp = 1.0 / np.sqrt(3.0)
        gauss = [(-gp, -gp), (gp, -gp), (gp, gp), (-gp, gp)]
        weights = [1.0, 1.0, 1.0, 1.0]

        p_global = [n.node_position for n in self.nodes]
        nodes_local = []
        for p in p_global:
            v = p - p_global[0]  # Ursprung in node1
            nodes_local.append((np.dot(v, self._e1), np.dot(v, self._e2)))
        nodes_local = np.array(nodes_local)

        for (xi, eta), w in zip(gauss, weights):
            N, dN_dxi, dN_deta = self._shape_function(xi, eta)

            J = np.zeros((2, 2))
            for i in range(4):
                xi_loc, yi_loc = nodes_local[i]
                J[0, 0] += dN_dxi[i] * xi_loc
                J[0, 1] += dN_dxi[i] * yi_loc
                J[1, 0] += dN_deta[i] * xi_loc
                J[1, 1] += dN_deta[i] * yi_loc

            detJ = np.linalg.det(J)
            if detJ <= 0:
                raise ValueError("Nicht-positive Jacobi-Determinante (inverted element?). detJ=%g" % detJ)
            invJ = np.linalg.inv(J)

            dN_dx = np.zeros(4)
            dN_dy = np.zeros(4)
            for i in range(4):
                grad_nat = np.array([dN_dxi[i], dN_deta[i]])
                grad_xy = invJ @ grad_nat
                dN_dx[i] = grad_xy[0]
                dN_dy[i] = grad_xy[1]

            # --- Bm (3x20) und Bb (3x20) aufbauen ---
            Bm = np.zeros((3, 20))  # [eps_xx, eps_yy, gamma_xy]
            Bb = np.zeros((3, 20))  # [kappa_xx, kappa_yy, kappa_xy]

            for i in range(4):
                c = i * 5
                Bm[0, c + 0] = dN_dx[i]  # eps_xx <- du/dx
                Bm[1, c + 1] = dN_dy[i]  # eps_yy <- dv/dy
                Bm[2, c + 0] = dN_dy[i]  # gamma_xy <- du/dy
                Bm[2, c + 1] = dN_dx[i]  # gamma_xy <- dv/dx
                Bb[0, c + 3] = dN_dx[i]  # kappa_xx aus theta_x
                Bb[1, c + 4] = dN_dy[i]  # kappa_yy aus theta_y
                Bb[2, c + 3] = dN_dy[i]  # part kappa_xy aus theta_x
                Bb[2, c + 4] = dN_dx[i]  # part kappa_xy aus theta_y

            self._Bc = np.vstack([Bm, Bb])  # (6,20)
            self._Bc_T = self._Bc.T
            Kloc += (self._Bc_T @ ABD_Matrix @ self._Bc) * detJ * w

        # Projektion des reference koordinaten systems
        e0_proj = self.reference_system - np.dot(self.reference_system, self._e3) * self._e3
        e0_proj /= np.linalg.norm(e0_proj)

        x_mat_local = e0_proj
        y_mat_local = np.cross(self._e3, x_mat_local)

        # Erstellen des Rotations koordinaten sytems
        Tmat = np.zeros((20, 20))
        for i in range(4):
            R = np.eye(5)
            R[:2, :2] = np.column_stack((x_mat_local[:2], y_mat_local[:2]))
            Tmat[i * 5:i * 5 + 5, i * 5:i * 5 + 5] = R

        # Rotieren des Lokalen systems in das Matrerial koordinaten systems
        Kloc_rotated = Tmat.T @ Kloc @ Tmat

        self.stiffness_matrix_local = Kloc_rotated
        self.stiffness_matrix_global = self._T.T @ self.stiffness_matrix_local @ self._T

    def compute_strain(self):

        # compute b matricies
        gp = 1.0 / np.sqrt(3.0)
        gauss = [(-gp, -gp), (gp, -gp), (gp, gp), (-gp, gp)]
        weights = [1.0, 1.0, 1.0, 1.0]

        p_global = [n.node_position for n in self.nodes]
        nodes_local = []
        for p in p_global:
            v = p - p_global[0]  # Ursprung in node1
            nodes_local.append((np.dot(v, self._e1), np.dot(v, self._e2)))
        nodes_local = np.array(nodes_local)

        for (xi, eta), w in zip(gauss, weights):
            N, dN_dxi, dN_deta = self._shape_function(xi, eta)

            J = np.zeros((2, 2))
            for i in range(4):
                xi_loc, yi_loc = nodes_local[i]
                J[0, 0] += dN_dxi[i] * xi_loc
                J[0, 1] += dN_dxi[i] * yi_loc
                J[1, 0] += dN_deta[i] * xi_loc
                J[1, 1] += dN_deta[i] * yi_loc

            detJ = np.linalg.det(J)
            if detJ <= 0:
                raise ValueError("Nicht-positive Jacobi-Determinante (inverted element?). detJ=%g" % detJ)
            invJ = np.linalg.inv(J)

            dN_dx = np.zeros(4)
            dN_dy = np.zeros(4)
            for i in range(4):
                grad_nat = np.array([dN_dxi[i], dN_deta[i]])
                grad_xy = invJ @ grad_nat
                dN_dx[i] = grad_xy[0]
                dN_dy[i] = grad_xy[1]

            # --- Bm (3x20) und Bb (3x20) aufbauen ---
            Bm = np.zeros((3, 20))  # [eps_xx, eps_yy, gamma_xy]
            Bb = np.zeros((3, 20))  # [kappa_xx, kappa_yy, kappa_xy]

            for i in range(4):
                c = i * 5
                Bm[0, c + 0] = dN_dx[i]  # eps_xx <- du/dx
                Bm[1, c + 1] = dN_dy[i]  # eps_yy <- dv/dy
                Bm[2, c + 0] = dN_dy[i]  # gamma_xy <- du/dy
                Bm[2, c + 1] = dN_dx[i]  # gamma_xy <- dv/dx
                Bb[0, c + 3] = dN_dx[i]  # kappa_xx aus theta_x
                Bb[1, c + 4] = dN_dy[i]  # kappa_yy aus theta_y
                Bb[2, c + 3] = dN_dy[i]  # part kappa_xy aus theta_x
                Bb[2, c + 4] = dN_dx[i]

        u_elem_global = np.stack((self.node1.get_displacement(), self.node2.get_displacement(),
                                  self.node3.get_displacement(), self.node4.get_displacement()))
        u_local = self._T @ u_elem_global

        u_mat = self.Tmat.T @ u_elem_global
        eps_mat = Bc @ u_mat


    def calc_Bs(self):


    def enumerate_dofs(self) -> None:
        self._dofNumbers = np.hstack((
            self.node1.getDOFNumbers(),
            self.node2.getDOFNumbers(),
            self.node3.getDOFNumbers(),
            self.node4.getDOFNumbers()
        ))

    def get_dof_numbers(self):
        return self._dofNumbers

    def compute_eps(self) -> None:
        pass

    def compute_sigma(self) -> None:
        pass

    def get_sigma(self) -> float:
        self.compute_sigma()
        return self._sigma

    def print(self) -> None:
        pass

    def _compute_T(self) -> None:
        p1, p2, p3 = [n.node_position for n in (self.node1, self.node2, self.node3,)]
        e_1 = (p2 - p1) / np.linalg.norm(p2 - p1)
        e_2 = (p3 - p1) - np.dot((p3 - p1), e_1) * e_1
        e_2 = e_2 / np.linalg.norm(e_2)
        e_3 = np.cross(e_1, e_2)

        R = np.array([e_1, e_2, e_3]) # Rotationsmatrix

        for i in range(4):
            self._T[i * 5:i * 5 + 3, i * 5:i * 5 + 3] = R
            self._T[i * 5 + 3:i * 5 + 5, i * 5 + 3:i * 5 + 5] = R[:2, :2]

        self._e1 = e_1
        self._e2 = e_2
        self._e3 = e_3


if __name__ == "__main__":
    n1 = node.Node(0, 0, 1)
    n2 = node.Node(1, 0, 1)
    n3 = node.Node(1, 1, 0.3)
    n4 = node.Node(0, 1, 0.3)
    e1 = Shell(n1, n2, n3, n4, np.array([1.0, 0.0, 0.0]))
    print(e1.stiffness_matrix_local.shape)