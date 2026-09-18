from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence


def reciprocal_rank_fusion(rankings: Sequence[Sequence[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] += 1.0 / (k + rank)
    return dict(scores)


def exact_match_bonus(query: str, filename: str, ucs: str = "", tags: str = "") -> float:
    tokens = {token.casefold() for token in query.split() if len(token) > 1}
    haystacks = [filename.casefold(), ucs.casefold(), tags.casefold()]
    matches = sum(any(token in value for value in haystacks) for token in tokens)
    return min(matches * 0.001, 0.005)
