import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from python.engine.session import SessionManager
from python.engine.reference import ReferenceStore

app = FastAPI()
sessions = SessionManager()
refs = ReferenceStore()

class CreateSessionReq(BaseModel):
    width_mm: float = 50.0
    length_mm: float = 100.0
    num_layers: int = 30
    white_thickness_mm: float = 0.8
    black_thickness_mm: float = 0.8

@app.get("/health")
def health():
    return {"ok": True, "engine": "damascus-python", "port": int(os.getenv("DAMASCUS_ENGINE_PORT", "0"))}

@app.post("/sessions")
def create_session(req: CreateSessionReq):
    sid = sessions.create(
        width=req.width_mm,
        length=req.length_mm,
        num_layers=req.num_layers,
        white_thickness=req.white_thickness_mm,
        black_thickness=req.black_thickness_mm
    )
    return {"session_id": sid}

@app.get("/sessions/{sid}/mesh")
def mesh(sid: str):
    s = sessions.get(sid)
    if not s:
        raise HTTPException(404, "Unknown session")
    return s.mesh_payload()

@app.get("/sessions/{sid}/stats")
def stats(sid: str):
    s = sessions.get(sid)
    if not s:
        raise HTTPException(404, "Unknown session")
    return s.stats_payload()

@app.post("/sessions/{sid}/op/{op}")
def op(sid: str, op: str, payload: dict):
    s = sessions.get(sid)
    if not s:
        raise HTTPException(404, "Unknown session")
    return s.apply_operation(op, payload or {})

@app.post("/sessions/{sid}/cross_section")
def cross_section(sid: str, payload: dict):
    s = sessions.get(sid)
    if not s:
        raise HTTPException(404, "Unknown session")
    y_slice = float(payload.get("y_slice", 0.0))
    res = int(payload.get("resolution", 700))
    return s.cross_section_png(y_slice=y_slice, resolution=res)

@app.post("/sessions/{sid}/export/model")
def export_model(sid: str, payload: dict):
    s = sessions.get(sid)
    if not s:
        raise HTTPException(404, "Unknown session")
    path = payload.get("path")
    if not path:
        raise HTTPException(400, "Missing path")
    merge_layers = bool(payload.get("merge_layers", True))
    s.export_model(path, merge_layers=merge_layers)
    return {"ok": True, "path": path}

@app.get("/reference/list")
def reference_list():
    return refs.list()

@app.get("/reference/get/{ref_id}")
def reference_get(ref_id: str):
    item = refs.get(ref_id)
    if not item:
        raise HTTPException(404, "Reference not found")
    return item
