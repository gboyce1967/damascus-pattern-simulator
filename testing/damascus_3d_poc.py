#!/usr/bin/env python3
"""
3D Damascus Billet Simulator - Proof of Concept
================================================

This is a breakthrough approach to Damascus pattern simulation.
Instead of trying to deform 2D pixels, we create actual 3D layers
and apply real physical deformations.

Key Insight:
-----------
Real Damascus forging involves 3D material deformation. Trying to simulate
this with 2D pixel manipulation is fundamentally wrong. Each layer needs
to be a real 3D object that can be physically deformed.

Approach:
---------
1. Create each Damascus layer as a 3D mesh (thin rectangular plane)
2. Apply real 3D deformations (wedge displacement, twist, drill holes)
3. Visualize in full 3D (rotate, zoom, inspect)
4. Extract cross-sections for traditional pattern views

Author: Damascus Pattern Simulator Team
Date: 2026-02-01
"""

import open3d as o3d
import numpy as np
from typing import List, Tuple
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class DamascusLayer:
    """Represents a single layer in the Damascus billet as a 3D mesh."""
    
    def __init__(self, z_position: float, thickness: float, color: Tuple[float, float, float], 
                 width: float = 50.0, length: float = 100.0):
        """
        Create a Damascus layer as a 3D mesh.
        
        Args:
            z_position: Vertical position of this layer
            thickness: Thickness of the layer
            color: RGB color tuple (0-1 range) - (1,1,1) for white steel, (0.2,0.2,0.2) for black
            width: Width of the billet (default 50mm)
            length: Length of the billet (default 100mm)
        """
        self.z_position = z_position
        self.thickness = thickness
        self.color = color
        self.width = width
        self.length = length
        
        # Create the mesh as a rectangular box
        self.mesh = self._create_layer_mesh()
        
    def _create_layer_mesh(self) -> o3d.geometry.TriangleMesh:
        """Create a 3D mesh representing this layer."""
        # Create a box mesh for the layer
        mesh = o3d.geometry.TriangleMesh.create_box(
            width=self.width,
            height=self.thickness,
            depth=self.length
        )
        
        # Center it at the origin in X and Y, position it at z_position in Z
        mesh.translate([-self.width/2, self.z_position, -self.length/2])
        
        # Apply color
        mesh.paint_uniform_color(self.color)
        
        # Compute normals for proper lighting
        mesh.compute_vertex_normals()
        
        return mesh
    
    def get_mesh(self) -> o3d.geometry.TriangleMesh:
        """Get the Open3D mesh for this layer."""
        return self.mesh


