"""
VisPy-based 3D Viewer for Damascus Pattern Simulator

This module provides OpenGL-accelerated 3D visualization using VisPy,
replacing matplotlib's 3D axes which have zoom limitations.

Key Features:
- Proper zoom behavior (maintains spatial relationships)
- Hardware-accelerated rendering
- Smooth camera controls (rotate, pan, zoom)
- Embeddable in Tkinter GUI

Author: Damascus Pattern Simulator Team
Date: 2026-02-05
"""

import numpy as np
import os

# Set PyOpenGL platform to use GLX on Linux (not EGL)
if 'Linux' in os.uname().sysname:
    os.environ['PYOPENGL_PLATFORM'] = 'glx'

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
        self.view.camera = 'turntable'  # Turntable camera for intuitive 3D navigation
        
        # Camera settings
        self.view.camera.fov = 45  # Field of view
        self.view.camera.distance = 200  # Initial camera distance
        
        # Storage for mesh visuals
        self.layer_meshes = []
        self.build_plate_visual = None
        
        # Scene bounds for camera auto-fit
        self.scene_bounds = None
        
        logger.debug("VisPy viewer initialized with turntable camera")
    
    def clear_scene(self):
        """Clear all existing mesh visuals from the scene."""
        logger.debug("Clearing scene")
        
        # Remove all layer meshes
        for mesh_visual in self.layer_meshes:
            mesh_visual.parent = None
        self.layer_meshes.clear()
        
        # Remove build plate
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
        
        # Clear existing scene
        self.clear_scene()
        
        # Render each layer
        for layer_idx, layer in enumerate(billet.layers):
            self._render_layer(layer, layer_idx)
        
        # Draw build plate boundary
        self._draw_build_plate(build_plate_width, build_plate_length)
        
        # Calculate scene bounds and fit camera
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
        # Get mesh data from Open3D
        vertices = np.asarray(layer.mesh.vertices)
        triangles = np.asarray(layer.mesh.triangles)
        
        # Convert color from hex string to RGB array (0-1 range)
        color = self._hex_to_rgb(layer.color)
        
        # Create VisPy mesh visual
        mesh_visual = visuals.Mesh(
            vertices=vertices,
            faces=triangles,
            color=color,
            shading='smooth'
        )
        
        # Add to viewbox
        mesh_visual.parent = self.view.scene
        
        # Store reference
        self.layer_meshes.append(mesh_visual)
        
        if layer_idx == 0 or layer_idx % 10 == 0:
            logger.debug(f"  Layer {layer_idx}: {len(vertices)} vertices, {len(triangles)} faces")
    
    def _draw_build_plate(self, width, length):
        """
        Draw build plate boundary as a rectangle at Z=0.
        
        Parameters:
        -----------
        width : float
            Build plate width in mm
        length : float
            Build plate length in mm
        """
        # Define rectangle corners at Z=0
        corners = np.array([
            [-width/2, -length/2, 0],
            [ width/2, -length/2, 0],
            [ width/2,  length/2, 0],
            [-width/2,  length/2, 0],
            [-width/2, -length/2, 0]  # Close the loop
        ], dtype=np.float32)
        
        # Create line visual
        self.build_plate_visual = visuals.Line(
            pos=corners,
            color=(0.5, 0.5, 0.5, 0.6),  # Gray with transparency
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
            Width of build plate
        build_plate_length : float
            Length of build plate
        """
        # Get billet dimensions
        billet_width = billet.width
        billet_length = billet.length
        billet_height = sum(l.thickness for l in billet.layers)
        
        # Use maximum of billet and build plate for bounds
        max_width = max(billet_width, build_plate_width)
        max_length = max(billet_length, build_plate_length)
        max_height = billet_height * 1.5  # Add some padding above
        
        # Store bounds as (center, size)
        self.scene_bounds = {
            'center': np.array([0, 0, max_height/2]),
            'size': np.array([max_width, max_length, max_height])
        }
        
        logger.debug(f"Scene bounds: center={self.scene_bounds['center']}, size={self.scene_bounds['size']}")
    
    def _fit_camera_to_scene(self):
        """Adjust camera to fit the entire scene in view."""
        if self.scene_bounds is None:
            return
        
        # Calculate appropriate camera distance
        max_dim = np.max(self.scene_bounds['size'])
        distance = max_dim * 2.0  # 2x the max dimension for good view
        
        # Set camera parameters
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
        # Convert to turntable camera parameters
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
        # If already a tuple/list, return as-is (assume it's already in correct format)
        if isinstance(hex_color, (tuple, list)):
            # Ensure it has 4 components (RGBA)
            if len(hex_color) == 3:
                return (*hex_color, 1.0)
            return tuple(hex_color)
        
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB (0-255)
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Convert to 0-1 range
        return (r/255.0, g/255.0, b/255.0, 1.0)


# Test function
if __name__ == '__main__':
    """Test the VisPy viewer with a simple cube."""
    import sys
    from vispy import app
    
    # Create test viewer
    viewer = DamascusVispyViewer()
    
    # Create a simple test cube
    vertices = np.array([
        [-10, -10, 0],
        [ 10, -10, 0],
        [ 10,  10, 0],
        [-10,  10, 0],
        [-10, -10, 20],
        [ 10, -10, 20],
        [ 10,  10, 20],
        [-10,  10, 20],
    ], dtype=np.float32)
    
    faces = np.array([
        [0, 1, 2], [0, 2, 3],  # Bottom
        [4, 5, 6], [4, 6, 7],  # Top
        [0, 1, 5], [0, 5, 4],  # Front
        [2, 3, 7], [2, 7, 6],  # Back
        [0, 3, 7], [0, 7, 4],  # Left
        [1, 2, 6], [1, 6, 5],  # Right
    ], dtype=np.uint32)
    
    # Create test mesh
    test_mesh = visuals.Mesh(
        vertices=vertices,
        faces=faces,
        color=(1.0, 0.5, 0.0, 1.0),  # Orange
        shading='smooth'
    )
    test_mesh.parent = viewer.view.scene
    
    # Draw build plate
    viewer._draw_build_plate(100, 100)
    
    # Set camera
    viewer.view.camera.center = (0, 0, 10)
    viewer.view.camera.distance = 80
    
    print("Test viewer created. Use mouse to interact:")
    print("  - Left drag: Rotate")
    print("  - Right drag: Pan")
    print("  - Mouse wheel: Zoom")
    print("  - Press Escape to exit")
    
    # Run VisPy app
    if sys.flags.interactive != 1:
        app.run()
