# Feather Pattern Physics Implementation

## Overview
The feather pattern in the Damascus Pattern Simulator uses proper materials science and stress-strain analysis to simulate the plastic deformation that occurs when a layered steel billet is compressed through a wedge during forging.

## Real-World Forging Process

1. **Setup**: Layered billet (alternating high-carbon and high-nickel steel) sits on a rising hydraulic plate
2. **Wedge**: A dull wedge (rounded tip, not sharp) is fixed above the billet
3. **Compression**: The plate pushes the billet UP through the stationary wedge
4. **Deformation**: The wedge compresses the material, causing plastic flow
5. **Result**: Creates characteristic feather pattern with central vein and angled barbs

## Physics Implementation

### 1. Stress-Strain Analysis

**Stress Calculation (σ = F/A)**
```
stress = Force / Contact_Area

Where:
- Force = 50,000 units (hydraulic press force)
- Contact_Area = wedge_width × depth
- Stress varies with position:
  * Maximum at vein center
  * Decreases toward wedge edges
  * Exponential decay outside wedge zone
```

**Wedge Geometry**
```
wedge_tip_width = 20 pixels (narrow at top)
wedge_base_width = 60 pixels (wide at bottom)
wedge_width(y) = tip + (y/height) × (base - tip)

This creates:
- Less compression at top (thin tip)
- More compression at bottom (wide base)
```

### 2. Laminate Theory

Each layer has different material properties:

**White Layers (High-Nickel Steel)**
- Young's Modulus: E₁ = 200 GPa
- Yield Strength: σ_yield = 300 MPa
- Characteristics: Softer, more ductile, deforms more easily

**Black Layers (High-Carbon Steel)**
- Young's Modulus: E₂ = 210 GPa  
- Yield Strength: σ_yield = 450 MPa
- Characteristics: Harder, less ductile, resists deformation

The simulator:
1. Detects layer type by pixel brightness (brightness > 127 = white layer)
2. Applies appropriate material properties
3. Calculates deformation separately for each layer
4. Composites results to show realistic flow patterns

### 3. Strain Calculation

**Plastic Deformation (when σ > σ_yield)**
```python
strain = (stress - yield_strength) / Young's_modulus
ε = (σ - σ_yield) / E
```
This is permanent deformation that remains after force is removed.

**Elastic Deformation (when σ ≤ σ_yield)**
```python
strain = stress / Young's_modulus
ε = σ / E  (Hooke's Law)
```
This is temporary deformation that would spring back.

### 4. Displacement Calculation

**Vertical Displacement (Downward Flow)**
```python
vertical_displacement = strain × 80 × wedge_progress

Where:
- Stronger at bottom (wedge_progress → 1)
- Weaker at top (wedge_progress → 0)
- Material is pushed down by wedge compression
```

**Horizontal Displacement (Barb Formation)**
```python
# Inside vein (distance < wedge_half_width):
horizontal_displacement = 0  # Minimal lateral flow

# Outside vein (distance > wedge_half_width):
barb_angle = wedge_angle + (wedge_progress × 0.3)
horizontal_displacement = side × strain × 40 × cos(barb_angle)
vertical_displacement += strain × 50 × sin(barb_angle)

Where:
- side = ±1 (left or right of vein)
- Barb angle increases toward bottom
- Creates characteristic angled flow lines
```

### 5. Central Vein Visibility

The vein is made visible by darkening the high-stress compression zone:

```python
if inside_vein:
    vein_factor = 0.85 - (stress_ratio × 0.15)
    color = color × vein_factor  # Darken by 15-30%
```

This simulates:
- Surface compression marks
- Grain refinement under stress
- Visual indicator of the compression zone

## Pattern Characteristics

The physics-based approach creates:

1. **Central Vein (Rachis)**
   - Visible vertical line down center
   - Width varies: narrow at top, wider at bottom
   - Darkened to show compression zone

2. **Angled Barbs**
   - Flow lines extend from vein at angles
   - Angle increases toward bottom
   - More pronounced in softer (white) layers

3. **Layered Flow**
   - White layers deform more (lower yield strength)
   - Black layers deform less (higher yield strength)
   - Creates organic, realistic patterns

4. **Gradient Effects**
   - Stress decreases away from vein
   - Exponential decay creates smooth transitions
   - Natural-looking feather appearance

## Comparison to Previous Implementation

**Old Implementation (Arbitrary)**
- Used sine waves and "turbulence"
- No material properties
- No stress-strain analysis
- Result: Generic wavy pattern without clear vein

**New Implementation (Physics-Based)**
- Proper σ = F/A stress calculation
- Laminate theory with different layer properties
- Yield strength and plastic deformation
- Result: Realistic feather with visible vein and barbs

## Future Enhancements

Potential improvements:
1. Add temperature-dependent properties (hot vs cold forging)
2. Implement work hardening (material gets harder as it deforms)
3. Add anisotropic flow (different flow in different directions)
4. Grain boundary effects between layers
5. User-adjustable wedge angle and force parameters

## References

- Materials Science: Stress-strain curves for steel alloys
- Laminate Theory: Composite material deformation
- Hooke's Law: σ = E·ε (elastic deformation)
- Plastic Flow: ε = (σ - σ_yield) / E (plastic deformation)
- Damascus Steel Forging: Traditional bladesmithing techniques

---

**Last Updated**: January 30, 2026  
**Simulator Version**: 1.3+  
**Implementation**: `create_feather_pattern()` method in `damascus_simulator.py`
