#!/usr/bin/env python3
"""
3D Damascus Billet Simulator - Production Version
==================================================

BREAKTHROUGH APPROACH:
---------------------
This simulator uses REAL 3D mesh layers with REAL physics-based deformation,
not 2D pixel manipulation. This is fundamentally how Damascus forging actually works.

KEY INSIGHT FROM DEBUGGING SESSION:
-----------------------------------
The previous 2D approach failed because:
  - Horizontal layers in a 2D pixel array have no physical "ends" to pull together
  - You can't simulate 3D material flow by warping pixels
  - The wedge split creates actual 3D geometry changes that pixels cannot represent

NEW APPROACH:
------------
  - Each Damascus layer is a 3D triangular mesh (thin rectangular solid)
  - Deformations modify actual 3D vertex positions
  - Physics includes: wedge splitting, twisting, compression, drilling
  - Can view from ANY angle in 3D space
  - Extract 2D cross-sections to see traditional Damascus patterns

ARCHITECTURE:
-------------
  DamascusLayer: Single layer (3D mesh + metadata)
  Damascus3DBillet: Stack of layers + deformation operations
  Logging: Comprehensive debug logging to file + console
  Visualization: Matplotlib 3D (Wayland-compatible)

Author: Damascus Pattern Simulator Team
Date: 2026-02-02
Version: 2.0 (3D Mesh-Based)
"""

