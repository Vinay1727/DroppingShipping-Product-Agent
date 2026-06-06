from typing import Optional

from product_agent.models import EngineResult, ProductInput, ProviderResult


class CompetitionEngine:
    def analyze(
        self,
        product: ProductInput,
        provider_data: Optional[dict[str, ProviderResult]] = None,
    ) -> EngineResult:
        try:
            search_data = None
            if provider_data:
                srch = provider_data.get("search")
                if srch and srch.success and srch.data:
                    search_data = srch.data

            if search_data:
                return self._score_from_search(search_data)

            return EngineResult(
                score=5.0,
                max_score=10.0,
                confidence=0.3,
                details={
                    "estimated_competitor_count": "unknown",
                    "marketplace_saturation": "unknown",
                    "competition_level": "unknown",
                    "sources_confirmed": 0,
                    "sources_checked": 1,
                    "data_source": "no_data",
                },
            )

        except Exception as e:
            return EngineResult(
                score=5.0, max_score=10.0, confidence=0.4,
                details={"error": str(e)}, error=str(e),
            )

    def _score_from_search(self, search_data: dict) -> EngineResult:
        result_count = search_data.get("result_count", 0)

        if result_count > 100:
            level = "extreme"
        elif result_count > 50:
            level = "high"
        elif result_count > 20:
            level = "medium"
        else:
            level = "low"

        score, label = self._score_by_level(level)
        confidence = self._confidence(level)

        return EngineResult(
            score=round(score, 2),
            max_score=10.0,
            confidence=round(confidence, 2),
            details={
                "estimated_competitor_count": result_count,
                "marketplace_saturation": level,
                "competition_level": label,
                "has_amazon_listings": search_data.get("has_amazon_listings", False),
                "sources_confirmed": 1,
                "sources_checked": 1,
                "data_source": "search_provider",
            },
        )

    def _score_by_level(self, level: str):
        mapping = {
            "low": (10.0, "low competition"),
            "medium": (7.0, "medium competition"),
            "high": (4.0, "high competition"),
            "extreme": (1.0, "extreme competition"),
        }
        return mapping.get(level, (5.0, "unknown"))

    def _confidence(self, level: str) -> float:
        mapping = {
            "low": 0.85,
            "medium": 0.75,
            "high": 0.7,
            "extreme": 0.8,
        }
        return mapping.get(level, 0.6)
