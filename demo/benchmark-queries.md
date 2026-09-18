# Evaluation query set (demo)

The benchmark query set is the closest thing this project has to a demo that can be shown without a licensed library, and it is worth showing because it makes the honest caveat concrete.

## Shape

100 entries in `examples/benchmark_queries.json`:

```json
{
  "id": "Q001",
  "query": "realistic close heavy rusty metal gate opening slowly",
  "category": "heavy",
  "relevant_file_ids": []
}
```

## Categories

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

## What is and is not being demonstrated

- **Demonstrated:** the project has a structured, categorised evaluation set and a harness that can compute retrieval metrics over it.
- **Not demonstrated:** retrieval quality. Every shipped entry has an empty `relevant_file_ids` array, because judging relevance requires a licensed 10k+ corpus. An empty ground truth cannot produce a Success@20 number.

That is precisely why the production target (Success@20 ≥ 80%) is documented as **not yet achieved** — see `docs/evaluation-gate.md`.

## What a real demo would need

1. A licensed test corpus indexed locally.
2. Ground-truth relevance populated per query.
3. Benchmark run, with results stored in `benchmark/reports/results.json`.
4. A recorded session showing successes **and** failures — the metaphor-style queries that CLAP retrieves badly are the most instructive part.

Until then, this file documents the evaluation approach rather than claiming a result.