import open3d as o3d
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import functools
import inspect
import logging
import os
import sys
from datetime import datetime
import json
from PIL import Image
from pathlib import Path


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def _get_runtime_root() -> Path:
    """
    Return runtime root for generated artifacts.

    - Source runs: project root (directory containing this file)
    - Frozen runs: directory containing the executable
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


RUNTIME_ROOT = _get_runtime_root()
LOGS_DIR = RUNTIME_ROOT / "logs"


def setup_logging(debug_level: str = "DEBUG") -> logging.Logger:
    """
    Configure comprehensive logging for debugging.
    
    Creates both console and file handlers with detailed formatting.
    Log file is saved to logs/damascus_3d_debug_<timestamp>.log
    
    DEBUG CAPABILITY:
    ----------------
    - All function calls are logged
    - All parameter values are logged
    - Vertex transformation calculations are logged
    - Performance metrics are tracked
    - State changes are recorded
    
    Args:
        debug_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('Damascus3D')
    logger.setLevel(getattr(logging, debug_level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler - INFO and above (user-facing messages)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )
    console_handler.setFormatter(console_format)
    
    # File handler - DEBUG and above (everything for debugging)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f'damascus_3d_debug_{timestamp}.log'
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(funcName)-25s | Line %(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info("="*70)
    logger.info("Damascus 3D Simulator - Debug Session Started")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Log file: {log_path}")
    logger.info("="*70)
    
    return logger


# Initialize global logger
logger = setup_logging("DEBUG")


# ============================================================================
# API CALL INSTRUMENTATION
# ============================================================================

def _resolve_source_location(func) -> Tuple[str, int]:
    """Return source filename and definition start line for a callable."""
    source_path = inspect.getsourcefile(func)
    source_file = os.path.basename(source_path) if source_path else "<unknown>"
    try:
        source_line = inspect.getsourcelines(func)[1]
    except (OSError, TypeError):
        source_line = -1
    return source_file, source_line


def _api_call_wrapper(func):
    """Wrap callable to emit a structured API call log on each invocation."""
    if getattr(func, "_damascus_api_wrapped", False):
        return func

    source_file, source_line = _resolve_source_location(func)

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        logger.info(
            "API_CALL | %s | file=%s | starts_at_line=%d",
            func.__qualname__,
            source_file,
            source_line,
        )
        return func(*args, **kwargs)

    wrapped._damascus_api_wrapped = True
    return wrapped


# ============================================================================
# DAMASCUS LAYER CLASS
# ============================================================================

class DamascusLayer:
    """
    Represents a single layer in the Damascus billet as a 3D triangular mesh.
    
    DESIGN NOTES:
    ------------
    - Each layer is a thin rectangular solid (box mesh)
    - Positioned in Z-axis (HORIZONTAL stacking on build plate)
    - X-axis: width, Y-axis: length, Z-axis: height (layer stacking)
    - Color represents steel type: light=high-nickel, dark=high-carbon
    
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
        
        # Position: centered in X and Y, stacked in Z (height)
        # X: width (centered at 0)
        # Y: length (centered at 0) 
        # Z: height (layers stack upward from z=0)
        translation = [-self.width/2, -self.length/2, self.z_position]
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


# ============================================================================
# DAMASCUS 3D BILLET CLASS
# ============================================================================

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
        
        This is the most common starting point for Damascus billets.
        
        TECHNICAL DETAILS:
        -----------------
        - Alternates between white (high-nickel) and black (high-carbon) steel
        - Even indices (0, 2, 4...) are white
        - Odd indices (1, 3, 5...) are black
        
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
        
        DEBUG OUTPUT:
        ------------
        Includes layer count, dimensions, vertex statistics, deformation history
        
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
        
        Mathematical model:
          - Vertical displacement: Δy = -depth × intensity × (layer_height / total_height)
          - Horizontal displacement: Δx = side × (gap + depth×tan(angle)) × intensity × normalized_height
          - Intensity function: exp(-(dist²) / (2σ²))  [Gaussian falloff]
        
        DEBUGGING:
        ---------
        When debug=True, logs:
          - Per-layer displacement statistics
          - Min/max/mean vertex displacements
          - Deformation bounds
          - Performance timing
        
        Args:
            wedge_depth: How deep the wedge penetrates (mm)
            wedge_angle: Angle of wedge in degrees (from vertical)
            split_gap: Gap created at the split point (mm)
            debug: Enable detailed debug logging
        """
        logger.info("="*70)
        logger.info("WEDGE DEFORMATION OPERATION")
        logger.info(f"Parameters: depth={wedge_depth}mm, angle={wedge_angle}°, gap={split_gap}mm")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        print(f"\nApplying wedge deformation:")
        print(f"  Depth: {wedge_depth}mm")
        print(f"  Angle: {wedge_angle}°")
        print(f"  Split gap: {split_gap}mm")
        print("This applies REAL 3D physics - each layer deforms based on its position!")
        
        center_x = 0.0  # Wedge at center
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
        
        # Process each layer
        for layer_idx, layer in enumerate(self.layers):
            logger.debug(f"Processing layer #{layer_idx}/{len(self.layers)}")
            
            vertices = np.asarray(layer.mesh.vertices).copy()
            original_vertices = vertices.copy()
            
            # Layer's normalized position (0 = bottom, 1 = top)
            layer_position_normalized = layer.z_position / total_height
            
            logger.debug(f"  Layer position (normalized): {layer_position_normalized:.3f}")
            logger.debug(f"  Vertex count: {len(vertices)}")
            
            # Track displacements for this layer
            vertical_displacements = []
            horizontal_displacements = []
            
            # For each vertex, calculate deformation
            for i, vertex in enumerate(vertices):
                x, y, z = vertex
                
                # Distance from wedge centerline
                dist_from_center = abs(x - center_x)
                
                # Which side of the wedge? (-1 = left, +1 = right)
                side = np.sign(x - center_x) if abs(x - center_x) > 0.001 else 1.0
                
                # Deformation intensity: maximum at center, falls off with distance
                # Using smooth Gaussian falloff for realistic material flow
                sigma = self.width / 3.0  # Deformation zone width
                intensity = np.exp(-(dist_from_center**2) / (2 * sigma**2))
                
                # DOWNWARD DISPLACEMENT (in -Z direction, since layers stack in Z)
                # Layers are pulled down by wedge - creates waterfall
                # Top layers displace more than bottom layers
                downward_displacement = -wedge_depth * intensity * layer_position_normalized
                
                # HORIZONTAL DISPLACEMENT (in X direction)
                # Wedge pushes layers outward - creates the split
                # The wedge angle determines how much horizontal spread
                # Two components: split gap + angle-induced spread
                horizontal_displacement = side * split_gap * intensity * layer_position_normalized
                horizontal_displacement += side * wedge_depth * np.tan(wedge_angle_rad) * intensity * layer_position_normalized
                
                # Apply the deformations
                # NEW COORDINATE SYSTEM: X=width, Y=length, Z=height (layers stack in Z)
                vertices[i, 0] += horizontal_displacement  # X axis (width) - split
                vertices[i, 2] += downward_displacement    # Z axis (height) - waterfall
                
                # Track displacements for statistics
                vertical_displacements.append(abs(downward_displacement))
                horizontal_displacements.append(abs(horizontal_displacement))
                
                # Log sample vertices (every 10th vertex to avoid log spam)
                if debug and i % 10 == 0:
                    logger.debug(f"    Vertex {i}: ({x:.2f}, {y:.2f}, {z:.2f}) -> "
                               f"({vertices[i,0]:.2f}, {vertices[i,1]:.2f}, {vertices[i,2]:.2f}) | "
                               f"Δx={horizontal_displacement:.2f}, Δz={downward_displacement:.2f}")
            
            # Update the mesh with deformed vertices
            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()
            
            # Record deformation in layer history
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
            
            # Update global statistics
            displacement_stats['max_vertical'] = max(displacement_stats['max_vertical'], max(vertical_displacements))
            displacement_stats['max_horizontal'] = max(displacement_stats['max_horizontal'], max(horizontal_displacements))
            displacement_stats['mean_vertical'].append(np.mean(vertical_displacements))
            displacement_stats['mean_horizontal'].append(np.mean(horizontal_displacements))
            
            total_vertices_processed += len(vertices)
            
            logger.debug(f"  Layer #{layer_idx} deformation complete:")
            logger.debug(f"    Vertical: max={max(vertical_displacements):.2f}mm, mean={np.mean(vertical_displacements):.2f}mm")
            logger.debug(f"    Horizontal: max={max(horizontal_displacements):.2f}mm, mean={np.mean(horizontal_displacements):.2f}mm")
        
        # Operation complete - log summary
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Wedge deformation complete in {elapsed:.2f}s")
        logger.info(f"  Processed {total_vertices_processed} vertices across {len(self.layers)} layers")
        logger.info(f"  Max vertical displacement: {displacement_stats['max_vertical']:.2f}mm")
        logger.info(f"  Max horizontal displacement: {displacement_stats['max_horizontal']:.2f}mm")
        
        # Record in billet history
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
        
        PHYSICS SIMULATION:
        ------------------
        Real-world process:
          1. Billet is clamped at one end
          2. Other end is rotated (twisted)
          3. Twist varies linearly along length
          4. Creates spiral/ladder pattern when viewed in cross-section
        
        Mathematical model:
          - Rotation angle varies: θ(y) = θ_max × (y + L/2) / L
          - Applied as rotation matrix around axis
          - For Y-axis twist: rotates in XZ plane (around length axis)
        
        DEBUGGING:
        ---------
        Logs rotation angles, vertex positions before/after, per-layer statistics
        
        Args:
            angle_degrees: Total rotation angle in degrees
            axis: Axis to twist around ('y' for length axis)
            debug: Enable detailed debug logging
        """
        logger.info("="*70)
        logger.info("TWIST DEFORMATION OPERATION")
        logger.info(f"Parameters: angle={angle_degrees}°, axis={axis}")
        logger.info("="*70)
        
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
                
                # Twist varies linearly along the length (Y-axis)
                # y = -length/2 => no twist (0°)
                # y = +length/2 => full twist (angle_degrees)
                normalized_position = (y + self.length/2) / self.length  # 0 to 1
                current_angle = angle_rad * normalized_position
                
                if debug and i == 0:  # Log first vertex of each layer
                    logger.debug(f"  Y position: {y:.2f}mm, normalized: {normalized_position:.3f}, "
                               f"rotation: {np.rad2deg(current_angle):.2f}°")
                
                # Rotate around Y-axis (length axis)
                # This rotates in the XZ plane
                if axis == 'y':
                    # Rotate in XZ plane around Y-axis
                    x_center = 0
                    z_center = layer.z_position + layer.thickness/2
                    
                    # Translate to origin
                    x_rel = x - x_center
                    z_rel = z - z_center
                    
                    # Apply rotation matrix
                    x_new = x_rel * np.cos(current_angle) - z_rel * np.sin(current_angle)
                    z_new = x_rel * np.sin(current_angle) + z_rel * np.cos(current_angle)
                    
                    # Translate back
                    vertices[i, 0] = x_new + x_center
                    vertices[i, 2] = z_new + z_center
            
            # Update the mesh
            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()
            
            # Record in layer history
            layer.deformation_history.append({
                'operation': 'twist',
                'timestamp': datetime.now().isoformat(),
                'parameters': {'angle_degrees': angle_degrees, 'axis': axis}
            })
            
            total_vertices_processed += len(vertices)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Twist complete in {elapsed:.2f}s - processed {total_vertices_processed} vertices")
        
        # Record in billet history
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
        
        PHYSICS SIMULATION:
        ------------------
        Real-world process:
          1. Billet is hammered or pressed
          2. Height decreases proportionally
          3. Layers consolidate together
          4. After drilling or twisting, compression closes voids
        
        Mathematical model:
          - All Y coordinates scaled by compression_factor
          - Layer thicknesses scaled proportionally
          - Preserves X and Z dimensions
        
        Args:
            compression_factor: Multiply height by this factor (< 1.0 compresses)
            debug: Enable detailed debug logging
        """
        logger.info("="*70)
        logger.info("COMPRESSION OPERATION")
        logger.info(f"Parameters: factor={compression_factor} ({compression_factor*100:.1f}%)")
        logger.info("="*70)
        
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
                # Scale Z position proportionally
                vertices[i, 2] = z * scale_factor
            
            # Update layer properties
            layer.thickness *= compression_factor
            layer.z_position *= compression_factor
            
            new_y_min = vertices[:, 2].min()
            new_y_max = vertices[:, 2].max()
            
            logger.debug(f"  Layer #{layer_idx} Z bounds: [{original_y_min:.2f}, {original_y_max:.2f}] -> "
                        f"[{new_y_min:.2f}, {new_y_max:.2f}]")
            
            # Update mesh
            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()
            
            # Record in history
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
        
        PHYSICS SIMULATION:
        ------------------
        Real-world process:
          1. Drill bit removes material
          2. Surrounding material is displaced radially outward
          3. Creates void that will compress into raindrop shape
        
        Mathematical model:
          - Inside hole (dist < radius): strong radial push outward
          - Near hole (radius < dist < 2×radius): gentle radial push with falloff
          - Falloff function: exp(-((dist-radius)²) / (2×radius²))
        
        DEBUGGING:
        ---------
        Logs hole position, affected vertex count per layer, displacement statistics
        
        Args:
            x_pos: X position of hole center (mm)
            z_pos: Z position of hole center (mm)
            radius: Radius of the hole (mm)
            debug: Enable detailed debug logging
        """
        logger.info("="*70)
        logger.info("DRILLING OPERATION")
        logger.info(f"Parameters: position=({x_pos:.1f}, {z_pos:.1f}), radius={radius}mm")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        print(f"\nDrilling hole at ({x_pos:.1f}, {z_pos:.1f}) with radius {radius:.1f}mm")
        
        total_vertices_affected = 0
        
        for layer_idx, layer in enumerate(self.layers):
            logger.debug(f"Drilling through layer #{layer_idx}")
            
            vertices = np.asarray(layer.mesh.vertices).copy()
            vertices_affected_in_layer = 0
            
            for i, vertex in enumerate(vertices):
                x, y, z = vertex
                
                # Distance from hole center (in XY plane - horizontal)
                dx = x - x_pos
                dy = y - z_pos
                dist = np.sqrt(dx**2 + dy**2)
                
                # Only affect vertices within influence radius
                if dist < radius * 2.0:
                    vertices_affected_in_layer += 1
                    
                    if dist < radius:
                        # Inside the hole - push outward strongly
                        push_factor = 1.5
                        logger.debug(f"  Vertex {i} INSIDE hole: dist={dist:.2f}mm, push={push_factor}")
                    else:
                        # Outside but close - gentle push with smooth falloff
                        influence = np.exp(-((dist - radius)**2) / (2 * radius**2))
                        push_factor = influence * 0.3
                    
                    # Push radially outward in XY plane (horizontal)
                    if dist > 0.001:  # Avoid division by zero at exact center
                        direction_x = dx / dist
                        direction_y = dy / dist
                        
                        displacement_x = direction_x * radius * push_factor
                        displacement_y = direction_y * radius * push_factor
                        
                        vertices[i, 0] += displacement_x
                        vertices[i, 1] += displacement_y
            
            logger.debug(f"  Layer #{layer_idx}: {vertices_affected_in_layer} vertices affected")
            total_vertices_affected += vertices_affected_in_layer
            
            # Update mesh
            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()
            
            # Record in history
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
        
        This slices through all the 3D layers to show the traditional
        Damascus pattern view - this is what you see when you cut and
        etch the blade.
        
        ALGORITHM:
        ---------
        1. Create empty image (white background)
        2. For each layer:
           a. Check each triangle for intersection with Z=z_slice plane
           b. If intersects, rasterize the triangle's contribution
           c. Apply layer color to pixels
        3. Return final composed image
        
        DEBUGGING:
        ---------
        Logs intersection counts, pixel coverage, rendering performance
        
        Args:
            z_slice: Z position to slice at (mm)
            resolution: Resolution of output image (pixels per side)
            debug: Enable detailed debug logging
        
        Returns:
            2D numpy array representing the pattern (0-255 grayscale)
        """
        logger.info("="*70)
        logger.info("CROSS-SECTION EXTRACTION")
        logger.info(f"Parameters: z_slice={z_slice}mm, resolution={resolution}px")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        print(f"\nExtracting cross-section at Z = {z_slice:.1f}mm (resolution: {resolution}px)")
        
        # Create output image (white background)
        img = np.ones((resolution, resolution)) * 255
        logger.debug(f"Created {resolution}x{resolution} image canvas")
        
        # Map from world coordinates to image pixels
        # For horizontal orientation: X=width, Z=height (layer stack)
        x_min, x_max = -self.width/2, self.width/2
        z_min = 0
        z_max = sum(l.thickness for l in self.layers)
        
        logger.debug(f"World bounds: X=[{x_min:.1f}, {x_max:.1f}], Z=[{z_min:.1f}, {z_max:.1f}]")
        
        triangles_processed = 0
        triangles_intersecting = 0
        pixels_colored = 0
        
        # For each layer, determine if it intersects this Z slice
        for layer_idx, layer in enumerate(self.layers):
            vertices = np.asarray(layer.mesh.vertices)
            triangles = np.asarray(layer.mesh.triangles)
            
            layer_intersections = 0
            
            # Check each triangle to see if it intersects the slice plane
            for tri_idx, tri_indices in enumerate(triangles):
                triangles_processed += 1
                tri_verts = vertices[tri_indices]
                
                # Check if triangle intersects the Y = z_slice plane (slicing along length)
                y_coords = tri_verts[:, 1]
                
                # Triangle intersects if z_slice is between min and max y
                if y_coords.min() <= z_slice <= y_coords.max():
                    triangles_intersecting += 1
                    layer_intersections += 1
                    
                    # Get coordinates for this triangle
                    z_coords = tri_verts[:, 2]  # Height (layer stack)
                    x_coords = tri_verts[:, 0]  # Width
                    
                    # Convert to pixel coordinates and rasterize
                    for x_val in x_coords:
                        for z_val in z_coords:
                            # Map to pixel space
                            px = int((x_val - x_min) / (x_max - x_min) * resolution)
                            pz = int((z_val - z_min) / (z_max - z_min) * resolution)
                            
                            if 0 <= px < resolution and 0 <= pz < resolution:
                                # Apply layer color (white=255, black=50)
                                color_val = 255 if layer.color[0] > 0.5 else 50
                                img[resolution - 1 - pz, px] = color_val  # Flip Z for display
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
        
        This opens an interactive window where you can:
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
            
            # Get all meshes
            meshes = self.get_all_meshes()
            
            # Create coordinate frame for reference
            coord_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
                size=20.0, origin=[0, 0, 0])
            
            # Visualize
            o3d.visualization.draw_geometries(
                meshes + [coord_frame],
                window_name=title,
                width=1200,
                height=800
            )
    
    def _visualize_matplotlib(self, title: str):
        """
        Visualize using matplotlib (more compatible with Wayland).
        
        IMPLEMENTATION DETAILS:
        ----------------------
        - Creates 3D axis with equal aspect ratio
        - Renders each layer as Poly3DCollection
        - Adds coordinate labels and grid
        - Interactive rotation and zoom
        """
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
        
        # Draw each layer
        for layer_idx, layer in enumerate(self.layers):
            vertices = np.asarray(layer.mesh.vertices)
            triangles = np.asarray(layer.mesh.triangles)
            
            logger.debug(f"  Rendering layer #{layer_idx}: {len(triangles)} triangles")
            
            # Create faces from triangles
            faces = vertices[triangles]
            
            # Create 3D polygon collection
            poly_collection = Poly3DCollection(
                faces,
                facecolors=layer.color,
                edgecolors='black',
                linewidths=0.1,
                alpha=0.95
            )
            ax.add_collection3d(poly_collection)
        
        # Set axis labels and limits
        # NEW COORDINATE SYSTEM: X=width, Y=length, Z=height
        ax.set_xlabel('X (width) [mm]', fontsize=10)
        ax.set_ylabel('Y (length) [mm]', fontsize=10)
        ax.set_zlabel('Z (height) [mm]', fontsize=10)
        
        # Set equal aspect ratio and limits
        max_range = max(self.width, sum(l.thickness for l in self.layers), self.length)
        mid_x = 0
        mid_y = sum(l.thickness for l in self.layers) / 2
        mid_z = 0
        
        logger.debug(f"View bounds: max_range={max_range:.1f}mm, center=({mid_x}, {mid_y:.1f}, {mid_z})")
        
        ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
        ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
        ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Set initial view angle (looking from front-right corner, slightly above)
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
        
        # Extract cross-section
        img_array = self.extract_cross_section(z_slice, resolution, debug=False)
        
        # Save using PIL
        img = Image.fromarray(img_array)
        img.save(output_path)
        
        logger.info(f"Cross-section saved to: {output_path}")
        print(f"Saved cross-section to: {output_path}")
    
    def export_3d_model(self, output_path: str, merge_layers: bool = False):
        """
        Export the billet as a 3D model file.
        
        SUPPORTED FORMATS:
        -----------------
        - .obj (Wavefront OBJ)
        - .stl (STereoLithography)
        - .ply (Stanford Polygon Library)
        - .pcd (Point Cloud Data)
        
        Args:
            output_path: Path to save model (extension determines format)
            merge_layers: If True, merge all layers into single mesh
        """
        logger.info(f"Exporting 3D model: {output_path}")
        logger.debug(f"  Merge layers: {merge_layers}")
        
        if merge_layers:
            # Combine all layers into single mesh
            logger.debug("Merging all layers into single mesh...")
            combined_mesh = o3d.geometry.TriangleMesh()
            for layer in self.layers:
                combined_mesh += layer.mesh
            
            logger.debug(f"  Combined mesh: {len(combined_mesh.vertices)} vertices, "
                        f"{len(combined_mesh.triangles)} triangles")
            
            success = o3d.io.write_triangle_mesh(output_path, combined_mesh)
        else:
            # Export each layer separately (creates multiple files)
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
        
        DEBUGGING USE:
        -------------
        This creates a machine-readable log of all operations performed
        on the billet, including parameters and statistics. Useful for:
        - Reproducing exact sequences
        - Performance analysis
        - Parameter tuning
        - Bug investigation
        
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


def _install_api_call_logging():
    """
    Instrument public simulator methods with API_CALL logs.

    Public methods from both `DamascusLayer` and `Damascus3DBillet` are wrapped
    so each invocation records the callable, source file, and definition line.
    """
    for cls in (DamascusLayer, Damascus3DBillet):
        for attr_name, attr_value in list(vars(cls).items()):
            if attr_name.startswith('_'):
                continue
            if not inspect.isfunction(attr_value):
                continue
            setattr(cls, attr_name, _api_call_wrapper(attr_value))


_install_api_call_logging()


# ============================================================================
# DEMONSTRATION FUNCTIONS
# ============================================================================

def demo_feather_pattern():
    """
    Demo: Feather Damascus using wedge deformation.
    
    PROCESS:
    -------
    1. Create billet with 30 alternating layers
    2. Apply wedge split (creates two waterfalls)
    3. Extract cross-section to view pattern
    
    EXPECTED RESULT:
    ---------------
    Feather/waterfall pattern with central vein
    """
    logger.info("="*70)
    logger.info("STARTING FEATHER DAMASCUS DEMO")
    logger.info("="*70)
    
    print("\n" + "=" * 70)
    print("  DEMO 1: FEATHER DAMASCUS (Wedge Split)")
    print("=" * 70)
    
    billet = Damascus3DBillet(width=50.0, length=100.0)
    billet.create_simple_layers(num_layers=30, white_thickness=0.8, black_thickness=0.8)
    
    print("\nStep 1: Original billet")
    billet.visualize("Feather Damascus - Step 1: Original Billet")
    
    print("\nStep 2: Wedge split")
    billet.apply_wedge_deformation(wedge_depth=18.0, wedge_angle=35.0, split_gap=6.0, debug=True)
    billet.visualize("Feather Damascus - Step 2: After Wedge Split")
    
    print("\nStep 3: Extract cross-section to see the pattern")
    cross_section = billet.extract_cross_section(z_slice=0.0, resolution=800, debug=True)
    
    # Display the cross-section
    plt.figure(figsize=(12, 8))
    plt.imshow(cross_section, cmap='gray', vmin=0, vmax=255)
    plt.title('Feather Damascus - Cross-Section View', fontsize=14, fontweight='bold')
    plt.xlabel('Width', fontsize=10)
    plt.ylabel('Height (layers)', fontsize=10)
    plt.tight_layout()
    plt.show()
    
    # Save outputs
    billet.save_cross_section_image(z_slice=0.0, output_path="feather_pattern.png", resolution=1600)
    billet.save_operation_log("feather_operations.json")
    
    logger.info("Feather Damascus demo complete")
    return billet


def demo_twist_pattern():
    """
    Demo: Ladder/Twist Damascus.
    
    PROCESS:
    -------
    1. Create billet with 24 layers
    2. Apply 180° twist along length
    3. Compress to consolidate
    4. Extract cross-section to view ladder pattern
    """
    logger.info("="*70)
    logger.info("STARTING TWIST DAMASCUS DEMO")
    logger.info("="*70)
    
    print("\n" + "=" * 70)
    print("  DEMO 2: LADDER/TWIST DAMASCUS")
    print("=" * 70)
    
    billet = Damascus3DBillet(width=40.0, length=120.0)
    billet.create_simple_layers(num_layers=24, white_thickness=1.0, black_thickness=1.0)
    
    print("\nStep 1: Original billet")
    billet.visualize("Twist Damascus - Step 1: Original Billet")
    
    print("\nStep 2: Apply twist")
    billet.apply_twist(angle_degrees=180.0, axis='y', debug=True)
    billet.visualize("Twist Damascus - Step 2: After 180° Twist")
    
    print("\nStep 3: Compress to consolidate")
    billet.apply_compression(compression_factor=0.7, debug=True)
    billet.visualize("Twist Damascus - Step 3: After Compression")
    
    print("\nStep 4: Extract cross-section")
    cross_section = billet.extract_cross_section(z_slice=0.0, resolution=800, debug=True)
    
    plt.figure(figsize=(12, 8))
    plt.imshow(cross_section, cmap='gray', vmin=0, vmax=255)
    plt.title('Ladder Damascus - Cross-Section View', fontsize=14, fontweight='bold')
    plt.xlabel('Width', fontsize=10)
    plt.ylabel('Height (layers)', fontsize=10)
    plt.tight_layout()
    plt.show()
    
    # Save outputs
    billet.save_cross_section_image(z_slice=0.0, output_path="twist_pattern.png", resolution=1600)
    billet.save_operation_log("twist_operations.json")
    
    logger.info("Twist Damascus demo complete")
    return billet


def demo_raindrop_pattern():
    """
    Demo: Raindrop Damascus using drilling.
    
    PROCESS:
    -------
    1. Create billet with 25 layers
    2. Drill grid of holes (3x3 pattern)
    3. Compress to close holes and create raindrops
    4. Extract cross-section
    """
    logger.info("="*70)
    logger.info("STARTING RAINDROP DAMASCUS DEMO")
    logger.info("="*70)
    
    print("\n" + "=" * 70)
    print("  DEMO 3: RAINDROP DAMASCUS (Drilling)")
    print("=" * 70)
    
    billet = Damascus3DBillet(width=60.0, length=80.0)
    billet.create_simple_layers(num_layers=25, white_thickness=0.8, black_thickness=0.8)
    
    print("\nStep 1: Original billet")
    billet.visualize("Raindrop Damascus - Step 1: Original Billet")
    
    print("\nStep 2: Drill holes in pattern")
    # Create a grid of holes (3x3)
    hole_positions = [
        (-15, -20), (0, -20), (15, -20),
        (-15, 0), (0, 0), (15, 0),
        (-15, 20), (0, 20), (15, 20)
    ]
    
    logger.info(f"Drilling {len(hole_positions)} holes in grid pattern")
    for hole_idx, (x_pos, z_pos) in enumerate(hole_positions):
        logger.debug(f"  Hole {hole_idx+1}/{len(hole_positions)}: ({x_pos}, {z_pos})")
        billet.drill_hole(x_pos=x_pos, z_pos=z_pos, radius=6.0, debug=(hole_idx == 0))  # Debug first hole only
    
    billet.visualize("Raindrop Damascus - Step 2: After Drilling Holes")
    
    print("\nStep 3: Compress to close holes and create raindrops")
    billet.apply_compression(compression_factor=0.5, debug=True)
    billet.visualize("Raindrop Damascus - Step 3: After Compression")
    
    print("\nStep 4: Extract cross-section")
    cross_section = billet.extract_cross_section(z_slice=0.0, resolution=800, debug=True)
    
    plt.figure(figsize=(12, 8))
    plt.imshow(cross_section, cmap='gray', vmin=0, vmax=255)
    plt.title('Raindrop Damascus - Cross-Section View', fontsize=14, fontweight='bold')
    plt.xlabel('Width', fontsize=10)
    plt.ylabel('Height (layers)', fontsize=10)
    plt.tight_layout()
    plt.show()
    
    # Save outputs
    billet.save_cross_section_image(z_slice=0.0, output_path="raindrop_pattern.png", resolution=1600)
    billet.save_operation_log("raindrop_operations.json")
    
    logger.info("Raindrop Damascus demo complete")
    return billet


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    """
    Main program: Interactive demo selector.
    
    FLOW:
    ----
    1. Display menu of available demos
    2. User selects pattern type
    3. Run demo with full visualization
    4. Save debug logs and outputs
    5. Repeat or exit
    """
    logger.info("="*70)
    logger.info("MAIN PROGRAM STARTED")
    logger.info("="*70)
    
    print("=" * 70)
    print("  DAMASCUS 3D BILLET SIMULATOR - PROOF OF CONCEPT")
    print("=" * 70)
    print("\nThis is a BREAKTHROUGH approach to Damascus pattern simulation!")
    print("\nInstead of manipulating 2D pixels, we create REAL 3D layers and")
    print("apply REAL physical deformations. This is how Damascus actually works!")
    print("=" * 70)
    
    while True:
        print("\n" + "=" * 70)
        print("AVAILABLE DEMOS:")
        print("=" * 70)
        print("1. Feather Damascus (wedge split + waterfall)")
        print("2. Ladder/Twist Damascus (torsional twist)")
        print("3. Raindrop Damascus (drilling + compression)")
        print("4. Exit")
        print("=" * 70)
        
        choice = input("\nSelect demo (1-4): ").strip()
        logger.info(f"User selected option: {choice}")
        
        if choice == '1':
            demo_feather_pattern()
        elif choice == '2':
            demo_twist_pattern()
        elif choice == '3':
            demo_raindrop_pattern()
        elif choice == '4':
            print("\n" + "=" * 70)
            print("  PROOF OF CONCEPT COMPLETE!")
            print("=" * 70)
            print("\nNext steps:")
            print("  - Refine mesh resolution for smoother deformations")
            print("  - Implement as-rigid-as-possible deformation")
            print("  - Add material property-based physics")
            print("  - Improve cross-section extraction algorithm")
            print("  - Build full interactive UI")
            print("  - Add animation timeline system")
            print("=" * 70)
            logger.info("User exited program")
            logger.info("="*70)
            logger.info("PROGRAM TERMINATED")
            logger.info("="*70)
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")
            logger.warning(f"Invalid menu choice: {choice}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("FATAL ERROR in main program:")
        print(f"\nFATAL ERROR: {e}")
        print("Check the debug log file for details.")
        sys.exit(1)
