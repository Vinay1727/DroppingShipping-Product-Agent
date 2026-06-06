STRONG_PRODUCT_MIN_SCORE = 35


def filter_strong_products(candidates):
    strong = [c for c in candidates if c.get("discovery_score", 0) >= STRONG_PRODUCT_MIN_SCORE]
    return strong


def rank_candidates(candidates, top_n=50):
    scored = []
    for c in candidates:
        score = _calculate_discovery_score(c)
        scored.append({**c, "discovery_score": round(score, 2)})

    scored.sort(key=lambda x: x["discovery_score"], reverse=True)
    return scored[:top_n]


def _calculate_discovery_score(candidate):
    source = candidate.get("source", "")
    score = 0.0

    if source == "google_trends":
        growth = candidate.get("growth", 0)
        if growth >= 100:
            score = 80 + (growth - 100) * 0.05
        elif growth >= 50:
            score = 60 + (growth - 50) * 0.4
        else:
            score = growth * 1.2

        score = min(score, 100)

    elif source == "reddit":
        mentions = candidate.get("mentions", 0)
        if mentions >= 10:
            score = 70 + min(mentions, 50) * 0.5
        elif mentions >= 5:
            score = 50 + (mentions - 5) * 4
        elif mentions >= 2:
            score = 30 + (mentions - 2) * 6
        else:
            score = 15

        score = min(score, 95)

    return max(0, min(100, score))
