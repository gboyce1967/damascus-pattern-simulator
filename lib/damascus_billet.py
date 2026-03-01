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
    # WEDGE DEFORMATION (Feather Damascus)
    # ========================================================================

    def apply_wedge_deformation(self, wedge_depth: float = 20.0, wedge_angle: float = 30.0,
                                split_gap: float = 5.0, debug: bool = True):
        """
        Apply wedge deformation to simulate feather Damascus.

        PHYSICS SIMULATION:
        ------------------
        Real-world process:
          1. Wedge is driven into center of billet from top
          2. Billet splits into two halves
          3. Material flows downward and outward (waterfall effect)
          4. Top layers displace more than bottom layers
          5. Wedge angle creates non-parallel edges

        Args:
            wedge_depth: How deep the wedge penetrates (mm)
            wedge_angle: Angle of wedge in degrees (from vertical)
            split_gap: Gap created at the split point (mm)
            debug: Enable detailed debug logging
        """
        logger.info("=" * 70)
        logger.info("WEDGE DEFORMATION OPERATION")
        logger.info(f"Parameters: depth={wedge_depth}mm, angle={wedge_angle}°, gap={split_gap}mm")
        logger.info("=" * 70)

        start_time = datetime.now()

        print(f"\nApplying wedge deformation:")
        print(f"  Depth: {wedge_depth}mm")
        print(f"  Angle: {wedge_angle}°")
        print(f"  Split gap: {split_gap}mm")
        print("This applies REAL 3D physics - each layer deforms based on its position!")

        center_x = 0.0
        wedge_angle_rad = np.deg2rad(wedge_angle)
        total_height = sum(l.thickness for l in self.layers)

        logger.debug(f"Wedge center X: {center_x}")
        logger.debug(f"Wedge angle (radians): {wedge_angle_rad:.4f}")
        logger.debug(f"Total billet height: {total_height:.2f}mm")

        # Statistics tracking
        total_vertices_processed = 0
        displacement_stats = {
            'max_vertical': 0.0,
            'max_horizontal': 0.0,
            'mean_vertical': [],
            'mean_horizontal': []
        }

        for layer_idx, layer in enumerate(self.layers):
            logger.debug(f"Processing layer #{layer_idx}/{len(self.layers)}")

            vertices = np.asarray(layer.mesh.vertices).copy()
            original_vertices = vertices.copy()

            layer_position_normalized = layer.z_position / total_height

            logger.debug(f"  Layer position (normalized): {layer_position_normalized:.3f}")
            logger.debug(f"  Vertex count: {len(vertices)}")

            vertical_displacements = []
            horizontal_displacements = []

            for i, vertex in enumerate(vertices):
                x, y, z = vertex

                dist_from_center = abs(x - center_x)
                side = np.sign(x - center_x) if abs(x - center_x) > 0.001 else 1.0

                sigma = self.width / 3.0
                intensity = np.exp(-(dist_from_center ** 2) / (2 * sigma ** 2))

                downward_displacement = -wedge_depth * intensity * layer_position_normalized
                horizontal_displacement = side * split_gap * intensity * layer_position_normalized
                horizontal_displacement += side * wedge_depth * np.tan(wedge_angle_rad) * intensity * layer_position_normalized

                vertices[i, 0] += horizontal_displacement
                vertices[i, 2] += downward_displacement

                vertical_displacements.append(abs(downward_displacement))
                horizontal_displacements.append(abs(horizontal_displacement))

                if debug and i % 10 == 0:
                    logger.debug(f"    Vertex {i}: ({x:.2f}, {y:.2f}, {z:.2f}) -> "
                                 f"({vertices[i, 0]:.2f}, {vertices[i, 1]:.2f}, {vertices[i, 2]:.2f}) | "
                                 f"Δx={horizontal_displacement:.2f}, Δz={downward_displacement:.2f}")

            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()

            deformation_record = {
                'operation': 'wedge',
                'timestamp': datetime.now().isoformat(),
                'parameters': {
                    'wedge_depth': wedge_depth,
                    'wedge_angle': wedge_angle,
                    'split_gap': split_gap
                },
                'displacement_stats': {
                    'vertical_max': max(vertical_displacements),
                    'vertical_mean': np.mean(vertical_displacements),
                    'horizontal_max': max(horizontal_displacements),
                    'horizontal_mean': np.mean(horizontal_displacements)
                }
            }
            layer.deformation_history.append(deformation_record)

            displacement_stats['max_vertical'] = max(displacement_stats['max_vertical'], max(vertical_displacements))
            displacement_stats['max_horizontal'] = max(displacement_stats['max_horizontal'], max(horizontal_displacements))
            displacement_stats['mean_vertical'].append(np.mean(vertical_displacements))
            displacement_stats['mean_horizontal'].append(np.mean(horizontal_displacements))

            total_vertices_processed += len(vertices)

            logger.debug(f"  Layer #{layer_idx} deformation complete:")
            logger.debug(f"    Vertical: max={max(vertical_displacements):.2f}mm, mean={np.mean(vertical_displacements):.2f}mm")
            logger.debug(f"    Horizontal: max={max(horizontal_displacements):.2f}mm, mean={np.mean(horizontal_displacements):.2f}mm")

        elapsed = (datetime.now() - start_time).total_seconds()

        logger.info(f"Wedge deformation complete in {elapsed:.2f}s")
        logger.info(f"  Processed {total_vertices_processed} vertices across {len(self.layers)} layers")
        logger.info(f"  Max vertical displacement: {displacement_stats['max_vertical']:.2f}mm")
        logger.info(f"  Max horizontal displacement: {displacement_stats['max_horizontal']:.2f}mm")

        self.operation_history.append({
            'operation': 'wedge_deformation',
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': elapsed,
            'parameters': {
                'wedge_depth': wedge_depth,
                'wedge_angle': wedge_angle,
                'split_gap': split_gap
            },
            'stats': displacement_stats
        })

        print("Deformation complete!")

    # ========================================================================
    # TWIST DEFORMATION (Ladder/Twist Damascus)
    # ========================================================================

    def apply_twist(self, angle_degrees: float = 90.0, axis: str = 'z', debug: bool = True):
        """
        Apply torsional twist to the billet (for ladder/twist Damascus).

        Args:
            angle_degrees: Total rotation angle in degrees
            axis: Axis to twist around ('y' for length axis)
            debug: Enable detailed debug logging
        """
        logger.info("=" * 70)
        logger.info("TWIST DEFORMATION OPERATION")
        logger.info(f"Parameters: angle={angle_degrees}°, axis={axis}")
        logger.info("=" * 70)

        start_time = datetime.now()

        print(f"\nApplying twist deformation: {angle_degrees}° around {axis}-axis")

        angle_rad = np.deg2rad(angle_degrees)
        logger.debug(f"Twist angle (radians): {angle_rad:.4f}")

        total_vertices_processed = 0

        for layer_idx, layer in enumerate(self.layers):
            logger.debug(f"Twisting layer #{layer_idx}")

            vertices = np.asarray(layer.mesh.vertices).copy()

            for i, vertex in enumerate(vertices):
                x, y, z = vertex

                normalized_position = (y + self.length / 2) / self.length
                current_angle = angle_rad * normalized_position

                if debug and i == 0:
                    logger.debug(f"  Y position: {y:.2f}mm, normalized: {normalized_position:.3f}, "
                                 f"rotation: {np.rad2deg(current_angle):.2f}°")

                if axis == 'y':
                    x_center = 0
                    z_center = layer.z_position + layer.thickness / 2

                    x_rel = x - x_center
                    z_rel = z - z_center

                    x_new = x_rel * np.cos(current_angle) - z_rel * np.sin(current_angle)
                    z_new = x_rel * np.sin(current_angle) + z_rel * np.cos(current_angle)

                    vertices[i, 0] = x_new + x_center
                    vertices[i, 2] = z_new + z_center

            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()

            layer.deformation_history.append({
                'operation': 'twist',
                'timestamp': datetime.now().isoformat(),
                'parameters': {'angle_degrees': angle_degrees, 'axis': axis}
            })

            total_vertices_processed += len(vertices)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Twist complete in {elapsed:.2f}s - processed {total_vertices_processed} vertices")

        self.operation_history.append({
            'operation': 'twist',
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': elapsed,
            'parameters': {'angle_degrees': angle_degrees, 'axis': axis}
        })

        print("Twist complete!")

    # ========================================================================
    # COMPRESSION OPERATION
    # ========================================================================

    def apply_compression(self, compression_factor: float = 0.8, debug: bool = True):
        """
        Compress the billet vertically (simulates hammering/pressing).

        Args:
            compression_factor: Multiply height by this factor (< 1.0 compresses)
            debug: Enable detailed debug logging
        """
        logger.info("=" * 70)
        logger.info("COMPRESSION OPERATION")
        logger.info(f"Parameters: factor={compression_factor} ({compression_factor * 100:.1f}%)")
        logger.info("=" * 70)

        start_time = datetime.now()

        total_height_before = sum(l.thickness for l in self.layers)
        total_height_after = total_height_before * compression_factor

        print(f"\nApplying compression: {compression_factor:.1%} of original height")
        logger.debug(f"Height before: {total_height_before:.2f}mm")
        logger.debug(f"Height after: {total_height_after:.2f}mm")
        logger.debug(f"Reduction: {total_height_before - total_height_after:.2f}mm")

        for layer_idx, layer in enumerate(self.layers):
            logger.debug(f"Compressing layer #{layer_idx}")

            vertices = np.asarray(layer.mesh.vertices).copy()

            original_y_min = vertices[:, 2].min()
            original_y_max = vertices[:, 2].max()

            # Compress in Z direction (height)
            for i, vertex in enumerate(vertices):
                x, y, z = vertex
                vertices[i, 2] = z * compression_factor

            # Update layer properties
            layer.thickness *= compression_factor
            layer.z_position *= compression_factor

            new_y_min = vertices[:, 2].min()
            new_y_max = vertices[:, 2].max()

            logger.debug(f"  Layer #{layer_idx} Z bounds: [{original_y_min:.2f}, {original_y_max:.2f}] -> "
                         f"[{new_y_min:.2f}, {new_y_max:.2f}]")

            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()

            layer.deformation_history.append({
                'operation': 'compression',
                'timestamp': datetime.now().isoformat(),
                'parameters': {'compression_factor': compression_factor},
                'height_change': {
                    'before': original_y_max - original_y_min,
                    'after': new_y_max - new_y_min
                }
            })

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Compression complete in {elapsed:.2f}s")
        logger.info(f"  Height: {total_height_before:.1f}mm → {total_height_after:.1f}mm")

        self.operation_history.append({
            'operation': 'compression',
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': elapsed,
            'parameters': {'compression_factor': compression_factor},
            'height_change': {
                'before_mm': total_height_before,
                'after_mm': total_height_after
            }
        })

        print(f"Compression complete! Height: {total_height_before:.1f}mm → {total_height_after:.1f}mm")

    # ========================================================================
    # DRILLING OPERATION (Raindrop Damascus)
    # ========================================================================

    def drill_hole(self, x_pos: float = 0.0, z_pos: float = 0.0, radius: float = 10.0, debug: bool = True):
        """
        Drill a hole through the billet.

        Args:
            x_pos: X position of hole center (mm)
            z_pos: Z position of hole center (mm)
            radius: Radius of the hole (mm)
            debug: Enable detailed debug logging
        """
        logger.info("=" * 70)
        logger.info("DRILLING OPERATION")
        logger.info(f"Parameters: position=({x_pos:.1f}, {z_pos:.1f}), radius={radius}mm")
        logger.info("=" * 70)

        start_time = datetime.now()

        print(f"\nDrilling hole at ({x_pos:.1f}, {z_pos:.1f}) with radius {radius:.1f}mm")

        total_vertices_affected = 0

        for layer_idx, layer in enumerate(self.layers):
            logger.debug(f"Drilling through layer #{layer_idx}")

            vertices = np.asarray(layer.mesh.vertices).copy()
            vertices_affected_in_layer = 0

            for i, vertex in enumerate(vertices):
                x, y, z = vertex

                dx = x - x_pos
                dy = y - z_pos
                dist = np.sqrt(dx ** 2 + dy ** 2)

                if dist < radius * 2.0:
                    vertices_affected_in_layer += 1

                    if dist < radius:
                        push_factor = 1.5
                        logger.debug(f"  Vertex {i} INSIDE hole: dist={dist:.2f}mm, push={push_factor}")
                    else:
                        influence = np.exp(-((dist - radius) ** 2) / (2 * radius ** 2))
                        push_factor = influence * 0.3

                    if dist > 0.001:
                        direction_x = dx / dist
                        direction_y = dy / dist

                        displacement_x = direction_x * radius * push_factor
                        displacement_y = direction_y * radius * push_factor

                        vertices[i, 0] += displacement_x
                        vertices[i, 1] += displacement_y

            logger.debug(f"  Layer #{layer_idx}: {vertices_affected_in_layer} vertices affected")
            total_vertices_affected += vertices_affected_in_layer

            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()

            layer.deformation_history.append({
                'operation': 'drill',
                'timestamp': datetime.now().isoformat(),
                'parameters': {'x_pos': x_pos, 'z_pos': z_pos, 'radius': radius},
                'vertices_affected': vertices_affected_in_layer
            })

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Drilling complete in {elapsed:.2f}s")
        logger.info(f"  Total vertices affected: {total_vertices_affected}")

        self.operation_history.append({
            'operation': 'drill_hole',
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': elapsed,
            'parameters': {'x_pos': x_pos, 'z_pos': z_pos, 'radius': radius},
            'vertices_affected': total_vertices_affected
        })

        print("Drilling complete!")

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
