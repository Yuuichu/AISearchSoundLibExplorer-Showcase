# Screenshots

Empty in this draft. A meaningful capture requires a licensed sound-effects library indexed locally, which is not available here — and capturing the UI against a private library would risk exposing client material.

## What should be captured

1. **`hero-reaper-search.png`** — the REAPER ReaImGui client after a natural-language query, showing ranked results. This is the strongest single image: retrieval *in the tool where it is used*.
2. **`segment-insert.png`** — segment insertion of a matched time range, which is the capability that distinguishes this from a file-name search.
3. **`debug-ui.png`** — the local debug UI with waveforms and Range preview.
4. **`openapi-docs.png`** — the `/docs` OpenAPI surface, showing that the engine is an API, not a script.
5. **`benchmark-report.png`** — an evaluation-gate report, which is the visual form of "quality is measured, not asserted".
6. **A failure example.** A query where the expected sound is *not* found. Showing only successes would misrepresent a system whose production target is explicitly unmet.

## Constraints on what may be shown

- **No client or licensed library content** in any frame: no real file names, no library paths, no waveform of client material. Use a synthetic or CC0 test library.
- No `.env` contents, API keys or tokens.
- No absolute local paths in the UI or terminal.

Until these exist, the showcase makes no visual claims.