# Deformation Formulas and Material Coordinates

## Purpose
Use these definitions when designing or changing forging operations. They are architectural requirements, not merely comments.

## Coordinate Definitions
- **Current position**: `x = [X, Y, Z]` is a point in the billet after some operations.
- **Reference/material coordinate**: `X0 = [X0, Y0, Z0]` is where that same material point came from in the original billet/layer stack.
- **Current material sampler**: `M_current(p)` returns the material/layer/color at current point `p`.
- **Reference material sampler**: `M0(X0)` returns the material/layer/color from the original billet stack.

## Displacement and Material Advection
- **Displacement field**: every forging operation should be represented as `x' = Φ(x) = x + u(x)`, where `u(x)` is the operation’s displacement vector.
- **Material advection**: if steel moves by `Φ`, the material field moves with it: `M'(Φ(x)) = M(x)`.
- **Inverse sampling**: to color or classify a current point `p`, sample by inverse mapping: `M_current(p) = M0(Φ1^-1 ∘ Φ2^-1 ∘ ... ∘ Φn^-1(p))`.
- **Operation composition**: a workflow is a chain of deformation maps. Do not replace the pattern after each operation; compose the maps so later cuts/grinds expose the accumulated internal material history.
- **Plasticized deformation**: hot forged steel is approximated as continuous plastic flow. The mesh is only a geometric carrier for the body; material coordinates must be advected through the same flow so internal layers bend, stretch, compress, twist, and stack with the steel.

## Conservation Rules
- Unless modeling material loss from cutting, grinding, or drilling, plastic forging should approximately preserve volume: `det(∂Φ/∂x) ≈ 1`.
- For simple scale operations, preserve volume with `sx * sy * sz ≈ 1`.
- For target cross-section area `A_target`, use `L_final = V_initial / A_target`.
- For a square bar of side `s`, use `A_target = s^2`.
- For an octagon from square side `s` and chamfer fraction `c`, use `A_octagon = s^2 * (1 - c^2 / 2)` and `L_final = V_initial / A_octagon`.

## Compression With Lateral Flow
For height compression factor `k`, current implementation uses lateral flow `sqrt(1 / k)`:
- `X' = Cx + (X - Cx) * sqrt(1 / k)`
- `Y' = Cy + (Y - Cy) * sqrt(1 / k)`
- `Z' = Cz + (Z - Cz) * k`

Material coordinates must move through the same compression field.

## Twist Mapping
For a length-axis twist:
- Normalize position along the bar: `t = (Y - Y_min) / span_Y`.
- Rotation angle along length: `θ(Y) = θ_total * t`.
- Twist axial shortening: `Y' = Cy + (Y - Cy) * axial_scale`, where `axial_scale = 1 - axial_shortening`.

With relative cross-section coordinates after any plastic round-bar flow:
- `X' = X_flow * cos(θ) - Z_flow * sin(θ) + Cx`
- `Z' = X_flow * sin(θ) + Z_flow * cos(θ) + Cz`

Current round-bar approximation:
- `r_rect = max(abs(X_rel / half_X), abs(Z_rel / half_Z))`
- `target_round_radius ≈ sqrt((span_X * span_Z / axial_scale) / π)`

## Smoothstep
Where gradual forging influence is needed, use `smoothstep(v) = v^2 * (3 - 2v)` with `v` clamped to `0..1`.

## Cut, Grind, and Cross-Section Rule
A cut, grind, or cross-section creates new exposed geometry. It must not create a new pattern. Its colors/patterns come only from sampling the existing through-volume material field at that exposed surface.

## Validation Invariant
When adding or modifying operations, validate both geometry displacement and material-field displacement. A visually plausible mesh is not sufficient if sampled interior material coordinates are wrong.
