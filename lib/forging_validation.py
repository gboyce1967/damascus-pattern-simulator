"""
Forging Validation Helpers
==========================

Reusable validation checks for displacement-first forging operations.

The helpers in this module are intentionally lightweight and deterministic:
they build sample billets, run one operation per fresh billet, and check for
finite vertices, degenerate triangles, expected operation history, optional
volume-frame conservation, and octagon envelope/central-flatness constraints.
"""

from __future__ import annotations

from contextlib import nullcontext, redirect_stdout
from dataclasses import asdict, dataclass, field
from io import StringIO
from typing import Callable

import numpy as np


@dataclass
class GeometrySummary:
    """Geometry metrics collected before or after an operation."""

    span: tuple[float, float, float]
    center: tuple[float, float, float]
    frame_volume: float
    vertices: int
    triangles: int
    degenerate_triangles: int
    finite_vertices: bool


@dataclass
class OperationValidationResult:
    """Validation result for one forging operation."""

    name: str
    passed: bool
    issues: list[str] = field(default_factory=list)
    before: GeometrySummary | None = None
    after: GeometrySummary | None = None
    frame_volume_ratio: float | None = None
    affected_vertices: int | None = None
    max_displacement: float | None = None
    octagon_envelope_outside_vertices: int | None = None
    octagon_z_outside_vertices: int | None = None
    octagon_central_flatness_failures: int | None = None
    octagon_max_central_z_spread: float | None = None
    length_ratio: float | None = None
    cross_section_aspect_ratio: float | None = None
    render_mesh_count: int | None = None
    render_material_count: int | None = None
    render_vertex_count: int | None = None
    render_triangle_count: int | None = None
    render_finite_vertices: bool | None = None
    render_degenerate_triangles: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def create_validation_billet(
    *,
    width: float = 40.0,
    length: float = 80.0,
    num_layers: int = 12,
    white_thickness: float = 1.0,
    black_thickness: float = 1.0,
):
    """Create a small representative billet for automated validation."""
    from lib.damascus_billet import Damascus3DBillet

    billet = Damascus3DBillet(width=width, length=length)
    billet.create_simple_layers(
        num_layers=num_layers,
        white_thickness=white_thickness,
        black_thickness=black_thickness,
    )
    return billet


def summarize_billet_geometry(billet) -> GeometrySummary:
    """Collect basic geometry health metrics for a billet."""
    from lib.forging_displacement import count_degenerate_triangles
    from lib.forging_utils import compute_billet_frame

    frame = compute_billet_frame(billet)
    total_vertices = 0
    total_triangles = 0
    degenerate_triangles = 0
    finite_vertices = True

    for layer in billet.layers:
        vertices = np.asarray(layer.mesh.vertices)
        triangles = np.asarray(layer.mesh.triangles)
        total_vertices += int(len(vertices))
        total_triangles += int(len(triangles))
        finite_vertices = finite_vertices and bool(np.isfinite(vertices).all())
        degenerate_triangles += count_degenerate_triangles(vertices, triangles)

    return GeometrySummary(
        span=(float(frame.span_x), float(frame.span_y), float(frame.span_z)),
        center=(float(frame.center_x), float(frame.center_y), float(frame.center_z)),
        frame_volume=float(frame.span_x * frame.span_y * frame.span_z),
        vertices=total_vertices,
        triangles=total_triangles,
        degenerate_triangles=int(degenerate_triangles),
        finite_vertices=bool(finite_vertices),
    )


def validate_basic_geometry(summary: GeometrySummary) -> list[str]:
    """Return issues found in a geometry summary."""
    issues: list[str] = []

    if summary.vertices <= 0:
        issues.append("no vertices found")
    if summary.triangles <= 0:
        issues.append("no triangles found")
    if not summary.finite_vertices:
        issues.append("non-finite vertex coordinates found")
    if summary.degenerate_triangles != 0:
        issues.append(f"{summary.degenerate_triangles} degenerate triangles found")
    if any(span <= 0.0 for span in summary.span):
        issues.append(f"non-positive billet span found: {summary.span}")

    return issues


def validate_octagon_envelope(
    billet,
    *,
    target_bar_size: float,
    chamfer_percent: float,
    tolerance: float = 1e-6,
) -> tuple[int, int]:
    """
    Count vertices outside the expected octagon X/Z envelope.

    Returns:
        Tuple of (outside_x_envelope_count, outside_z_bounds_count).
    """
    from lib.forging_displacement import octagon_width_at_z_array
    from lib.forging_utils import compute_billet_frame

    frame = compute_billet_frame(billet)
    hw = target_bar_size / 2.0
    hh = target_bar_size / 2.0
    c = float(np.clip(chamfer_percent / 100.0, 0.01, 0.95))

    outside_x = 0
    outside_z = 0
    for layer in billet.layers:
        vertices = np.asarray(layer.mesh.vertices)
        x = vertices[:, 0] - frame.center_x
        z = vertices[:, 2] - frame.center_z
        allowed_x = octagon_width_at_z_array(z, hw, hh, c)
        outside_x += int(np.count_nonzero(np.abs(x) > allowed_x + tolerance))
        outside_z += int(np.count_nonzero(np.abs(z) > hh + tolerance))

    return outside_x, outside_z