class Damascus3DBillet:
    """Represents a complete Damascus billet with multiple layers."""
    
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
        
    def add_layer(self, thickness: float, is_white: bool):
        """
        Add a layer to the billet.
        
        Args:
            thickness: Thickness of layer in mm
            is_white: True for high-nickel (white) steel, False for high-carbon (black)
        """
        # Calculate z position based on existing layers
        z_pos = sum(layer.thickness for layer in self.layers)
        
        # White steel: light gray, Black steel: dark gray
        color = (0.9, 0.9, 0.9) if is_white else (0.2, 0.2, 0.2)
        
        layer = DamascusLayer(z_pos, thickness, color, self.width, self.length)
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
        self.layers = []
        for i in range(num_layers):
            is_white = (i % 2 == 0)
            thickness = white_thickness if is_white else black_thickness
            self.add_layer(thickness, is_white)
        
        print(f"Created {num_layers} layers, total height: {sum(l.thickness for l in self.layers):.1f}mm")
    
    def get_all_meshes(self) -> List[o3d.geometry.TriangleMesh]:
        """Get all layer meshes for visualization."""
        return [layer.get_mesh() for layer in self.layers]
    
    def apply_wedge_deformation(self, wedge_depth: float = 20.0, wedge_angle: float = 30.0, 
                                 split_gap: float = 5.0):
        """
        Apply wedge deformation to simulate feather Damascus.
        
        This is where the magic happens - we apply REAL 3D deformation
        to actual 3D meshes, not pixel manipulation!
        
        Physics:
        --------
        - Wedge pushes into the center, splitting the billet
        - Creates two waterfalls that flow downward and outward
        - Top layers are displaced more than bottom layers
        - The wedge angle creates non-parallel edges
        - Layers are stretched and thinned as they flow down
        
        Args:
            wedge_depth: How deep the wedge penetrates (mm)
            wedge_angle: Angle of wedge in degrees (from vertical)
            split_gap: Gap created at the split point (mm)
        """
        print(f"\nApplying wedge deformation:")
        print(f"  Depth: {wedge_depth}mm")
        print(f"  Angle: {wedge_angle}°")
        print(f"  Split gap: {split_gap}mm")
        print("This applies REAL 3D physics - each layer deforms based on its position!")
        
        center_x = 0.0  # Wedge at center
        wedge_angle_rad = np.deg2rad(wedge_angle)
        total_height = sum(l.thickness for l in self.layers)
        
        for layer_idx, layer in enumerate(self.layers):
            vertices = np.asarray(layer.mesh.vertices).copy()
            
            # Layer's normalized position (0 = bottom, 1 = top)
            layer_position_normalized = layer.z_position / total_height
            
            # For each vertex, calculate deformation
            for i, vertex in enumerate(vertices):
                x, y, z = vertex
                
                # Distance from wedge centerline
                dist_from_center = abs(x - center_x)
                
                # Which side of the wedge? (-1 = left, +1 = right)
                side = np.sign(x - center_x) if abs(x - center_x) > 0.001 else 1.0
                
                # Deformation intensity: maximum at center, falls off with distance
                # Using smooth Gaussian falloff
                sigma = self.width / 3.0  # Deformation zone width
                intensity = np.exp(-(dist_from_center**2) / (2 * sigma**2))
                
                # Vertical displacement: layers pulled down by wedge
                # Top layers displace more than bottom layers
                # Creates the "waterfall" effect
                vertical_displacement = -wedge_depth * intensity * layer_position_normalized
                
                # Horizontal displacement: wedge pushes layers outward
                # This creates the split and the waterfalls flowing down and out
                # The wedge angle determines how much horizontal spread
                horizontal_displacement = side * split_gap * intensity * layer_position_normalized
                horizontal_displacement += side * wedge_depth * np.tan(wedge_angle_rad) * intensity * layer_position_normalized
                
                # Apply the deformations
                vertices[i, 0] += horizontal_displacement  # X axis (width)
                vertices[i, 1] += vertical_displacement    # Y axis (height)
            
            # Update the mesh with deformed vertices
            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()
        
        print("Deformation complete!")
    
    def apply_twist(self, angle_degrees: float = 90.0, axis: str = 'z'):
        """
        Apply torsional twist to the billet (for ladder/twist Damascus).
        
        The twist varies along the length - one end stays fixed, the other
        end rotates by the specified angle.
        
        Args:
            angle_degrees: Total rotation angle in degrees
            axis: Axis to twist around ('z' for length axis)
        """
        print(f"\nApplying twist deformation: {angle_degrees}° around {axis}-axis")
        
        angle_rad = np.deg2rad(angle_degrees)
        
        for layer in self.layers:
            vertices = np.asarray(layer.mesh.vertices).copy()
            
            for i, vertex in enumerate(vertices):
                x, y, z = vertex
                
                # Twist varies linearly along the length
                # z = -length/2 => no twist, z = +length/2 => full twist
                normalized_position = (z + self.length/2) / self.length  # 0 to 1
                current_angle = angle_rad * normalized_position
                
                # Rotate around the center axis
                if axis == 'z':
                    # Rotate in XY plane
                    x_center = 0
                    y_center = layer.z_position + layer.thickness/2
                    
                    # Translate to origin
                    x_rel = x - x_center
                    y_rel = y - y_center
                    
                    # Rotate
                    x_new = x_rel * np.cos(current_angle) - y_rel * np.sin(current_angle)
                    y_new = x_rel * np.sin(current_angle) + y_rel * np.cos(current_angle)
                    
                    # Translate back
                    vertices[i, 0] = x_new + x_center
                    vertices[i, 1] = y_new + y_center
            
            # Update the mesh
            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()
        
        print("Twist complete!")
    
    def apply_compression(self, compression_factor: float = 0.8):
        """
        Compress the billet vertically (simulates hammering/pressing).
        
        Args:
            compression_factor: Multiply height by this factor (< 1.0 compresses)
        """
        print(f"\nApplying compression: {compression_factor:.1%} of original height")
        
        total_height = sum(l.thickness for l in self.layers)
        new_total_height = total_height * compression_factor
        scale_factor = compression_factor
        
        for layer in self.layers:
            vertices = np.asarray(layer.mesh.vertices).copy()
            
            # Compress in Y direction
            for i, vertex in enumerate(vertices):
                x, y, z = vertex
                
                # Scale Y position proportionally
                vertices[i, 1] = y * scale_factor
            
            # Update layer properties
            layer.thickness *= scale_factor
            layer.z_position *= scale_factor
            
            # Update mesh
            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()
        
        print(f"Compression complete! Height: {total_height:.1f}mm → {new_total_height:.1f}mm")
    
    def drill_hole(self, x_pos: float = 0.0, z_pos: float = 0.0, radius: float = 10.0):
        """
        Drill a hole through the billet.
        
        Layers deform around the hole, creating radial patterns.
        
        Args:
            x_pos: X position of hole center
            z_pos: Z position of hole center  
            radius: Radius of the hole
        """
        print(f"\nDrilling hole at ({x_pos:.1f}, {z_pos:.1f}) with radius {radius:.1f}mm")
        
        for layer in self.layers:
            vertices = np.asarray(layer.mesh.vertices).copy()
            
            for i, vertex in enumerate(vertices):
                x, y, z = vertex
                
                # Distance from hole center
                dx = x - x_pos
                dz = z - z_pos
                dist = np.sqrt(dx**2 + dz**2)
                
                if dist < radius * 2.0:  # Affect vertices within influence radius
                    if dist < radius:  # Inside the hole - push outward strongly
                        push_factor = 1.5
                    else:  # Outside but close - gentle push
                        # Smooth falloff
                        influence = np.exp(-((dist - radius)**2) / (2 * radius**2))
                        push_factor = influence * 0.3
                    
                    # Push radially outward
                    if dist > 0.001:  # Avoid division by zero
                        direction_x = dx / dist
                        direction_z = dz / dist
                        
                        vertices[i, 0] += direction_x * radius * push_factor
                        vertices[i, 2] += direction_z * radius * push_factor
            
            # Update mesh
            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()
        
        print("Drilling complete!")
    
    def extract_cross_section(self, z_slice: float = 0.0, resolution: int = 500) -> np.ndarray:
        """
        Extract a 2D cross-section at a specific Z position.
        
        This slices through all the 3D layers to show the traditional
        Damascus pattern view.
        
        Args:
            z_slice: Z position to slice at
            resolution: Resolution of output image (pixels per side)
        
        Returns:
            2D numpy array representing the pattern (0-255 grayscale)
        """
        print(f"\nExtracting cross-section at Z = {z_slice:.1f}mm (resolution: {resolution}px)")
        
        # Create output image
        img = np.ones((resolution, resolution)) * 255  # White background
        
        # Map from world coordinates to image pixels
        x_min, x_max = -self.width/2, self.width/2
        y_min = 0
        y_max = sum(l.thickness for l in self.layers)
        
        # For each layer, determine if it intersects this Z slice
        # and draw its contribution to the cross-section
        for layer in self.layers:
            vertices = np.asarray(layer.mesh.vertices)
            triangles = np.asarray(layer.mesh.triangles)
            
            # Check each triangle to see if it intersects the slice plane
            for tri_indices in triangles:
                tri_verts = vertices[tri_indices]
                
                # Check if triangle intersects the Z = z_slice plane
                z_coords = tri_verts[:, 2]
                
                # Triangle intersects if z_slice is between min and max z
                if z_coords.min() <= z_slice <= z_coords.max():
                    # Interpolate to find where edges intersect the plane
                    # For simplicity in POC, we'll rasterize the layer's bounds
                    
                    # Get Y range for this layer at this Z position
                    y_coords = tri_verts[:, 1]
                    x_coords = tri_verts[:, 0]
                    
                    # Convert to pixel coordinates
                    for x_val in x_coords:
                        for y_val in y_coords:
                            # Map to pixel space
                            px = int((x_val - x_min) / (x_max - x_min) * resolution)
                            py = int((y_val - y_min) / (y_max - y_min) * resolution)
                            
                            if 0 <= px < resolution and 0 <= py < resolution:
                                # Apply layer color (white=255, black=50)
                                color_val = 255 if layer.color[0] > 0.5 else 50
                                img[resolution - 1 - py, px] = color_val  # Flip Y for display
        
        print("Cross-section extracted!")
        return img.astype(np.uint8)
    
    def visualize(self, title: str = "Damascus 3D Billet", use_matplotlib: bool = True):
        """
        Visualize the billet in 3D.
        
        This opens an interactive window where you can:
        - Rotate: Left mouse drag
        - Zoom: Mouse wheel
        - Pan: Ctrl + Left mouse drag
        """
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
        """Visualize using matplotlib (more compatible with Wayland)."""
        print("Using Matplotlib 3D viewer (Wayland-compatible)")
        print("Controls:")
        print("  Rotate: Left click + drag")
        print("  Zoom: Mouse wheel (or right click + drag)")
        print("  Close window to continue")
        print("=" * 50)
        
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Draw each layer
        for layer in self.layers:
            vertices = np.asarray(layer.mesh.vertices)
            triangles = np.asarray(layer.mesh.triangles)
            
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
        ax.set_xlabel('X (width) [mm]', fontsize=10)
        ax.set_ylabel('Y (height) [mm]', fontsize=10)
        ax.set_zlabel('Z (length) [mm]', fontsize=10)
        
        # Set equal aspect ratio and limits
        max_range = max(self.width, sum(l.thickness for l in self.layers), self.length)
        mid_x = 0
        mid_y = sum(l.thickness for l in self.layers) / 2
        mid_z = 0
        ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
        ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
        ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Set initial view angle
        ax.view_init(elev=20, azim=45)
        
        plt.tight_layout()
        plt.show()


