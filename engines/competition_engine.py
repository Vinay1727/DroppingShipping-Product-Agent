from typing import Optional

from ..models import EngineResult, ProductInput, ProviderResult


class CompetitionEngine:
    SATURATED_TERMS = [
        "phone", "case", "charger", "cable", "t-shirt", "shoe",
        "headphone", "earphone", "laptop", "bag", "water bottle",
        "mug", "pillow", "blanket", "mask", "notebook", "pen",
        "wallet", "hat", "socks", "keychain", "sticker", "poster",
    ]
    NICHE_TERMS = [
        "remover", "extractor", "organizer", "specialty", "specific",
        "pro", "professional", "industrial", "heavy duty",
        "attachment", "adapter", "converter", "accessory",
        "hypoallergenic", "organic", "vegan", "natural",
        "automatic", "smart", "adjustable", "ergonomic",
    ]
    HIGH_AD_TERMS = [
        "insurance", "loan", "credit", "lawyer", "attorney",
        "dentist", "plumber", "locksmith", "moving", "storage",
        "weight loss", "diet", "supplement", "skin cream",
    ]

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
                score=5.0, max_score=10.0, confidence=0.4,
                details={"error": str(e)}, error=str(e),
            )

    def _score_from_amazon(self, amazon_data: dict) -> EngineResult:
        product_count = amazon_data.get("product_count", 0)

        if product_count > 5000:
            level = "extreme"
        elif product_count > 1000:
            level = "high"
        elif product_count > 100:
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
                "estimated_competitor_count": product_count,
                "marketplace_saturation": level,
                "advertising_density": "unknown",
                "competition_level": label,
                "sources_confirmed": 1,
                "sources_checked": 1,
                "data_source": "amazon_provider",
            },
        )

    def _score_from_keywords(self, product_name: str) -> EngineResult:
        competitor_count = self._estimate_competitor_count(product_name)
        marketplace_saturation = self._estimate_saturation(product_name)
        advertising_density = self._estimate_ad_density(product_name)

        level = self._classify_competition(
            competitor_count, marketplace_saturation, advertising_density
        )
        score, label = self._score_by_level(level)
        confidence = self._confidence(level)

        return EngineResult(
            score=round(score, 2),
            max_score=10.0,
            confidence=round(confidence, 2),
            details={
                "estimated_competitor_count": competitor_count,
                "marketplace_saturation": marketplace_saturation,
                "advertising_density": advertising_density,
                "competition_level": label,
                "sources_confirmed": 0,
                "sources_checked": 1,
                "data_source": "keyword_heuristic",
            },
        )

    def _estimate_competitor_count(self, product_name: str) -> int:
        name_lower = product_name.lower()
        saturated = sum(1 for t in self.SATURATED_TERMS if t in name_lower)
        niche = sum(1 for t in self.NICHE_TERMS if t in name_lower)
        if niche >= saturated and niche > 0:
            return 15
        if saturated > niche:
            return 300
        return 80

    def _estimate_saturation(self, product_name: str) -> str:
        name_lower = product_name.lower()
        saturated = sum(1 for t in self.SATURATED_TERMS if t in name_lower)
        niche = sum(1 for t in self.NICHE_TERMS if t in name_lower)
        if niche > saturated:
            return "low"
        if saturated >= 2:
            return "extreme"
        if saturated >= 1:
            return "high"
        return "medium"

    def _estimate_ad_density(self, product_name: str) -> str:
        name_lower = product_name.lower()
        for term in self.HIGH_AD_TERMS:
            if term in name_lower:
                return "high"

        saturated = sum(1 for t in self.SATURATED_TERMS if t in name_lower)
        niche = sum(1 for t in self.NICHE_TERMS if t in name_lower)
        if saturated >= 2:
            return "high"
        if saturated >= 1:
            return "medium"
        if niche > 0:
            return "low"
        return "medium"

    def _classify_competition(
        self, count: int, saturation: str, ad_density: str
    ) -> str:
        if saturation == "extreme" or (count > 200 and ad_density == "high"):
            return "extreme"
        if saturation == "high" or count > 100 or ad_density == "high":
            return "high"
        if saturation == "medium" or count > 30:
            return "medium"
        return "low"

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