def validate_octagon_central_flatness(
    billet,
    *,
    chamfer_percent: float,
    samples_x: int = 17,
    tolerance: float = 1e-6,
) -> tuple[int, float]:
    """
    Check that central-band rows in generated octagon layer meshes stay flat.

    This relies on the structured vertex layout produced by
    `build_octagon_layer_mesh()`: each row contains `samples_x` vertices.
    """
    from lib.forging_utils import compute_billet_frame

    frame = compute_billet_frame(billet)
    c = float(np.clip(chamfer_percent / 100.0, 0.01, 0.95))
    central_limit = (1.0 - c) * frame.span_x / 2.0
    failures = 0
    max_spread = 0.0

    for layer in billet.layers:
        vertices = np.asarray(layer.mesh.vertices)
        if len(vertices) == 0 or len(vertices) % samples_x != 0:
            continue

        row_count = len(vertices) // samples_x
        for row_index in range(row_count):
            row = vertices[row_index * samples_x:(row_index + 1) * samples_x]
            x = row[:, 0] - frame.center_x
            central_mask = np.abs(x) <= central_limit + tolerance
            if int(np.count_nonzero(central_mask)) < 2:
                continue

            z_values = row[central_mask, 2]
            spread = float(z_values.max() - z_values.min())
            max_spread = max(max_spread, spread)
            if spread > tolerance:
                failures += 1

    return failures, max_spread


def validate_twist_visible_surface(billet) -> tuple[dict[str, int | bool], list[str]]:
    """Validate fused visible-surface render geometry for a twisted billet."""
    from lib.forging_displacement import count_degenerate_triangles
    from lib.forging_visible_surface import build_twist_visible_surface_layers

    issues: list[str] = []
    try:
        render_layers = build_twist_visible_surface_layers(
            billet,
            circumference_segments=48,
            length_segments=144,
            radial_segments=6,
        )
    except Exception as exc:
        return {
            "render_mesh_count": 0,
            "render_material_count": 0,
            "render_vertex_count": 0,
            "render_triangle_count": 0,
            "render_finite_vertices": False,
            "render_degenerate_triangles": 0,
        }, [f"twist visible surface generation failed: {type(exc).__name__}: {exc}"]

    render_mesh_count = len(render_layers)
    render_material_count = 0
    render_vertex_count = 0
    render_triangle_count = 0
    render_finite_vertices = True
    render_degenerate_triangles = 0
    colors: set[tuple[float, float, float]] = set()

    for layer in render_layers:
        vertices = np.asarray(layer.get("vertices", []), dtype=np.float64).reshape((-1, 3))
        triangles = np.asarray(layer.get("triangles", []), dtype=np.int64).reshape((-1, 3))
        if len(vertices) and len(triangles):
            render_material_count += 1
            color = layer.get("color", [])
            if isinstance(color, (list, tuple)) and len(color) == 3:
                colors.add((float(color[0]), float(color[1]), float(color[2])))
        render_vertex_count += int(len(vertices))
        render_triangle_count += int(len(triangles))
        render_finite_vertices = render_finite_vertices and bool(np.isfinite(vertices).all())
        if len(vertices) and len(triangles):
            render_degenerate_triangles += count_degenerate_triangles(vertices, triangles)

    if render_mesh_count <= 0:
        issues.append("twist visible surface generated no render meshes")
    if render_mesh_count > 4:
        issues.append(
            f"twist visible surface generated {render_mesh_count} render meshes; "
            "expected material-color groups, not one mesh per physical layer"
        )
    if render_material_count < 2 or len(colors) < 2:
        issues.append("twist visible surface did not expose at least two material colors")
    if render_vertex_count <= 0:
        issues.append("twist visible surface generated no vertices")
    if render_triangle_count <= 0:
        issues.append("twist visible surface generated no triangles")
    if not render_finite_vertices:
        issues.append("twist visible surface has non-finite vertex coordinates")
    if render_degenerate_triangles:
        issues.append(f"twist visible surface has {render_degenerate_triangles} degenerate triangles")

    return {
        "render_mesh_count": int(render_mesh_count),
        "render_material_count": int(render_material_count),
        "render_vertex_count": int(render_vertex_count),
        "render_triangle_count": int(render_triangle_count),
        "render_finite_vertices": bool(render_finite_vertices),
        "render_degenerate_triangles": int(render_degenerate_triangles),
    }, issues