def demo_feather_pattern():
    """Demo: Feather Damascus using wedge deformation."""
    print("\n" + "=" * 70)
    print("  DEMO 1: FEATHER DAMASCUS (Wedge Split)")
    print("=" * 70)
    
    billet = Damascus3DBillet(width=50.0, length=100.0)
    billet.create_simple_layers(num_layers=30, white_thickness=0.8, black_thickness=0.8)
    
    print("\nStep 1: Original billet")
    billet.visualize("Feather Damascus - Step 1: Original Billet")
    
    print("\nStep 2: Wedge split")
    billet.apply_wedge_deformation(wedge_depth=18.0, wedge_angle=35.0, split_gap=6.0)
    billet.visualize("Feather Damascus - Step 2: After Wedge Split")
    
    print("\nStep 3: Extract cross-section to see the pattern")
    cross_section = billet.extract_cross_section(z_slice=0.0, resolution=800)
    
    # Display the cross-section
    plt.figure(figsize=(12, 8))
    plt.imshow(cross_section, cmap='gray', vmin=0, vmax=255)
    plt.title('Feather Damascus - Cross-Section View', fontsize=14, fontweight='bold')
    plt.xlabel('Width', fontsize=10)
    plt.ylabel('Height (layers)', fontsize=10)
    plt.tight_layout()
    plt.show()
    
    return billet


