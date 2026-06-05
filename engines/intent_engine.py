from ..models import EngineResult, ProductInput


class IntentEngine:
    HIGH_INTENT_KEYWORDS = [
        "buy", "best", "review", "discount", "cheap",
        "vs", "comparison", "alternative",
    ]

    def analyze(self, product: ProductInput, trend_result: EngineResult) -> EngineResult:
        try:
            match_count = self._count_keywords(product.product_name)
            score, label = self._score_intent(match_count)
            confidence = self._confidence(match_count)

            return EngineResult(
                score=round(score, 2),
                max_score=10.0,
                confidence=round(confidence, 2),
                details={
                    "high_intent_keywords_found": match_count,
                    "keywords_matched": self._matched_keywords(product.product_name),
                    "intent_level": label,
                    "sources_confirmed": 1,
                    "sources_checked": 1,
                },
            )
        except Exception as e:
            return EngineResult(
                score=5.0, max_score=10.0, confidence=0.4,
                details={"error": str(e)}, error=str(e),
            )

    def _count_keywords(self, product_name: str) -> int:
        name_lower = product_name.lower()
        return sum(1 for kw in self.HIGH_INTENT_KEYWORDS if kw in name_lower)

    def _matched_keywords(self, product_name: str) -> list:
        name_lower = product_name.lower()
        return [kw for kw in self.HIGH_INTENT_KEYWORDS if kw in name_lower]

    def _score_intent(self, match_count: int):
        if match_count >= 3:
            return 10.0, "very high intent"
        if match_count >= 1:
            return 8.0, "high intent"
        return 5.0, "medium intent"

    def _confidence(self, match_count: int) -> float:
        if match_count >= 3:
            return 0.95
        if match_count >= 1:
            return 0.8
        return 0.6
