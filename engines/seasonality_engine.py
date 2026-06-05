from ..models import EngineResult, ProductInput


class SeasonalityEngine:
    def analyze(self, product: ProductInput, trend_result: EngineResult) -> EngineResult:
        try:
            product_type = self._classify_product(product.product_name)

            if product_type == "evergreen":
                score = 10.0
            elif product_type == "seasonal":
                score = 4.0
            else:
                score = 1.0

            confidence = 0.9 if product_type == "evergreen" else 0.6

            return EngineResult(
                score=round(score, 2),
                max_score=10.0,
                confidence=round(confidence, 2),
                details={
                    "product_type": product_type,
                    "explanation": self._explain(product_type),
                    "sources_confirmed": 1,
                    "sources_checked": 1,
                },
            )
        except Exception as e:
            return EngineResult(
                score=5.0, max_score=10.0, confidence=0.4,
                details={"error": str(e)}, error=str(e),
            )

    def _classify_product(self, product_name: str) -> str:
        name_lower = product_name.lower()

        event_based = [
            "election", "campaign", "president", "candidate", "vote",
            "olympic", "world cup", "super bowl", "graduation",
            "commencement", "inauguration", "coronation",
        ]
        for term in event_based:
            if term in name_lower:
                return "event_based"

        seasonal = [
            "christmas", "xmas", "santa", "easter", "halloween",
            "thanksgiving", "valentine", "hanukkah", "kwanzaa",
            "new year", "fourth of july", "independence day",
            "st patrick", "mother day", "father day", "memorial day",
            "labor day", "back to school", "summer", "winter",
            "spring", "fall", "autumn", "beach", "pool", "snow",
            "costume", "candy", "ornament", "wreath", "stocking",
            "firework", "bbq", "grill", "sunblock", "sunscreen",
            "umbrella", "raincoat", "mitten", "scarf", "beanie",
        ]
        for term in seasonal:
            if term in name_lower:
                return "seasonal"

        return "evergreen"

    def _explain(self, product_type: str) -> str:
        if product_type == "evergreen":
            return "Year-round demand, consistent sales potential"
        if product_type == "seasonal":
            return "Seasonal demand peak, limited selling window"
        return "Event-based demand spike, high timing risk"
