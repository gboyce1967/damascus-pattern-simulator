# Local Codebase RAG System — Development Plan
**Date:** 2026-05-04
**Status:** Approved, pending implementation

## Problem
Build a reusable, fully-local RAG pipeline that indexes any codebase by function/class boundaries, stores embeddings in ChromaDB, and retrieves relevant code context on demand — using Ollama for all AI operations (no cloud APIs).

## Current State
- Damascus project has ~30 source files across `src/` (TypeScript), `python/`, and `lib/` (Python)
- Ollama running on Gary's network (likely at 192.168.101.16, needs confirmation)
- No RAG tooling exists yet

## Architecture
**Standalone reusable project** at `~/Projects/codebase-rag/` — indexes any project, stores vectors per-project in `.rag_index/` subdirectories.

### Project layout
```
~/Projects/codebase-rag/
├── index.py              # CLI: index a codebase
├── query.py              # CLI: query the index
├── config.yaml           # Default config template
├── requirements.txt
├── lib/
│   ├── __init__.py
│   ├── scanner.py        # File discovery & filtering
│   ├── chunker.py        # Tree-sitter function/class boundary parsing
│   ├── embedder.py       # Ollama embedding client
│   ├── store.py          # ChromaDB persistence
│   ├── retriever.py      # Similarity search + context assembly
│   └── debug.py          # Logging, timing, diagnostics
```

### Per-project output (gitignored)
```
<any-project>/.rag_index/
├── chroma_db/            # Vector database
└── index_meta.json       # Indexing metadata (timestamp, files, config)
```

## Key Design Decisions
- **Embeddings**: `nomic-embed-text` via Ollama — 8192-token context, designed for retrieval. Fallback to `mxbai-embed-large` or `all-minilm`.
- **Chunking**: Tree-sitter for language-aware function/class boundary splitting (Python + TypeScript). Regex fallback.
- **LLM (optional)**: Configurable Ollama LLM for standalone RAG Q&A mode. Retrieval-only mode for Oz integration.
- **Scanning scope**: Configurable per-project. Defaults to full project root for `.py`, `.ts`, `.js`, `.tsx`, `.jsx`.

## Config defaults
```yaml
ollama:
  host: "http://localhost:11434"
  embed_model: "nomic-embed-text"
  llm_model: null

scanner:
  include_dirs: ["."]
  exclude_dirs: ["node_modules", ".git", "venv", ".venv", "__pycache__", "out", "dist", ".rag_index"]
  file_extensions: [".py", ".ts", ".js", ".tsx", ".jsx"]

chunker:
  strategy: "tree_sitter"
  max_chunk_size: 2000
  overlap_lines: 2

retriever:
  top_k: 10
  min_similarity: 0.25
```

## CLI Usage
```bash
# Index
python ~/Projects/codebase-rag/index.py ~/Projects/damascus-pattern-simulator

# Query (retrieval-only)
python ~/Projects/codebase-rag/query.py ~/Projects/damascus-pattern-simulator "how does wedge deformation work?"

# Query (full RAG with LLM)
python ~/Projects/codebase-rag/query.py ~/Projects/damascus-pattern-simulator "how does wedge deformation work?" --answer

# Incremental re-index
python ~/Projects/codebase-rag/index.py ~/Projects/damascus-pattern-simulator --incremental
```

## Warp Rules (to create)
1. **Project rule** for damascus-pattern-simulator: query RAG index before answering dev questions
2. **Global rule**: index and use RAG for all coding projects under `~/Projects/`

## Implementation Steps
1. Create project directory, venv, install deps (llama-index, chromadb, tree-sitter, ollama, pyyaml)
2. Build lib/debug.py — logging and timing
3. Build lib/scanner.py — file discovery
4. Build lib/chunker.py — tree-sitter parsing
5. Build lib/embedder.py — Ollama embedding client
6. Build lib/store.py — ChromaDB management
7. Build lib/retriever.py — similarity search
8. Build index.py — CLI indexer
9. Build query.py — CLI query tool
10. Create config.yaml template
11. Index damascus-pattern-simulator and verify
12. Create Warp rules

## Notes
- Gary's Ollama machine appears to be at 192.168.101.16 (from SSH attempt)
- Need to confirm Ollama port and available models after reboot
