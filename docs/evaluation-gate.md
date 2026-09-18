# Evaluation gate — how retrieval quality is measured (and not claimed)

This is the most important document in the showcase, because retrieval quality is the easiest thing in this project to overstate.

## The short version

| Claim | Status |
|---|---|
| Success@20 ≥ 80% | **Production goal. Not achieved.** |
| Evaluation pipeline works end to end | **Yes** — validated by a 100-query gate |
| Advanced retrieval improves quality | **Unproven, therefore disabled** |

## 1. What exists today

The repository ships a **100-query synthetic query set** (`benchmark/queries/benchmark_queries.json`), each entry shaped as:

```json
{
  "id": "Q001",
  "query": "realistic close heavy rusty metal gate opening slowly",
  "category": "heavy",
  "relevant_file_ids": []
}
```

Query categories:

| `large` | 8 |
| `small` | 8 |
| `heavy` | 8 |
| `monster` | 4 |
| `car` | 4 |
| `plastic` | 4 |
| `industrial` | 4 |
| `soft` | 4 |
| `forest` | 4 |
| `electricity` | 4 |
| `ceramic` | 4 |
| `snow` | 4 |
| `paper` | 4 |
| `distant` | 4 |
| `rifle` | 4 |
| `fast` | 4 |
| `close` | 4 |
| `metal` | 4 |
| `underwater` | 4 |
| `cloth` | 4 |
| `wet` | 4 |
| `wooden` | 4 |

**The critical detail:** `relevant_file_ids` is empty in every shipped entry. Ground truth requires a licensed 10k+ sound-effects corpus to judge against, which is not something this project can ship. So the synthetic set currently validates the **evaluation machinery** — parsing, candidate generation, metric computation, reporting — not retrieval quality.

Anyone quoting a quality number from this repository without first populating `relevant_file_ids` against a real corpus would be quoting an artefact of the harness.

## 2. What reaching production quality requires

1. Populate `relevant_file_ids` using a **licensed 10k+ SFX corpus**.
2. Run the benchmark and reach **Success@20 ≥ 80%**.
3. Keep advanced retrieval fail-closed until it demonstrably helps (see below).

Until step 1 is done, no Success@20 figure from this project is meaningful.

## 3. The fail-closed rule (ADR-004)

Cross-encoders, fine-tuned embeddings, personalised reranking, visual maps, automatic layering and scene analysis are **disabled by default**, and stay disabled unless `benchmark/reports/results.json` records:

- at least a **two-point Success@20 improvement**, and
- candidate latency **below 500 ms**.

**Missing evidence is a hard off switch, not implicit approval.** This is the design decision that keeps the project honest: an unbuilt feature cannot quietly become a claim.

## 4. Other validation that does run

| Check | Command |
|---|---|
| Lint | `ruff check .` |
| Tests + coverage | `pytest --cov=sfx` |
| Scale benchmark | `python scripts/benchmark_scale.py --count 10000` |

Note that the scale benchmark measures *the pipeline's behaviour at scale* (throughput, latency), which is a different question from retrieval *quality*.

## 5. How quality claims should be made in this showcase

- Allowed: "the evaluation harness and gate exist, and advanced features are blocked behind measured improvement."
- Allowed: "a 100-query synthetic gate validates the evaluation pipeline."
- Not allowed: "retrieval reaches 80% Success@20", or any statement implying the production target has been met.
- Not allowed: presenting the synthetic gate as evidence of real-library retrieval quality.

## 6. Known failure modes worth showing

CLAP retrieves descriptive, sound-driven phrasing well and metaphorical or narrative phrasing poorly. Any future demo of this system should include failures — including queries where the right file was never returned — because that is what the gate is for.