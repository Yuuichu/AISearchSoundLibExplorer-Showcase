# AI SFX Explorer — local-first semantic search for sound-effects libraries

Natural-language retrieval over a large sound-effects library: describe the sound, get the file **and the time range inside it**, audition it, and drop it into the session — all running locally, with the source library strictly read-only.

<!-- Hero image: see screenshots/README.md -->

## Why I Built This

Sound-effects libraries grow past the point where filenames and folder structure can carry the search. A designer knows they want "heavy rusty metal gate opening slowly", but the library knows `MTL_GATE_Rusty_Open_01.wav`. The usual answers are tag discipline (which decays), or uploading the library to a cloud service (which is unacceptable for licensed or client material).

I wanted three properties at once: **local-first** (no audio leaves the machine), **read-only over the source library** (a search tool must never be able to corrupt the asset library), and **segment-level results** (a 40-second ambience contains several usable events; returning the whole file is not an answer).

## What It Does

- **Natural-language search** with three modes: `keyword`, `semantic`, `hybrid`.
- **Segment-level retrieval.** Long files are indexed as overlapping segments, so a hit points at a time range inside the file rather than at the file as a whole.
- **Dual-path recall with rank fusion.** Semantic (CLAP) and metadata candidates are retrieved independently and merged with Reciprocal Rank Fusion plus an exact-match bonus.
- **REAPER client.** Search, preview, similar, favourite, insert, segment-insert and keyboard navigation without leaving the DAW.
- **Whole-workflow plumbing:** resumable index jobs, waveforms and Range previews, UCS browsing, collections, favourites, feedback capture, history, CSV export, and an OpenAPI surface.
- **Non-destructive metadata.** Writing metadata produces a `.sfx.json` sidecar; the source file and its embedded tags are never modified.

## Workflow

```text
Natural-language query ("heavy rusty metal gate opening slowly")
        |
        v
query parsing  (optional LLM query planning — disabled by default)
        |
        +-------------------------+
        v                         v
  CLAP text embedding       metadata / keyword index
        |                         |
        v                         v
   Qdrant (HNSW)              SQLite
        |                         |
        +---------> RRF fusion <--+
                   (k = 60, + exact-match bonus)
                        |
                        v
        file hit + best matching time range
                        |
                        v
        REAPER client  /  HTTP API  /  debug UI
```

## Technical Highlights

- **Three-layer storage with a deliberate authority order.** SQLite is the source of truth for files, metadata, jobs, feedback, history and collections; Qdrant holds replaceable vector indexes and minimal filtering payloads. Rebuilding or migrating the vector store therefore cannot lose user data.
- **Index identity is versioned.** Collection names include the embedding model and preprocessing identity, so an embedding change creates a new collection instead of silently mixing incompatible vectors.
- **Fail-closed by default.** If CLAP cannot load, the system refuses to index rather than silently filling a production library with deterministic test vectors. The deterministic provider exists only for development and CI, behind an explicit flag.
- **Bounded segment indexing.** Files above the short-audio threshold use overlapping windows (10 s window / 5 s stride, capped at 60 segments), and search collapses segment hits back to files while keeping the best-matching range.
- **Resumable indexing.** Jobs checkpoint as they go and report progress every 50 files, so a re-run safely resumes files that were scanned but not yet embedded.
- **Read-only source audio.** The library is never written to; user and AI metadata live in SQLite, and export writes a sidecar.
- **LLM where it belongs.** Query planning only, disabled by default, and cloud providers receive query text alone — never audio, and never the library index.
- **Architecture decisions are written down as ADRs** (see `docs/adr-summary.md`), including the ones that constrain future work.

## Demo

`demo/benchmark-queries.md` describes the evaluation query set. Screenshots and a live demo are pending — see `screenshots/README.md`.

Selected source is in `selected-code/` (ranking/fusion, embeddings, vector store, and the REAPER client).

## Architecture

`docs/architecture.md` covers the layering and boundaries; `docs/adr-summary.md` summarises the four architectural decisions; `docs/reaper-integration.md` covers the DAW client; `docs/evaluation-gate.md` covers how retrieval quality is measured and gated.

## My Role

Sole author: retrieval design, indexing pipeline, storage model, API, REAPER client, evaluation harness and documentation.

## Limitations

These are stated deliberately, because retrieval quality is easy to overclaim:

- **The production quality target has not been met.** The repository documents **Success@20 ≥ 80% as a production goal**. It has **not** been achieved: reaching it requires populating ground-truth relevance over a licensed 10k+ sound-effects corpus. What exists today is a **100-query synthetic gate that validates the evaluation pipeline**, not a claim about real-library retrieval quality.
- **Scale is designed for, not demonstrated.** The architecture targets libraries in the hundreds of thousands of files; the largest library actually indexed locally is far smaller.
- **Advanced retrieval is deliberately switched off.** Cross-encoders, fine-tuned embeddings, personalised reranking, visual maps, automatic layering and scene analysis stay disabled unless the benchmark records at least a two-point Success@20 improvement with candidate latency under 500 ms. Missing evidence is treated as a hard off switch.
- **CLAP has real failure modes.** Descriptive metaphors ("a door that has given up") retrieve poorly. Failure cases are part of the honest picture and should be shown alongside successes.
- **CUDA is optional but recommended.** CPU embedding is correct, just slow; the production CLAP provider is required for meaningful semantic quality.
- **No audio content ships with this showcase**, by design.

## Repository Scope

This is a portfolio showcase repository. The full development repository remains private.

Included: architecture and ADR summaries, the evaluation-gate description, the ranking/embedding/vector-store code, the REAPER client, and the benchmark query set. Excluded: the product specification (`PLAN.md`), deployment configuration, local data directories, virtual environments and model weights.

## Tech Stack

`Python` · `CLAP (laion/clap-htsat-unfused, 512-d)` · `Qdrant (HNSW)` · `SQLite` · `FastAPI / OpenAPI` · `Reciprocal Rank Fusion` · `segment-level audio embeddings` · `REAPER ReaImGui (Lua)` · `Docker / compose` · `pytest + ruff + coverage`