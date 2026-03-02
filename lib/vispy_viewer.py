"""
VisPy-based 3D Viewer for Damascus Pattern Simulator
=====================================================

!! ELECTRON MIGRATION NOTE !!
This module was the legacy 3D viewer using VisPy (OpenGL) embedded in Tkinter.
The Electron UI replaces it with Three.js WebGL rendering in Viewport3D.tsx.
This module is preserved for reference — the render_billet() mesh traversal
and build plate drawing logic may be useful if VisPy is ever needed again
(e.g. for headless server-side rendering or off-screen snapshot generation).

OpenGL-accelerated 3D visualization using VisPy, replacing matplotlib's
3D axes which have zoom limitations.

Key Features:
- Proper zoom behavior (maintains spatial relationships)
- Hardware-accelerated rendering
- Smooth camera controls (rotate, pan, zoom)
- Embeddable in Tkinter GUI

Usage:
    from lib.vispy_viewer import DamascusVispyViewer
    viewer = DamascusVispyViewer(parent=some_tk_frame)
    viewer.render_billet(billet)
"""

import numpy as np
import os
import platform

# Configure PyOpenGL platform per OS before importing VisPy/OpenGL.
# Use setdefault so user-provided env vars still win.
os_name = platform.system()
if os_name == 'Linux':
    os.environ.setdefault('PYOPENGL_PLATFORM', 'glx')
elif os_name == 'Windows':
    os.environ.setdefault('PYOPENGL_PLATFORM', 'win32')

# Configure VisPy to use Tkinter backend
import vispy
vispy.use(app='tkinter', gl='gl+')

from vispy import scene
from vispy.scene import visuals
import logging

logger = logging.getLogger(__name__)