def _latest_displacement_stats(billet) -> dict | None:
    if not billet.operation_history:
        return None
    latest = billet.operation_history[-1]
    stats = latest.get("displacement_stats")
    return stats if isinstance(stats, dict) else None


def _run_operation(
    operation: Callable[[object], None],
    billet,
    *,
    quiet: bool,
) -> None:
    stream = StringIO()
    context = redirect_stdout(stream) if quiet else nullcontext()
    with context:
        operation(billet)


def _create_case_billet(*, quiet: bool):
    stream = StringIO()
    context = redirect_stdout(stream) if quiet else nullcontext()
    with context:
        return create_validation_billet()


def validate_operation_case(
    *,
    name: str,
    operation: Callable[[object], None],
    expected_operation: str,
    required_parameters: tuple[str, ...] = (),
    require_length_shortening: bool = False,
    require_width_reduction: bool = False,
    require_height_growth: bool = False,
    max_length_ratio: float | None = None,
    max_cross_section_aspect_ratio: float | None = None,
    require_twist_visible_surface: bool = False,
    volume_ratio_range: tuple[float, float] | None = None,
    octagon: dict | None = None,
    quiet: bool = True,
) -> OperationValidationResult:
    """Run one operation on a fresh billet and validate the result."""
    result = OperationValidationResult(name=name, passed=False)

    try:
        billet = _create_case_billet(quiet=quiet)
        result.before = summarize_billet_geometry(billet)
        _run_operation(operation, billet, quiet=quiet)
        result.after = summarize_billet_geometry(billet)
    except Exception as exc:
        result.issues.append(f"operation raised {type(exc).__name__}: {exc}")
        return result

    result.issues.extend(validate_basic_geometry(result.after))

    if result.before and result.after and result.before.frame_volume > 1e-9:
        result.frame_volume_ratio = result.after.frame_volume / result.before.frame_volume
    if result.before and result.after and result.before.span[1] > 1e-9:
        result.length_ratio = result.after.span[1] / result.before.span[1]

    latest_history = billet.operation_history[-1] if billet.operation_history else {}
    latest_operation = latest_history.get("operation")
    if latest_operation != expected_operation:
        result.issues.append(
            f"latest operation history entry was {latest_operation!r}, expected {expected_operation!r}"
        )
    latest_parameters = latest_history.get("parameters") if isinstance(latest_history, dict) else None
    if required_parameters:
        if not isinstance(latest_parameters, dict):
            result.issues.append("latest operation history entry has no parameters dict")
        else:
            missing_parameters = [
                parameter
                for parameter in required_parameters
                if parameter not in latest_parameters
            ]
            if missing_parameters:
                result.issues.append(f"missing operation parameters: {', '.join(missing_parameters)}")

    if result.before and result.after:
        if require_length_shortening and not result.after.span[1] < result.before.span[1]:
            result.issues.append(
                f"length did not shorten: before={result.before.span[1]:.6f}, after={result.after.span[1]:.6f}"
            )
        if max_length_ratio is not None and result.length_ratio is not None:
            if result.length_ratio > max_length_ratio:
                result.issues.append(
                    f"length ratio is still too coarse for twist compression: "
                    f"{result.length_ratio:.6f}, expected <= {max_length_ratio:.3f}"
                )
        if require_width_reduction and not result.after.span[0] < result.before.span[0]:
            result.issues.append(
                f"width did not reduce toward round bar: before={result.before.span[0]:.6f}, after={result.after.span[0]:.6f}"
            )
        if require_height_growth and not result.after.span[2] > result.before.span[2]:
            result.issues.append(
                f"height did not grow toward round bar: before={result.before.span[2]:.6f}, after={result.after.span[2]:.6f}"
            )
        if max_cross_section_aspect_ratio is not None:
            cross_section_min = min(result.after.span[0], result.after.span[2])
            cross_section_max = max(result.after.span[0], result.after.span[2])
            if cross_section_min > 1e-9:
                result.cross_section_aspect_ratio = cross_section_max / cross_section_min
                if result.cross_section_aspect_ratio > max_cross_section_aspect_ratio:
                    result.issues.append(
                        f"cross-section is still too flat for a round bar: "
                        f"aspect={result.cross_section_aspect_ratio:.6f}, "
                        f"expected <= {max_cross_section_aspect_ratio:.3f}"
                    )
            else:
                result.issues.append("cross-section aspect ratio could not be computed")

    stats = _latest_displacement_stats(billet)
    if stats:
        result.affected_vertices = int(stats.get("affected_vertices", 0))
        result.max_displacement = float(stats.get("max_displacement", 0.0))
        if result.affected_vertices <= 0:
            result.issues.append("operation recorded zero affected vertices")
        if result.max_displacement <= 0.0:
            result.issues.append("operation recorded zero max displacement")

    if volume_ratio_range and result.frame_volume_ratio is not None:
        lo, hi = volume_ratio_range
        if not (lo <= result.frame_volume_ratio <= hi):
            result.issues.append(
                f"frame volume ratio {result.frame_volume_ratio:.6f} outside expected range {lo:.3f}..{hi:.3f}"
            )

    if octagon:
        outside_x, outside_z = validate_octagon_envelope(billet, **octagon)
        flat_failures, max_spread = validate_octagon_central_flatness(
            billet,
            chamfer_percent=float(octagon["chamfer_percent"]),
        )
        result.octagon_envelope_outside_vertices = outside_x
        result.octagon_z_outside_vertices = outside_z
        result.octagon_central_flatness_failures = flat_failures
        result.octagon_max_central_z_spread = max_spread

        if outside_x:
            result.issues.append(f"{outside_x} octagon vertices outside X envelope")
        if outside_z:
            result.issues.append(f"{outside_z} octagon vertices outside Z bounds")
        if flat_failures:
            result.issues.append(
                f"{flat_failures} octagon central rows are not flat; max spread={max_spread:.8f}"
            )

    if require_twist_visible_surface:
        render_summary, render_issues = validate_twist_visible_surface(billet)
        result.render_mesh_count = int(render_summary["render_mesh_count"])
        result.render_material_count = int(render_summary["render_material_count"])
        result.render_vertex_count = int(render_summary["render_vertex_count"])
        result.render_triangle_count = int(render_summary["render_triangle_count"])
        result.render_finite_vertices = bool(render_summary["render_finite_vertices"])
        result.render_degenerate_triangles = int(render_summary["render_degenerate_triangles"])
        result.issues.extend(render_issues)

    result.passed = not result.issues
    return result


