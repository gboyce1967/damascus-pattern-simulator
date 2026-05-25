#!/usr/bin/env python3
"""
Run displacement-first forging validation checks.

Recommended:
    .venv/bin/python scripts/validate_displacement_operations.py
"""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import nullcontext, redirect_stdout
from io import StringIO
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _format_span(span: tuple[float, float, float]) -> str:
    return f"({span[0]:.3f}, {span[1]:.3f}, {span[2]:.3f})"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate displacement-first forging operation geometry.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the text summary.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show operation print output while running validations.",
    )
    args = parser.parse_args()

    output_context = nullcontext() if args.verbose else redirect_stdout(StringIO())
    try:
        with output_context:
            from lib.forging_validation import run_displacement_validation_suite

            results = run_displacement_validation_suite(quiet=not args.verbose)
    except ModuleNotFoundError as exc:
        if exc.name == "open3d":
            print(
                "Open3D is not available in this Python environment. "
                "Run with the project virtualenv, e.g. "
                ".venv/bin/python scripts/validate_displacement_operations.py",
                file=sys.stderr,
            )
            return 2
        raise

    if args.json:
        print(json.dumps([result.to_dict() for result in results], indent=2))
    else:
        print("Displacement forging validation")
        print("=" * 34)
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            after_span = _format_span(result.after.span) if result.after else "n/a"
            volume = (
                f"{result.frame_volume_ratio:.6f}"
                if result.frame_volume_ratio is not None
                else "n/a"
            )
            length = (
                f"{result.length_ratio:.6f}"
                if result.length_ratio is not None
                else "n/a"
            )
            print(
                f"[{status}] {result.name}: "
                f"span={after_span}, volume_ratio={volume}, "
                f"length_ratio={length}, "
                f"degenerate={result.after.degenerate_triangles if result.after else 'n/a'}"
                + (
                    f", cross_section_aspect={result.cross_section_aspect_ratio:.3f}"
                    if result.cross_section_aspect_ratio is not None
                    else ""
                )
                + (
                    f", render_meshes={result.render_mesh_count}, "
                    f"render_materials={result.render_material_count}, "
                    f"render_tris={result.render_triangle_count}"
                    if result.render_mesh_count is not None
                    else ""
                )
            )
            if result.octagon_envelope_outside_vertices is not None:
                print(
                    "       octagon: "
                    f"outside_x={result.octagon_envelope_outside_vertices}, "
                    f"outside_z={result.octagon_z_outside_vertices}, "
                    f"central_flat_failures={result.octagon_central_flatness_failures}, "
                    f"max_central_z_spread={result.octagon_max_central_z_spread:.8f}"
                )
            for issue in result.issues:
                print(f"       - {issue}")

        passed_count = sum(1 for result in results if result.passed)
        print("=" * 34)
        print(f"{passed_count}/{len(results)} checks passed")

    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