class DamascusVispyViewer:
    """
    VisPy-based 3D viewer for Damascus billet visualization.

    This class handles rendering of layered Damascus steel billets with
    proper zoom and camera controls.
    """

    def __init__(self, parent=None):
        """
        Initialize the VisPy 3D viewer.

        Parameters:
        -----------
        parent : tk.Widget, optional
            Parent Tkinter widget to embed the canvas in
        """
        logger.info("Initializing Damascus VisPy 3D Viewer")

        # Create VisPy canvas with scene
        self.canvas = scene.SceneCanvas(
            keys='interactive',
            show=True,
            bgcolor='#2d2d2d',
            parent=parent
        )

        # Create a viewbox with camera
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'turntable'

        # Camera settings
        self.view.camera.fov = 45
        self.view.camera.distance = 200

        # Storage for mesh visuals
        self.layer_meshes = []
        self.build_plate_visual = None

        # Scene bounds for camera auto-fit
        self.scene_bounds = None

        logger.debug("VisPy viewer initialized with turntable camera")

    def clear_scene(self):
        """Clear all existing mesh visuals from the scene."""
        logger.debug("Clearing scene")

        for mesh_visual in self.layer_meshes:
            mesh_visual.parent = None
        self.layer_meshes.clear()

        if self.build_plate_visual is not None:
            self.build_plate_visual.parent = None
            self.build_plate_visual = None

    def render_billet(self, billet, build_plate_width=500, build_plate_length=500):
        """
        Render a Damascus billet with all its layers.

        Parameters:
        -----------
        billet : Damascus3DBillet
            The billet object containing layers with meshes
        build_plate_width : float
            Width of the build plate in mm
        build_plate_length : float
            Length of the build plate in mm
        """
        logger.info(f"Rendering billet: {len(billet.layers)} layers")

        self.clear_scene()

        for layer_idx, layer in enumerate(billet.layers):
            self._render_layer(layer, layer_idx)

        self._draw_build_plate(build_plate_width, build_plate_length)
        self._calculate_scene_bounds(billet, build_plate_width, build_plate_length)
        self._fit_camera_to_scene()

        logger.info(f"Rendered {len(self.layer_meshes)} layer meshes")

    def _render_layer(self, layer, layer_idx):
        """
        Render a single layer as a mesh visual.

        Parameters:
        -----------
        layer : DamascusLayer
            Layer object with mesh and color
        layer_idx : int
            Index of the layer for debugging
        """
        vertices = np.asarray(layer.mesh.vertices)
        triangles = np.asarray(layer.mesh.triangles)

        color = self._hex_to_rgb(layer.color)

        mesh_visual = visuals.Mesh(
            vertices=vertices,
            faces=triangles,
            color=color,
            shading='smooth'
        )

        mesh_visual.parent = self.view.scene
        self.layer_meshes.append(mesh_visual)

        if layer_idx == 0 or layer_idx % 10 == 0:
            logger.debug(f"  Layer {layer_idx}: {len(vertices)} vertices, {len(triangles)} faces")

    def _draw_build_plate(self, width, length):
        """
        Draw build plate boundary as a rectangle at Z=0.

        Parameters:
        -----------
        width : float
            Build plate width in mm (X-axis)
        length : float
            Build plate length in mm (Y-axis)
        """
        corners = np.array([
            [0, 0, 0],
            [width, 0, 0],
            [width, length, 0],
            [0, length, 0],
            [0, 0, 0]
        ], dtype=np.float32)

        self.build_plate_visual = visuals.Line(
            pos=corners,
            color=(0.5, 0.5, 0.5, 0.6),
            width=2,
            method='gl'
        )

        self.build_plate_visual.parent = self.view.scene
        logger.debug(f"Drew build plate: {width}x{length}mm")

    def _calculate_scene_bounds(self, billet, build_plate_width, build_plate_length):
        """
        Calculate the bounding box of the entire scene.

        Parameters:
        -----------
        billet : Damascus3DBillet
            The billet to calculate bounds for
        build_plate_width : float
            Width of build plate (X-axis)
        build_plate_length : float
            Length of build plate (Y-axis)
        """
        billet_width = billet.width
        billet_length = billet.length
        billet_height = sum(l.thickness for l in billet.layers)

        max_width = max(billet_width, build_plate_width)
        max_length = max(billet_length, build_plate_length)
        max_height = billet_height * 1.5

        self.scene_bounds = {
            'center': np.array([max_width / 2, max_length / 2, max_height / 2]),
            'size': np.array([max_width, max_length, max_height])
        }

        logger.debug(f"Scene bounds: center={self.scene_bounds['center']}, size={self.scene_bounds['size']}")

    def _fit_camera_to_scene(self):
        """Adjust camera to fit the entire scene in view."""
        if self.scene_bounds is None:
            return

        max_dim = np.max(self.scene_bounds['size'])
        distance = max_dim * 2.0

        self.view.camera.center = self.scene_bounds['center']
        self.view.camera.distance = distance

        logger.debug(f"Camera fitted: center={self.scene_bounds['center']}, distance={distance:.1f}")

    def set_view_angles(self, elevation, azimuth):
        """
        Set camera view angles.

        Parameters:
        -----------
        elevation : float
            Elevation angle in degrees
        azimuth : float
            Azimuth angle in degrees
        """
        self.view.camera.elevation = elevation
        self.view.camera.azimuth = azimuth
        logger.debug(f"View angles set: elevation={elevation}°, azimuth={azimuth}°")

    def reset_camera(self):
        """Reset camera to default isometric view."""
        self.set_view_angles(elevation=30, azimuth=45)
        if self.scene_bounds is not None:
            self._fit_camera_to_scene()
        logger.info("Camera reset to default view")

    def get_native_widget(self):
        """
        Get the native widget for embedding in Tkinter.

        Returns:
        --------
        widget : native widget
            The native widget that can be embedded in Tkinter
        """
        return self.canvas.native

    @staticmethod
    def _hex_to_rgb(hex_color):
        """
        Convert hex color to RGB tuple (0-1 range).

        Parameters:
        -----------
        hex_color : str or tuple
            Hex color string (e.g., '#FFFFFF') or RGB tuple

        Returns:
        --------
        rgb : tuple
            RGB values in 0-1 range
        """
        if isinstance(hex_color, (tuple, list)):
            if len(hex_color) == 3:
                return (*hex_color, 1.0)
            return tuple(hex_color)

        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        return (r / 255.0, g / 255.0, b / 255.0, 1.0)
