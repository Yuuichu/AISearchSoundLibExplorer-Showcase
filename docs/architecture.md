# Architecture

The governing rule is a **one-way dependency direction**:

```text
API / CLI  ->  services  ->  repositories / adapters
```

API routes never touch SQLite, Qdrant or CLAP directly. That boundary is what makes the storage and embedding layers replaceable, and it is what makes the evaluation gate meaningful: quality can change without the interface changing.

## Storage model

| Layer | Role | Authority |
|---|---|---|
| **SQLite** | Files, metadata, jobs, feedback, history, collections | **Source of truth** |
| **Qdrant** | Vector indexes (HNSW) plus minimal filtering payloads | Replaceable index data |
| **Source audio library** | The actual `.wav` files and their embedded metadata | **Read-only, never modified** |

Consequences that follow from that ordering:

- Rebuilding or migrating a vector collection cannot lose user data, because none of it lives in the vector store.
- User and AI-generated metadata lives in SQLite, not in the audio files.
- Collection names include the **embedding model and preprocessing identity**, so changing embeddings creates a new collection rather than mixing incompatible vectors into an existing one.
- Writing metadata produces a separate `.sfx.json` sidecar next to the file (opt-in, `--confirm`); embedded source metadata is never edited.

## Retrieval pipeline

1. **Query parsing.** Raw text in; optional LLM query planning (disabled by default). Cloud query providers receive the query text only.
2. **Dual-path recall.** Two candidate sets are retrieved independently — semantic (CLAP text embedding against Qdrant) and metadata/keyword (SQLite). Default candidate budget: 300 each.
3. **Fusion.** Candidates are merged with **Reciprocal Rank Fusion (k = 60)** plus an exact-match bonus, producing one ranked list. Three user-facing modes (`keyword`, `semantic`, `hybrid`) select which paths contribute.
4. **Segment collapse.** Segment-level hits are folded back to their parent file, retaining the best matching time range — which is what the caller actually needs in order to insert a usable slice.

## Indexing pipeline

- Files are scanned and hashed; the hash threshold distinguishes cheap-change detection from full re-reads.
- **Short files** (below the short-audio threshold): one vector for the whole file.
- **Long files:** bounded overlapping segments — 10 s window, 5 s stride, capped at 60 segments per file — so a hit can point *inside* a long ambience instead of at the whole recording.
- Jobs are **resumable**: files scanned but not yet embedded are safely re-processed on the next run, with progress reported every 50 files.
- **Fail-closed embedding:** if the CLAP provider cannot load, indexing refuses to run. A deterministic test provider exists for development and CI only (`embedding.allow_deterministic_fallback`), so a production library can never be populated with meaningless vectors.

## Adapters

| Adapter | Notes |
|---|---|
| **REAPER** | ReaImGui client over loopback HTTP (`docs/reaper-integration.md`) |
| **CLAP** | Production text/audio embedding provider |
| **Vector store** | Qdrant (embedded for development, standalone URL for large libraries) |
| **Database** | SQLite |

## Interfaces

- **HTTP API** (FastAPI) with an OpenAPI description at `/docs`: search, similar audio, segment/Range preview, waveforms, index jobs, metadata, feedback, history, collections, UCS browsing, layered queries and CSV export.
- **CLI** (`python -m sfx`): `init`, `index`, `search`, `similar`, `benchmark`, `serve`.
- **Debug UI** served locally alongside the API.
- **REAPER client** for in-DAW use.

## Validation

- `ruff` for linting.
- `pytest --cov=sfx` for the test suite.
- `scripts/benchmark_scale.py --count 10000` for scale benchmarking.
- The evaluation gate itself: see `docs/evaluation-gate.md`.