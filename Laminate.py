from typing import List, Dict, Optional
import numpy as np
import Plies


class Laminate:
    def __init__(self, entries: List[Plies.Ply]):
        # mandatory parameters
        self.entries = entries
        self.Aij = np.zeros((3, 3))
        self.Bij = np.zeros((3, 3))
        self.Dij = np.zeros((3, 3))
        self.update_laminate_properties()
        self.ABDij = np.zeros((6, 6))

    @classmethod
    def from_ply_list(cls, entry_list: List[Plies.Ply]):
        return cls(entries=entry_list)

    @classmethod
    def from_ply_dict(cls, ply_dict: Dict[str, Dict]):
        entries = [Plies.Ply(**ply_info) for ply_info in ply_dict.values()]
        return cls(entries=entries)

    def add_ply(self, ply: Plies.Ply):
        self.entries.append(ply)
        self.update_laminate_properties()

    def remove_ply(self, index: int):
        if 0 <= index < len(self.entries):
            del self.entries[index]
            self.update_laminate_properties()
        else:
            raise ValueError("Invalid index")

    def calc_ABD_matrices(self):
        # total laminate thickness
        total_thickness = sum(ply.thickness for ply in self.entries)
        self.thickness = total_thickness

        # mid-plane reference
        z_bot = -total_thickness / 2.0
        z_coords = [z_bot]

        # build z-coordinates (top and bottom of each ply)
        for ply in self.entries:
            z_coords.append(z_coords[-1] + ply.thickness)

        # reset matrices
        A = np.zeros((3, 3))
        B = np.zeros((3, 3))
        D = np.zeros((3, 3))

        # loop through plies
        for k, ply in enumerate(self.entries):
            ply.calc_global_stiffens_matrix()  # ensure Qbar is updated
            Qbar = ply.global_stiffness_matrix

            z_km1 = z_coords[k]
            z_k = z_coords[k + 1]

            A += Qbar * (z_k - z_km1)
            B += 0.5 * Qbar * (z_k ** 2 - z_km1 ** 2)
            D += (1 / 3) * Qbar * (z_k ** 3 - z_km1 ** 3)

        self.Aij = A
        self.Bij = B
        self.Dij = D

        # assemble ABD matrix
        self.ABDij = np.block([
            [A, B],
            [B, D]
        ])

    def update_laminate_properties(self):
        self.calc_ABD_matrices()

    def print_layup(self):
        print("Ply Number | Material | Thickness | Angle")
        print("-----------------------------------------")
        for i, ply in enumerate(self.entries):
            print(f"{i + 1} | {ply.material.name} | {ply.thickness*1000} | {np.degrees(ply.rotation_angle)}")
        print("-----------------------------------------")