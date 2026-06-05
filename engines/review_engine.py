from typing import Optional

from ..models import EngineResult, ProductInput, ProviderResult


class ReviewEngine:
    def analyze(
        self,
        product: ProductInput,
        provider_data: Optional[dict[str, ProviderResult]] = None,
    ) -> EngineResult:
        try:
            amazon_data = None
            if provider_data:
                amz = provider_data.get("amazon")
                if amz and amz.success and amz.data:
                    amazon_data = amz.data

            if amazon_data:
                return self._score_from_amazon(amazon_data)

            return self._score_from_keywords(product.product_name)

        except Exception as e:
            return EngineResult(
                score=1.0, max_score=3.0, confidence=0.3,
                details={"error": str(e)}, error=str(e),
            )

    def _score_from_amazon(self, data: dict) -> EngineResult:
        avg_rating = data.get("avg_rating", 0)
        total_reviews = data.get("total_reviews", 0)
        product_count = data.get("product_count", 0)

        if avg_rating >= 4.5:
            rating_score = 3
        elif avg_rating >= 4.0:
            rating_score = 2
        elif avg_rating >= 3.0:
            rating_score = 1
        else:
            rating_score = 0

        if total_reviews > 5000:
            count_score = 3
        elif total_reviews > 1000:
            count_score = 2
        elif total_reviews > 50:
            count_score = 1
        else:
            count_score = 0

        if product_count > 50:
            recent_score = 3
        elif product_count > 10:
            recent_score = 2
        elif product_count > 0:
            recent_score = 1
        else:
            recent_score = 0

        raw = (count_score + rating_score + recent_score) / 3.0
        score = raw
        label = self._label(raw)
        confidence = 0.4 + (raw / 3.0) * 0.5

        return EngineResult(
            score=round(min(score, 3.0), 2),
            max_score=3.0,
            confidence=round(min(confidence, 0.95), 2),
            details={
                "review_count_score": count_score,
                "average_rating_score": rating_score,
                "recent_reviews_score": recent_score,
                "review_quality": label,
                "avg_rating": avg_rating,
                "total_reviews": total_reviews,
                "product_count": product_count,
                "data_source": "amazon_provider",
                "sources_confirmed": 1,
                "sources_checked": 1,
            },
        )

    def _score_from_keywords(self, product_name: str) -> EngineResult:
        count_score = self._score_review_count(product_name)
        rating_score = self._score_average_rating(product_name)
        recent_score = self._score_recent_reviews(product_name)

        raw = (count_score + rating_score + recent_score) / 3.0
        score = raw
        label = self._label(raw)
        confidence = 0.4 + (raw / 3.0) * 0.5

        return EngineResult(
            score=round(min(score, 3.0), 2),
            max_score=3.0,
            confidence=round(min(confidence, 0.95), 2),
            details={
                "review_count_score": count_score,
                "average_rating_score": rating_score,
                "recent_reviews_score": recent_score,
                "review_quality": label,
                "data_source": "keyword_heuristic",
                "sources_confirmed": 0,
                "sources_checked": 1,
            },
        )

    def _score_review_count(self, product_name: str) -> int:
        name_lower = product_name.lower()
        high_review = [
            "electronic", "gadget", "device", "tool", "appliance",
            "beauty", "skin", "hair", "makeup", "fitness",
            "kitchen", "home", "pet", "toy", "game",
            "headphone", "phone", "charger", "cable",
        ]
        low_review = [
            "consumable", "food", "drink", "snack", "beverage",
            "battery", "bulk", "refill", "disposable", "label",
            "sticker", "tag", "envelope", "bag",
        ]
        for cat in high_review:
            if cat in name_lower:
                return 3
        for cat in low_review:
            if cat in name_lower:
                return 0
        return 2

    def _score_average_rating(self, product_name: str) -> int:
        name_lower = product_name.lower()
        high_quality = [
            "premium", "pro", "professional", "advanced", "organic",
            "natural", "vegan", "hypoallergenic", "dermatologist",
            "medical", "surgical", "clinical", "therapeutic",
        ]
        low_quality = [
            "cheap", "budget", "basic", "generic", "replacement",
            "compatible", "universal", "economy", "value",
        ]
        for t in high_quality:
            if t in name_lower:
                return 3
        for t in low_quality:
            if t in name_lower:
                return 1
        return 2

    def _score_recent_reviews(self, product_name: str) -> int:
        name_lower = product_name.lower()
        trending = [
            "trending", "viral", "new", "2024", "2025", "2026",
            "popular", "hot", "latest", "recent", "upgraded",
        ]
        stagnant = [
            "classic", "traditional", "retro", "vintage", "old school",
            "original", "standard", "basic",
        ]
        for t in trending:
            if t in name_lower:
                return 3
        for t in stagnant:
            if t in name_lower:
                return 1
        return 2

    def _label(self, raw_score: float) -> str:
        if raw_score >= 2.5:
            return "excellent"
        if raw_score >= 1.5:
            return "good"
        if raw_score >= 0.5:
            return "average"
        return "poor"
