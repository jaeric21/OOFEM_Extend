import pyvista as pv
mesh = pv.Arrow()
import numpy as np
import pyvista as pv

# arc parameters
r = 1.0
theta = np.linspace(np.deg2rad(30), np.deg2rad(330), 100)
pts = np.c_[r*np.cos(theta), r*np.sin(theta), np.zeros_like(theta)]

# shaft as tube
spline = pv.Spline(pts, 200).tube(radius=0.03)

# tangents at ends (for arrow directions)
t0 = pts[1] - pts[0]
t1 = pts[-1] - pts[-2]
t0 /= np.linalg.norm(t0)
t1 /= np.linalg.norm(t1)

# two arrowheads (using pv.Arrow)
arrow0 = pv.Arrow(start=pts[0], direction=-t0, tip_length=0.3, tip_radius=0.08, shaft_radius=0.0)
arrow1 = pv.Arrow(start=pts[-1], direction=-t1, tip_length=0.3, tip_radius=0.08, shaft_radius=0.0)

# plot
p = pv.Plotter()
p.add_mesh(spline, color="darkorange")
p.add_mesh(arrow0, color="darkorange")
p.add_mesh(arrow1, color="darkorange")
p.show(cpos="xy")
mesh.plot(show_edges=True)