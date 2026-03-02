import base64
import io
import uuid
from dataclasses import dataclass
from PIL import Image

from python.engine.serialize import serialize_layers_mesh
from python.engine.forge_ops import (
    forge_to_square_safe, forge_to_octagon_safe, apply_twist_safe,
    apply_wedge_safe, apply_compression_safe, drill_hole_safe,
    cross_section_png_safe,
)

# Import your existing simulator (copied into python/vendor/)
from python.vendor.damascus_3d_simulator import Damascus3DBillet  # type: ignore


@dataclass
class EngineSession:
    billet: Damascus3DBillet

    def stats_payload(self):
        # uses your billet stats + op history as-is
        return self.billet.get_billet_stats() | {"operation_history": self.billet.operation_history}

    def mesh_payload(self):
        height = sum(l.thickness for l in self.billet.layers)
        return {
            "session_id": "n/a",
            "dims": {
                "width_mm": float(self.billet.width),
                "length_mm": float(self.billet.length),
                "height_mm": float(height)
            },
            "layers": serialize_layers_mesh(self.billet.layers)
        }

    def apply_operation(self, op: str, payload: dict):
        if op == "wedge":
            apply_wedge_safe(
                self.billet,
                wedge_depth=float(payload.get("wedge_depth", 18.0)),
                wedge_angle=float(payload.get("wedge_angle", 35.0)),
                split_gap=float(payload.get("split_gap", 6.0))
            )
        elif op == "forge_square":
            forge_to_square_safe(
                self.billet,
                target_bar_size=float(payload.get("target_bar_size", 15.0)),
                num_heats=int(payload.get("num_heats", 5))
            )
        elif op == "forge_octagon":
            forge_to_octagon_safe(
                self.billet,
                target_bar_size=float(payload.get("target_bar_size", 15.0)),
                num_heats=int(payload.get("num_heats", 5)),
                chamfer_percent=float(payload.get("chamfer_percent", 15.0))
            )
        elif op == "twist":
            apply_twist_safe(
                self.billet,
                angle_degrees=float(payload.get("angle_degrees", 180.0))
            )
        elif op == "compression":
            apply_compression_safe(
                self.billet,
                compression_factor=float(payload.get("compression_factor", 0.8))
            )
        elif op == "drill":
            drill_hole_safe(
                self.billet,
                x_pos=float(payload.get("x_pos", 0.0)),
                z_pos=float(payload.get("z_pos", 0.0)),
                radius=float(payload.get("radius", 10.0))
            )
        else:
            raise ValueError(f"Unknown op: {op}")
        return {"ok": True, "op": op}

    def cross_section_png(self, y_slice: float, resolution: int):
        png_bytes = cross_section_png_safe(self.billet, y_slice=y_slice, resolution=resolution)
        return {"png_base64": base64.b64encode(png_bytes).decode("utf-8")}

    def export_model(self, path: str, merge_layers: bool = True):
        # Uses your built-in exporter
        self.billet.export_3d_model(path, merge_layers=merge_layers)


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, EngineSession] = {}

    def create(self, width: float, length: float, num_layers: int, white_thickness: float, black_thickness: float) -> str:
        billet = Damascus3DBillet(width=width, length=length)
        billet.create_simple_layers(num_layers=num_layers, white_thickness=white_thickness, black_thickness=black_thickness)

        sid = str(uuid.uuid4())
        self._sessions[sid] = EngineSession(billet=billet)
        return sid

    def get(self, sid: str) -> EngineSession | None:
        s = self._sessions.get(sid)
        if not s:
            return None

        # Patch session_id into payloads without mutating the billet itself
        original_mesh_payload = s.mesh_payload
        def mesh_payload_with_id():
          p = original_mesh_payload()
          p["session_id"] = sid
          return p
        s.mesh_payload = mesh_payload_with_id  # type: ignore

        return s
