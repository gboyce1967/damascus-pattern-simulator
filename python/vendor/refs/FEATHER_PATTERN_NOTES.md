# Feather Pattern Physics - Key Insights

## The Problem with Current Approach
The current implementation applies a displacement field to horizontal layers, trying to pull them down and inward. But this doesn't create the proper feather pattern because:

1. **Horizontal layers have no "ends"** - they run across the full width
2. Pulling them inward just compresses/stretches them
3. There's no way for layer ENDS to meet at the center vein

## What Actually Happens in Real Forging

### Step 1: Wedge Splitting
- Wedge pushes down through horizontal layers
- Creates V-shaped split (wider at top, narrower at bottom) 
- Layers are pulled down and stretched
- **Result: Two separate halves with exposed/stretched layer ends**

### Step 2: Closing the Split
- The wedge created a GAP between the halves
- The wedge is ANGLED (not perpendicular)
- Top of split is wider than bottom
- To forge-weld back together, halves must be ROTATED inward
- This rotation closes the wedge gap
- **Layer ends now meet at the center vein**

### Step 3: Side Effect of Rotation
- When halves rotate inward to close the gap
- Outer edges angle outward (non-parallel)
- Creates the characteristic feather shape

## What Needs to be Implemented

1. **Deform with wedge**: Apply vertical stretch to layers (downward pull strongest at split line)
2. **Split**: Literally separate into two halves
3. **Rotate/Shear**: Apply transformation to close the wedge angle
4. **Rejoin**: Put halves back together with layer ends meeting at vein

The key missing piece: **The rotation/shear transformation that closes the wedge gap**

Without this rotation, the two halves just sit apart with a gap between them (which is what we're seeing).
