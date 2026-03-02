from pathlib import Path

class ReferenceStore:
    def __init__(self):
        self.base = Path(__file__).resolve().parent.parent / "vendor" / "refs"

    def list(self):
        items = []
        if not self.base.exists():
            return items
        for p in sorted(self.base.glob("*")):
            if p.is_file():
                items.append({"id": p.name, "name": p.name})
        return items

    def get(self, ref_id: str):
        p = self.base / ref_id
        if not p.exists() or not p.is_file():
            return None
        return {"id": p.name, "name": p.name, "text": p.read_text(encoding="utf-8", errors="replace")}
