"""
Damascus Layer - Single 3D Mesh Layer
======================================

Represents a single layer in the Damascus billet as a 3D triangular mesh.

DESIGN NOTES:
- Each layer is a thin rectangular solid (box mesh)
- Positioned in Z-axis (HORIZONTAL stacking on build plate)
- X-axis: width, Y-axis: length, Z-axis: height (layer stacking)
- Color represents steel type: light=high-nickel, dark=high-carbon

Usage:
    from lib.damascus_layer import DamascusLayer
    layer = DamascusLayer(z_position=0.0, thickness=1.0, color=(0.9, 0.9, 0.9))
"""

import open3d as o3d
import numpy as np
from typing import List, Tuple, Dict, Any

from lib.logging_config import logger


class DamascusLayer:
    """
    Represents a single layer in the Damascus billet as a 3D triangular mesh.

    DEBUGGING:
    ---------
    - All vertex operations are logged at DEBUG level
    - Mesh statistics (vertex count, bounds) are tracked
    - Deformation amounts are recorded for analysis
    """

    def __init__(self, z_position: float, thickness: float, color: Tuple[float, float, float],
                 width: float = 50.0, length: float = 100.0, layer_index: int = 0):
        """
        Create a Damascus layer as a 3D mesh.

        Args:
            z_position: Vertical position of this layer (mm)
            thickness: Thickness of the layer (mm)
            color: RGB color tuple (0-1 range) - (0.9,0.9,0.9) for white, (0.2,0.2,0.2) for black
            width: Width of the billet (mm)
            length: Length of the billet (mm)
            layer_index: Index of this layer in the stack (for debugging)
        """
        self.layer_index = layer_index
        self.z_position = z_position
        self.thickness = thickness
        self.color = color
        self.width = width
        self.length = length

        # Track original state for debugging
        self.original_z_position = z_position
        self.original_thickness = thickness

        # Deformation history for debugging
        self.deformation_history: List[Dict[str, Any]] = []

        logger.debug(f"Creating Layer #{layer_index}: z={z_position:.2f}mm, "
                     f"thickness={thickness:.2f}mm, color={'WHITE' if color[0] > 0.5 else 'BLACK'}")

        # Create the mesh as a rectangular box
        self.mesh = self._create_layer_mesh()

        logger.debug(f"Layer #{layer_index} mesh created: "
                     f"{len(self.mesh.vertices)} vertices, {len(self.mesh.triangles)} triangles")

    def _create_layer_mesh(self) -> o3d.geometry.TriangleMesh:
        """
        Create a 3D mesh representing this layer.

        TECHNICAL DETAILS:
        -----------------
        - Uses Open3D's create_box primitive
        - Box dimensions: width x length x thickness
        - HORIZONTAL ORIENTATION: Layers stack in Z-axis (height)
        - Centered at X=0, Y=0, positioned at z_position in Z
        - Normals computed for proper lighting in 3D view

        Returns:
            Open3D TriangleMesh object
        """
        logger.debug(f"Creating box mesh: {self.width}x{self.length}x{self.thickness} mm (W x L x H)")

        # Create a box mesh for the layer
        # IMPORTANT: width x length x thickness (horizontal orientation)
        mesh = o3d.geometry.TriangleMesh.create_box(
            width=self.width,
            height=self.length,
            depth=self.thickness
        )

        # Position: starts at origin (0,0,0) and extends in positive X, Y, Z directions
        # X: width (starts at 0)
        # Y: length (starts at 0)
        # Z: height (layers stack upward from z=0)
        translation = [0, 0, self.z_position]
        logger.debug(f"Translating mesh by: {translation}")
        mesh.translate(translation)

        # Apply color
        mesh.paint_uniform_color(self.color)

        # Compute normals for proper lighting
        mesh.compute_vertex_normals()

        return mesh

    def get_mesh(self) -> o3d.geometry.TriangleMesh:
        """Get the Open3D mesh for this layer."""
        return self.mesh

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about this layer for debugging.

        Returns:
            Dictionary containing layer metrics
        """
        vertices = np.asarray(self.mesh.vertices)

        return {
            'layer_index': self.layer_index,
            'vertex_count': len(vertices),
            'triangle_count': len(self.mesh.triangles),
            'bounds_x': (vertices[:, 0].min(), vertices[:, 0].max()),
            'bounds_y': (vertices[:, 1].min(), vertices[:, 1].max()),
            'bounds_z': (vertices[:, 2].min(), vertices[:, 2].max()),
            'center': vertices.mean(axis=0).tolist(),
            'color_type': 'WHITE' if self.color[0] > 0.5 else 'BLACK',
            'deformation_count': len(self.deformation_history)
        }
