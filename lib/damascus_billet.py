"""
Damascus 3D Billet - Full Simulation Engine
============================================

Represents a complete Damascus billet with multiple 3D layers and provides
all deformation operations (wedge, twist, compression, drilling),
cross-section extraction, visualization, and export.

Usage:
    from lib.damascus_billet import Damascus3DBillet
    billet = Damascus3DBillet(width=50.0, length=100.0)
    billet.create_simple_layers(num_layers=30)
    billet.apply_wedge_deformation(wedge_depth=18.0)
"""

import open3d as o3d
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import json
from datetime import datetime
from PIL import Image

from lib.logging_config import logger
from lib.damascus_layer import DamascusLayer
from lib.api_instrumentation import install_api_call_logging
from lib.forging_wedge import apply_wedge_deformation as _apply_wedge
from lib.forging_twist import apply_twist as _apply_twist
from lib.forging_compression import apply_compression as _apply_compression
from lib.forging_drill import drill_hole as _drill_hole


class Damascus3DBillet:
    """
    Represents a complete Damascus billet with multiple 3D layers.

    CORE FUNCTIONALITY:
    ------------------
    - Layer management (add, stack, query)
    - Deformation operations (wedge, twist, compression, drilling)
    - Visualization (3D interactive, cross-sections)
    - Export (3D models, 2D patterns)

    DEBUGGING FEATURES:
    ------------------
    - Operation history tracking
    - Per-operation statistics
    - Vertex displacement logging
    - Performance timing
    - State snapshots before/after operations
    """

    def __init__(self, width: float = 50.0, length: float = 100.0):
        """
        Create a Damascus billet.

        Args:
            width: Width of billet in mm
            length: Length of billet in mm
        """
        self.width = width
        self.length = length
        self.layers: List[DamascusLayer] = []

        # Operation history for debugging and undo functionality
        self.operation_history: List[Dict[str, Any]] = []

        logger.info(f"Created new Damascus3DBillet: {width}mm x {length}mm")
        logger.debug(f"Billet initialized with width={width}, length={length}")

    def add_layer(self, thickness: float, is_white: bool):
        """
        Add a layer to the billet.

        Args:
            thickness: Thickness of layer in mm
            is_white: True for high-nickel (white) steel, False for high-carbon (black)
        """
        # Calculate z position based on existing layers
        z_pos = sum(layer.thickness for layer in self.layers)
        layer_index = len(self.layers)

        # White steel: light gray (0.9), Black steel: dark gray (0.2)
        color = (0.9, 0.9, 0.9) if is_white else (0.2, 0.2, 0.2)

        logger.debug(f"Adding layer #{layer_index}: {'WHITE' if is_white else 'BLACK'}, "
                     f"thickness={thickness}mm, z_pos={z_pos}mm")

        layer = DamascusLayer(z_pos, thickness, color, self.width, self.length, layer_index)
        self.layers.append(layer)

    def create_simple_layers(self, num_layers: int = 20, white_thickness: float = 1.0,
                             black_thickness: float = 1.0):
        """
        Create simple alternating layers.

        Args:
            num_layers: Total number of layers
            white_thickness: Thickness of white layers in mm
            black_thickness: Thickness of black layers in mm
        """
        logger.info(f"Creating {num_layers} alternating layers...")
        logger.debug(f"Layer parameters: white={white_thickness}mm, black={black_thickness}mm")

        self.layers = []
        for i in range(num_layers):
            is_white = (i % 2 == 0)
            thickness = white_thickness if is_white else black_thickness
            self.add_layer(thickness, is_white)

        total_height = sum(l.thickness for l in self.layers)
        logger.info(f"Layer creation complete: {num_layers} layers, total height: {total_height:.1f}mm")
        logger.debug(f"White layers: {sum(1 for l in self.layers if l.color[0] > 0.5)}")
        logger.debug(f"Black layers: {sum(1 for l in self.layers if l.color[0] < 0.5)}")

        print(f"Created {num_layers} layers, total height: {total_height:.1f}mm")

    def get_all_meshes(self) -> List[o3d.geometry.TriangleMesh]:
        """Get all layer meshes for visualization."""
        return [layer.get_mesh() for layer in self.layers]

    def get_billet_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the entire billet.

        Returns:
            Dictionary with billet statistics
        """
        stats = {
            'timestamp': datetime.now().isoformat(),
            'layer_count': len(self.layers),
            'total_height_mm': sum(l.thickness for l in self.layers),
            'width_mm': self.width,
            'length_mm': self.length,
            'total_vertices': sum(len(l.mesh.vertices) for l in self.layers),
            'total_triangles': sum(len(l.mesh.triangles) for l in self.layers),
            'operation_count': len(self.operation_history),
            'layers': [layer.get_stats() for layer in self.layers]
        }

        logger.debug(f"Billet stats: {json.dumps(stats, indent=2)}")
        return stats

    # ========================================================================
    # FORGING OPERATIONS (delegated to lib/forging_*.py modules)
    # ========================================================================

    def apply_wedge_deformation(self, wedge_depth: float = 20.0, wedge_angle: float = 30.0,
                                split_gap: float = 5.0, debug: bool = True):
        """Apply wedge deformation to simulate feather Damascus. See lib/forging_wedge.py."""
        _apply_wedge(self, wedge_depth=wedge_depth, wedge_angle=wedge_angle,
                     split_gap=split_gap, debug=debug)

    def apply_twist(self, angle_degrees: float = 90.0, axis: str = 'z', debug: bool = True):
        """Apply torsional twist to the billet. See lib/forging_twist.py."""
        _apply_twist(self, angle_degrees=angle_degrees, axis=axis, debug=debug)

    def apply_compression(self, compression_factor: float = 0.8, debug: bool = True):
        """Compress the billet vertically. See lib/forging_compression.py."""
        _apply_compression(self, compression_factor=compression_factor, debug=debug)

    def drill_hole(self, x_pos: float = 0.0, z_pos: float = 0.0, radius: float = 10.0, debug: bool = True):
        """Drill a hole through the billet. See lib/forging_drill.py."""
        _drill_hole(self, x_pos=x_pos, z_pos=z_pos, radius=radius, debug=debug)

    # ========================================================================
    # CROSS-SECTION EXTRACTION
    # ========================================================================

    def extract_cross_section(self, z_slice: float = 0.0, resolution: int = 500, debug: bool = True) -> np.ndarray:
        """
        Extract a 2D cross-section at a specific Z position.

        Args:
            z_slice: Z position to slice at (mm)
            resolution: Resolution of output image (pixels per side)
            debug: Enable detailed debug logging

        Returns:
            2D numpy array representing the pattern (0-255 grayscale)
        """
        logger.info("=" * 70)
        logger.info("CROSS-SECTION EXTRACTION")
        logger.info(f"Parameters: z_slice={z_slice}mm, resolution={resolution}px")
        logger.info("=" * 70)

        start_time = datetime.now()

        print(f"\nExtracting cross-section at Z = {z_slice:.1f}mm (resolution: {resolution}px)")

        img = np.ones((resolution, resolution)) * 255
        logger.debug(f"Created {resolution}x{resolution} image canvas")

        x_min, x_max = -self.width / 2, self.width / 2
        z_min = 0
        z_max = sum(l.thickness for l in self.layers)

        logger.debug(f"World bounds: X=[{x_min:.1f}, {x_max:.1f}], Z=[{z_min:.1f}, {z_max:.1f}]")

        triangles_processed = 0
        triangles_intersecting = 0
        pixels_colored = 0

        for layer_idx, layer in enumerate(self.layers):
            vertices = np.asarray(layer.mesh.vertices)
            triangles = np.asarray(layer.mesh.triangles)

            layer_intersections = 0

            for tri_idx, tri_indices in enumerate(triangles):
                triangles_processed += 1
                tri_verts = vertices[tri_indices]

                y_coords = tri_verts[:, 1]

                if y_coords.min() <= z_slice <= y_coords.max():
                    triangles_intersecting += 1
                    layer_intersections += 1

                    z_coords = tri_verts[:, 2]
                    x_coords = tri_verts[:, 0]

                    for x_val in x_coords:
                        for z_val in z_coords:
                            px = int((x_val - x_min) / (x_max - x_min) * resolution)
                            pz = int((z_val - z_min) / (z_max - z_min) * resolution)

                            if 0 <= px < resolution and 0 <= pz < resolution:
                                color_val = 255 if layer.color[0] > 0.5 else 50
                                img[resolution - 1 - pz, px] = color_val
                                pixels_colored += 1

            if debug and layer_intersections > 0:
                logger.debug(f"Layer #{layer_idx} ({layer.get_stats()['color_type']}): "
                             f"{layer_intersections} triangles intersect slice plane")

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Cross-section extraction complete in {elapsed:.2f}s")
        logger.info(f"  Triangles processed: {triangles_processed}")
        logger.info(f"  Triangles intersecting: {triangles_intersecting}")
        logger.info(f"  Pixels colored: {pixels_colored}")

        print("Cross-section extracted!")
        return img.astype(np.uint8)

    # ========================================================================
    # VISUALIZATION
    # ========================================================================

    def visualize(self, title: str = "Damascus 3D Billet", use_matplotlib: bool = True):
        """
        Visualize the billet in 3D.

        Controls (when not using matplotlib):
        - Rotate: Left mouse drag
        - Zoom: Mouse wheel
        - Pan: Ctrl + Left mouse drag
        """
        logger.info(f"Visualizing billet: {title}")
        logger.debug(f"Using matplotlib: {use_matplotlib}")

        print(f"\n{title}")
        print("=" * 50)

        if use_matplotlib:
            self._visualize_matplotlib(title)
        else:
            print("Controls:")
            print("  Rotate: Left click + drag")
            print("  Zoom: Mouse wheel")
            print("  Pan: Ctrl + Left click + drag")
            print("  Reset view: R")
            print("  Screenshot: Ctrl + S")
            print("=" * 50)

            meshes = self.get_all_meshes()

            coord_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
                size=20.0, origin=[0, 0, 0])

            o3d.visualization.draw_geometries(
                meshes + [coord_frame],
                window_name=title,
                width=1200,
                height=800
            )

    def _visualize_matplotlib(self, title: str):
        """Visualize using matplotlib (more compatible with Wayland)."""
        logger.debug("Setting up matplotlib 3D visualization")

        print("Using Matplotlib 3D viewer (Wayland-compatible)")
        print("Controls:")
        print("  Rotate: Left click + drag")
        print("  Zoom: Mouse wheel (or right click + drag)")
        print("  Close window to continue")
        print("=" * 50)

        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')

        logger.debug(f"Rendering {len(self.layers)} layers...")

        for layer_idx, layer in enumerate(self.layers):
            vertices = np.asarray(layer.mesh.vertices)
            triangles = np.asarray(layer.mesh.triangles)

            logger.debug(f"  Rendering layer #{layer_idx}: {len(triangles)} triangles")

            faces = vertices[triangles]

            poly_collection = Poly3DCollection(
                faces,
                facecolors=layer.color,
                edgecolors='black',
                linewidths=0.1,
                alpha=0.95
            )
            ax.add_collection3d(poly_collection)

        ax.set_xlabel('X (width) [mm]', fontsize=10)
        ax.set_ylabel('Y (length) [mm]', fontsize=10)
        ax.set_zlabel('Z (height) [mm]', fontsize=10)

        max_range = max(self.width, sum(l.thickness for l in self.layers), self.length)
        mid_x = 0
        mid_y = sum(l.thickness for l in self.layers) / 2
        mid_z = 0

        logger.debug(f"View bounds: max_range={max_range:.1f}mm, center=({mid_x}, {mid_y:.1f}, {mid_z})")

        ax.set_xlim(mid_x - max_range / 2, mid_x + max_range / 2)
        ax.set_ylim(mid_y - max_range / 2, mid_y + max_range / 2)
        ax.set_zlim(mid_z - max_range / 2, mid_z + max_range / 2)

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.view_init(elev=20, azim=45)

        plt.tight_layout()
        logger.debug("Displaying visualization window")
        plt.show()
        logger.debug("Visualization window closed")

    # ========================================================================
    # EXPORT CAPABILITIES
    # ========================================================================

    def save_cross_section_image(self, z_slice: float, output_path: str, resolution: int = 1000):
        """
        Extract and save a cross-section as an image file.

        Args:
            z_slice: Z position to slice at (mm)
            output_path: Path to save image (PNG format)
            resolution: Image resolution (pixels per side)
        """
        logger.info(f"Saving cross-section image: {output_path}")
        logger.debug(f"  Z slice: {z_slice}mm, Resolution: {resolution}px")

        img_array = self.extract_cross_section(z_slice, resolution, debug=False)
        img = Image.fromarray(img_array)
        img.save(output_path)

        logger.info(f"Cross-section saved to: {output_path}")
        print(f"Saved cross-section to: {output_path}")

    def export_3d_model(self, output_path: str, merge_layers: bool = False):
        """
        Export the billet as a 3D model file.

        SUPPORTED FORMATS: .obj, .stl, .ply, .pcd

        Args:
            output_path: Path to save model (extension determines format)
            merge_layers: If True, merge all layers into single mesh
        """
        logger.info(f"Exporting 3D model: {output_path}")
        logger.debug(f"  Merge layers: {merge_layers}")

        if merge_layers:
            logger.debug("Merging all layers into single mesh...")
            combined_mesh = o3d.geometry.TriangleMesh()
            for layer in self.layers:
                combined_mesh += layer.mesh

            logger.debug(f"  Combined mesh: {len(combined_mesh.vertices)} vertices, "
                         f"{len(combined_mesh.triangles)} triangles")

            success = o3d.io.write_triangle_mesh(output_path, combined_mesh)
        else:
            base_path = output_path.rsplit('.', 1)[0]
            extension = output_path.rsplit('.', 1)[1]

            for layer_idx, layer in enumerate(self.layers):
                layer_path = f"{base_path}_layer{layer_idx:03d}.{extension}"
                logger.debug(f"  Exporting layer #{layer_idx} to {layer_path}")
                success = o3d.io.write_triangle_mesh(layer_path, layer.mesh)

        if success:
            logger.info(f"3D model export successful: {output_path}")
            print(f"3D model saved to: {output_path}")
        else:
            logger.error(f"3D model export FAILED: {output_path}")
            print(f"ERROR: Failed to save 3D model")

    def save_operation_log(self, output_path: str = "damascus_operations.json"):
        """
        Save complete operation history to JSON file for analysis.

        Args:
            output_path: Path to save JSON file
        """
        logger.info(f"Saving operation log to: {output_path}")

        log_data = {
            'billet_info': {
                'width_mm': self.width,
                'length_mm': self.length,
                'layer_count': len(self.layers),
                'total_height_mm': sum(l.thickness for l in self.layers)
            },
            'operations': self.operation_history,
            'final_stats': self.get_billet_stats()
        }

        with open(output_path, 'w') as f:
            json.dump(log_data, f, indent=2)

        logger.info(f"Operation log saved: {len(self.operation_history)} operations recorded")
        print(f"Operation log saved to: {output_path}")


# Install API call instrumentation on both engine classes
install_api_call_logging(DamascusLayer, Damascus3DBillet)
