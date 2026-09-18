# Licence and third-party notice

## AI SFX Explorer

Released under the **MIT licence** — the full text is included as `LICENSE` (Copyright (c) 2026 Yuuichu).

## Models and data

- **CLAP** (`laion/clap-htsat-unfused`, 512-dimensional) is used as the embedding provider. Model weights are **not** redistributed in this showcase; they are downloaded from their upstream source at install time and cached locally by the application.
- **No sound-effects audio is included.** The library is the user's own licensed material, and the system is designed to treat it as strictly read-only.
- **No ground-truth relevance data is included**, for the same reason: judging relevance requires a licensed corpus.

## Third-party software

| Component | Role | Licence |
|---|---|---|
| `Qdrant` | Vector index (HNSW) | Apache-2.0 |
| `clap` / `laion` model | Text/audio embeddings | see upstream model card |
| `FastAPI` | HTTP API + OpenAPI | MIT |
| `SQLite` | Durable metadata store | Public domain |
| `REAPER` + **ReaImGui** | DAW host and scripting UI | REAPER and ReaImGui are the property of their authors; ReaImGui is installed via ReaPack |

**REAPER** is commercial software by Cockos Incorporated and is not included or licensed here. The Lua client is an independent script that runs inside a licensed REAPER installation.

## Included sources

`selected-code/` contains verbatim copies of the ranking/fusion logic, the embedding provider layer, the vector-store adapter and the REAPER client entry point. No credentials, no API keys and no library paths are included; `config.toml` is not copied, but its non-secret defaults are described in the architecture documentation.