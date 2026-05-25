# Material Field Requirements

## Purpose
This application is meant to help smiths predict how Damascus patterns evolve through real forging workflows. The visual result must not be surface-only eye candy. The internal pattern must be generated and preserved through the full billet volume so later operations can expose it.

## Non-Negotiable Rules
- Treat a forge-welded billet as one continuous steel body with an internal material/layer field, not as independent physical layer slabs after welding.
- Generate and preserve the pattern through the full billet volume. Later operations can expose interior material through cutting, grinding, compression, forging, stacking, forge-welding, or blade shaping.
- Every forging operation that moves steel must also advect/update the material field using the same displacement/deformation model. Geometry and material coordinates must stay coupled.
- Viewport colors, end faces, cross-sections, grind faces, cut faces, and exported pattern previews must sample the same internal material field.
- Do not create separate decorative patterns for caps, skins, side surfaces, or end faces.
- Avoid fixes that merely hide internal geometry or make the outside look correct while leaving the interior material state wrong.
- When there is a conflict between visual appearance and physically meaningful material displacement, prioritize the material displacement model and explain the tradeoff before changing visuals.

## Twist-Specific Rule
For Twist, the exposed end pattern is a cut plane through the twisted internal material field after the smith trims the malformed end. Do not generate a special end-cap pattern that is independent of the through-volume field.

## Future Workflow Requirements
Future workflows must support material-field preservation across cut/stack/forge-weld sequences, including multi-bar patterns such as Turkish twist with alternating left- and right-hand twisted bars.

Example Turkish twist workflow that the architecture must eventually support:
1. Stack layers.
2. Forge-weld layers into one continuous billet.
3. Draw the billet to a square bar.
4. Compress/chamfer corners.
5. Cut the bar into multiple pieces.
6. Twist some bars left-hand and some bars right-hand.
7. Grind twisted bars back to square.
8. Stack alternating right/left twist bars.
9. Forge-weld into a composite billet.
10. Forge into a knife shape.
11. Grind to expose the final pattern.

Each cut piece must carry its own material-field transform. Stacking should create a composite field with per-piece placement transforms. Forge-welding should fuse the composite into a new continuous billet body while preserving the material coordinates inside each region.

## Transitional Compatibility
Existing per-layer meshes may temporarily remain as legacy geometry carriers or sources of initial layer intervals. They must not be treated as the final material truth after forge welding. Any compatibility layer must clearly state that material coordinates are the future source of truth.
