# Architecture decision summaries

> **English** | [简体中文](adr-summary.zh-CN.md)

The repository keeps full ADRs; these are the decisions and, more usefully, what each one costs.

## ADR-001 — Qdrant over FAISS

**Decision.** Qdrant is the production vector store. FAISS is restricted to exact-neighbour benchmark comparison.

**Why.** Persistence, updates, deletion, payload filters and HNSW in one store — the things a library that is continuously indexed actually needs. FAISS is excellent as an exact-recall reference point, which is exactly the role it keeps here: a benchmark comparator rather than a production dependency.

**Cost.** An external service (or an embedded instance) to run, and a second storage engine to reason about next to SQLite.

## ADR-002 — SQLite as the source of truth

**Decision.** All durable metadata and workflow state live in SQLite. Qdrant payloads are disposable index data.

**Why.** A vector collection is a derived artefact: it must be rebuildable when the embedding model or preprocessing changes. Putting user data in the vector store would make re-indexing a data-loss event. This decision is what makes ADR-001's replaceability actually safe.

**Cost.** Two stores to keep consistent, and every search merges results from both rather than trusting one authority.

## ADR-003 — Segment indexing

**Decision.** Short files get one file vector. Long files use bounded overlapping segments with adaptive stride. Search collapses segment hits to files while retaining the best matching time range.

**Why.** Whole-file embeddings average away local events; a 40-second ambience becomes one blurry vector. Segments make "that one metallic impact at 00:12" findable. Bounded overlap keeps the index from exploding.

**Cost.** More vectors per file, a larger index, and a collapse step in the search path that has to be correct — a bad collapse returns the right file with the wrong timestamp.

## ADR-004 — Benchmark-gated advanced retrieval

**Decision.** Cross-encoders, fine-tuned embeddings, personalised reranking, visual maps, automatic layering and scene analysis remain **disabled** unless `benchmark/reports/results.json` records at least a **two-point Success@20 improvement** and candidate latency below **500 ms**.

**Why.** Advanced retrieval techniques are easy to add and hard to justify. This ADR converts "we should try reranking" into a measurable, falsifiable requirement, and — importantly — treats **missing evidence as a hard off switch rather than implicit approval**.

**Cost.** Features stay unbuilt until the measurement infrastructure exists, which is slower than shipping them on intuition. That is the intended trade.

## What these decisions add up to

Authority flows in one direction: the audio library is read-only, SQLite is authoritative, the vector store is derived, and every optional quality feature has to earn its way in with evidence. The result is a system whose storage can be rebuilt, whose embeddings can be replaced, and whose claims about quality are bounded by what has actually been measured.