def demo_twist_pattern():
    """Demo: Ladder/Twist Damascus."""
    print("\n" + "=" * 70)
    print("  DEMO 2: LADDER/TWIST DAMASCUS")
    print("=" * 70)
    
    billet = Damascus3DBillet(width=40.0, length=120.0)
    billet.create_simple_layers(num_layers=24, white_thickness=1.0, black_thickness=1.0)
    
    print("\nStep 1: Original billet")
    billet.visualize("Twist Damascus - Step 1: Original Billet")
    
    print("\nStep 2: Apply twist")
    billet.apply_twist(angle_degrees=180.0)
    billet.visualize("Twist Damascus - Step 2: After 180° Twist")
    
    print("\nStep 3: Compress to consolidate")
    billet.apply_compression(compression_factor=0.7)
    billet.visualize("Twist Damascus - Step 3: After Compression")
    
    print("\nStep 4: Extract cross-section")
    cross_section = billet.extract_cross_section(z_slice=0.0, resolution=800)
    
    plt.figure(figsize=(12, 8))
    plt.imshow(cross_section, cmap='gray', vmin=0, vmax=255)
    plt.title('Ladder Damascus - Cross-Section View', fontsize=14, fontweight='bold')
    plt.xlabel('Width', fontsize=10)
    plt.ylabel('Height (layers)', fontsize=10)
    plt.tight_layout()
    plt.show()
    
    return billet


def demo_raindrop_pattern():
    """Demo: Raindrop Damascus using drilling."""
    print("\n" + "=" * 70)
    print("  DEMO 3: RAINDROP DAMASCUS (Drilling)")
    print("=" * 70)
    
    billet = Damascus3DBillet(width=60.0, length=80.0)
    billet.create_simple_layers(num_layers=25, white_thickness=0.8, black_thickness=0.8)
    
    print("\nStep 1: Original billet")
    billet.visualize("Raindrop Damascus - Step 1: Original Billet")
    
    print("\nStep 2: Drill holes in pattern")
    # Create a grid of holes
    hole_positions = [
        (-15, -20), (0, -20), (15, -20),
        (-15, 0), (0, 0), (15, 0),
        (-15, 20), (0, 20), (15, 20)
    ]
    
    for x_pos, z_pos in hole_positions:
        billet.drill_hole(x_pos=x_pos, z_pos=z_pos, radius=6.0)
    
    billet.visualize("Raindrop Damascus - Step 2: After Drilling Holes")
    
    print("\nStep 3: Compress to close holes and create raindrops")
    billet.apply_compression(compression_factor=0.5)
    billet.visualize("Raindrop Damascus - Step 3: After Compression")
    
    print("\nStep 4: Extract cross-section")
    cross_section = billet.extract_cross_section(z_slice=0.0, resolution=800)
    
    plt.figure(figsize=(12, 8))
    plt.imshow(cross_section, cmap='gray', vmin=0, vmax=255)
    plt.title('Raindrop Damascus - Cross-Section View', fontsize=14, fontweight='bold')
    plt.xlabel('Width', fontsize=10)
    plt.ylabel('Height (layers)', fontsize=10)
    plt.tight_layout()
    plt.show()
    
    return billet


def main():
    """
    Proof of Concept: 3D Damascus Simulation
    =========================================
    
    This demonstrates the fundamental breakthrough:
    Real 3D layers with real 3D physics!
    """
    
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
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
