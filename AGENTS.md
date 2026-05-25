# Damascus Pattern Simulator — Project Rules

## How Agents Should Use These Rules
This file is the always-read entry point. Linked rule files contain detailed requirements and are part of the project rules, not optional background reading.

Before changing simulation, geometry, rendering, cross-section, cut/grind, export, or forging workflow code, read:
- `docs/agent-rules/material-field-requirements.md`
- `docs/agent-rules/deformation-formulas.md`

## RAG-Assisted Development
This project has a local RAG index powered by Ollama + ChromaDB. Before answering development questions about this codebase, query the RAG index for relevant code context:

```bash
/home/gary/Projects/codebase-rag/venv/bin/python /home/gary/Projects/codebase-rag/query.py /home/gary/Projects/damascus-pattern-simulator "<question>" --json --top-k 5
```

Use the returned code snippets as additional context when answering. If the index seems stale, re-index first:

```bash
/home/gary/Projects/codebase-rag/venv/bin/python /home/gary/Projects/codebase-rag/index.py /home/gary/Projects/damascus-pattern-simulator --incremental
```

## Project Architecture
- **Electron + TypeScript frontend** in `src/` (main process, preload, renderer)
- **Python FastAPI backend** in `python/` (3D engine, forging operations, steel database)
- **Shared Python library modules** in `lib/` (forging operations, GUI, visualization, billet/layer classes)
- **Build output** in `out/`
- **3D engine**: Open3D + NumPy for mesh manipulation, matplotlib for visualization

## Critical Simulation Requirement: Through-Volume Material Field
The visual result must not be surface-only eye candy. A forge-welded billet is one continuous steel body with a through-volume internal material field. Viewport colors, end faces, cross-sections, grind faces, cut faces, and exports must sample that same material field.

Do not create decorative caps, skins, or surface-only patterns. If a temporary compatibility workaround is unavoidable, label it transitional and do not treat it as the final simulation model.

Detailed rules:
- `docs/agent-rules/material-field-requirements.md`
- `docs/agent-rules/deformation-formulas.md`

## Coding Conventions
- Python modules in `lib/` are designed to be reusable across scripts
- All forging operations are in separate `lib/forging_*.py` modules
- Extensive debug logging is built into all operations via `lib/logging_config.py`
- The Python API bridges to Electron via FastAPI (`python/api.py`)
