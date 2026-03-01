"""
VisPy-based 3D Viewer for Damascus Pattern Simulator

Backward-compatible re-export wrapper.
The implementation has moved to lib/vispy_viewer.py.

Usage (unchanged):
    from vispy_3d_viewer import DamascusVispyViewer
"""

from lib.vispy_viewer import DamascusVispyViewer  # noqa: F401


if __name__ == '__main__':
    """Test the VisPy viewer with a simple cube."""
    import numpy as np
    from vispy import app
    from vispy.scene import visuals
    import sys

    viewer = DamascusVispyViewer()

    vertices = np.array([
        [-10, -10, 0], [10, -10, 0], [10, 10, 0], [-10, 10, 0],
        [-10, -10, 20], [10, -10, 20], [10, 10, 20], [-10, 10, 20],
    ], dtype=np.float32)
    faces = np.array([
        [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
        [0, 3, 7], [0, 7, 4], [1, 2, 6], [1, 6, 5],
    ], dtype=np.uint32)

    test_mesh = visuals.Mesh(vertices=vertices, faces=faces,
                             color=(1.0, 0.5, 0.0, 1.0), shading='smooth')
    test_mesh.parent = viewer.view.scene
    viewer._draw_build_plate(100, 100)
    viewer.view.camera.center = (0, 0, 10)
    viewer.view.camera.distance = 80

    print("Test viewer created. Left drag=Rotate, Right drag=Pan, Wheel=Zoom")
    if sys.flags.interactive != 1:
        app.run()
