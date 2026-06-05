from typing import Optional

from ..models import EngineResult, ProductInput, ProviderResult


class DemandEngine:
    def analyze(
        self,
        product: ProductInput,
        trend_result: Optional[EngineResult] = None,
        provider_data: Optional[dict[str, ProviderResult]] = None,
    ) -> EngineResult:
        try:
            google_confirmed = self._check_google_trends(trend_result, provider_data)
            amazon_confirmed = self._check_amazon(provider_data)
            reddit_confirmed = self._check_reddit(provider_data)
            heuristic_confirmed = self._check_heuristic(product.product_name)

            sources = {
                "google_trends": google_confirmed,
                "amazon": amazon_confirmed,
                "reddit": reddit_confirmed,
                "heuristic": heuristic_confirmed,
            }

            confirmed_count = sum(1 for v in sources.values() if v)
            score = confirmed_count * 5.0

            confidence = 0.3 + (confirmed_count / 4.0) * 0.6

            has_provider_data = bool(provider_data)
            has_real_source = amazon_confirmed or google_confirmed or reddit_confirmed

            return EngineResult(
                score=round(min(score, 20.0), 2),
                max_score=20.0,
                confidence=round(confidence, 2),
                details={
                    "google_trends": google_confirmed,
                    "amazon": amazon_confirmed,
                    "reddit": reddit_confirmed,
                    "heuristic": heuristic_confirmed,
                    "confirmed_sources": confirmed_count,
                    "total_sources": 4,
                    "sources_confirmed": confirmed_count,
                    "sources_checked": 4,
                    "data_source": "providers" if has_real_source else "heuristic_only",
                },
            )
        except Exception as e:
            return EngineResult(
                score=4.0, max_score=20.0, confidence=0.2,
                details={"error": str(e), "sources_confirmed": 0, "sources_checked": 4}, error=str(e),
            )

    def _check_google_trends(
        self,
        trend_result: Optional[EngineResult],
        provider_data: Optional[dict[str, ProviderResult]],
    ) -> bool:
        if provider_data:
            gt = provider_data.get("google_trends")
            if gt and gt.success and gt.data:
                avg = gt.data.get("one_eighty_day_avg", 0)
                direction = gt.data.get("direction", "stable")
                if avg > 10 or direction == "rising":
                    return True

        if trend_result:
            details = trend_result.details
            avg = details.get("one_eighty_day_avg", 0)
            direction = details.get("direction", "unknown")
            if avg > 10 or direction == "rising":
                return True

        return False

    def _check_amazon(self, provider_data: Optional[dict[str, ProviderResult]]) -> bool:
        if provider_data:
            amz = provider_data.get("amazon")
            if amz and amz.success and amz.data:
                reviews = amz.data.get("total_reviews", 0)
                listings = amz.data.get("product_count", 0)
                return reviews > 50 or listings > 5

        return False

    def _check_reddit(self, provider_data: Optional[dict[str, ProviderResult]]) -> bool:
        if provider_data:
            reddit = provider_data.get("reddit")
            if reddit and reddit.success and reddit.data:
                return reddit.data.get("post_count_30d", 0) > 0

        return False

    def _check_heuristic(self, product_name: str) -> bool:
        name_lower = product_name.lower()
        visual_categories = [
            "fashion", "beauty", "hair", "skin", "makeup", "nail",
            "home", "decor", "kitchen", "garden", "craft", "DIY",
            "wedding", "party", "recipe", "food", "drink",
            "fitness", "yoga", "outfit", "style", "jewelry",
            "art", "drawing", "painting", "tattoo", "nail art",
            "organizer", "storage", "furniture", "lighting",
            "remover", "cleaner", "tool", "pet", "dog", "cat",
        ]
        for cat in visual_categories:
            if cat in name_lower:
                return True
        return False