def run_displacement_validation_suite(*, quiet: bool = True) -> list[OperationValidationResult]:
    """Run the standard displacement-first forging validation suite."""
    from python.engine.forge_ops import (
        apply_compression_safe,
        apply_twist_safe,
        apply_wedge_safe,
        drill_hole_safe,
        forge_to_octagon_safe,
        forge_to_square_safe,
    )

    octagon_target = 15.0
    octagon_chamfer = 45.0

    cases = [
        {
            "name": "forge_square",
            "operation": lambda billet: forge_to_square_safe(
                billet,
                target_bar_size=15.0,
                num_heats=5,
            ),
            "expected_operation": "forge_square",
            "volume_ratio_range": (0.995, 1.005),
        },
        {
            "name": "forge_octagon_45",
            "operation": lambda billet: forge_to_octagon_safe(
                billet,
                target_bar_size=octagon_target,
                num_heats=5,
                chamfer_percent=octagon_chamfer,
            ),
            "expected_operation": "forge_octagon",
            "octagon": {
                "target_bar_size": octagon_target,
                "chamfer_percent": octagon_chamfer,
            },
        },
        {
            "name": "compression",
            "operation": lambda billet: apply_compression_safe(
                billet,
                compression_factor=0.8,
            ),
            "expected_operation": "compression",
            "volume_ratio_range": (0.995, 1.005),
        },
        {
            "name": "twist",
            "operation": lambda billet: apply_twist_safe(
                billet,
                angle_degrees=3600.0,
            ),
            "expected_operation": "twist",
            "required_parameters": (
                "total_twists",
                "billet_length_inches",
                "twists_per_inch",
                "guideline_band",
                "standard_twists_per_inch",
                "turkish_twists_per_inch",
                "axial_scale",
                "axial_shortening",
                "roundness_factor",
                "target_round_radius",
                "source_span_x",
                "source_span_z",
                "center_y",
                "material_layers",
            ),
            "require_length_shortening": True,
            "require_height_growth": True,
            "max_length_ratio": 0.36,
            "max_cross_section_aspect_ratio": 1.12,
            "require_twist_visible_surface": True,
        },
        {
            "name": "wedge",
            "operation": lambda billet: apply_wedge_safe(
                billet,
                wedge_depth=8.0,
                wedge_angle=30.0,
                split_gap=3.0,
            ),
            "expected_operation": "wedge_deformation",
        },
        {
            "name": "drill",
            "operation": lambda billet: drill_hole_safe(
                billet,
                x_pos=20.0,
                z_pos=6.0,
                radius=4.0,
            ),
            "expected_operation": "drill_hole",
        },
    ]

    return [
        validate_operation_case(quiet=quiet, **case)
        for case in cases
    ]
