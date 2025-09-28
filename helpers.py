import numpy as np

def transform_stress_to_global(alpha):
    rotation_matrix = np.array([
        [np.cos(alpha)**2, np.sin(alpha)**2, -np.sin(2*alpha)],
        [np.sin(alpha)**2, np.cos(alpha)**2, np.sin(2*alpha)],
        [0.5*np.sin(2*alpha), -0.5*np.sin(2*alpha), np.cos(2*alpha)]
    ])
    return rotation_matrix


def transform_strains_to_global(alpha):
    rotation_matrix = np.array([
        [np.cos(alpha)**2, np.sin(alpha)**2, -0.5*np.sin(2*alpha)],
        [np.sin(alpha)**2, np.cos(alpha)**2, 0.5*np.sin(2*alpha)],
        [np.sin(2*alpha), -np.sin(2*alpha), np.cos(2*alpha)]
    ])
    return rotation_matrix


def transform_strains_to_local(alpha):
    rotation_matrix = np.array([
        [np.cos(alpha)**2, np.sin(alpha)**2, 0.5*np.sin(2*alpha)],
        [np.sin(alpha)**2, np.cos(alpha)**2, -0.5*np.sin(2*alpha)],
        [-np.sin(2*alpha), np.sin(2*alpha), np.cos(2*alpha)]
    ])
    return rotation_matrix




