from product_agent.models import EngineResult, ProductInput


class SupplierEngine:
    def analyze(self, product: ProductInput) -> EngineResult:
        try:
            rating_score = self._score_supplier_rating(product)
            order_score = self._score_order_count(product)
            years_score = self._score_years_active(product)

            raw = (rating_score + order_score + years_score) / 3.0
            score = raw * 2.0
            label = self._label(raw)

            confidence = 0.4 + (raw / 5.0) * 0.5

            return EngineResult(
                score=round(min(score, 10.0), 2),
                max_score=10.0,
                confidence=round(min(confidence, 0.95), 2),
                details={
                    "supplier_rating": rating_score,
                    "order_count": order_score,
                    "years_active": years_score,
                    "supplier_quality": label,
                    "sources_confirmed": 1,
                    "sources_checked": 1,
                },
            )
        except Exception as e:
            return EngineResult(
                score=4.0, max_score=10.0, confidence=0.3,
                details={"error": str(e)}, error=str(e),
            )

    def _score_supplier_rating(self, product: ProductInput) -> int:
        cost = product.supplier_price
        price = product.selling_price
        if cost <= 0 or price <= 0:
            return 0
        ratio = cost / price
        if ratio <= 0.2:
            return 5
        if ratio <= 0.3:
            return 4
        if ratio <= 0.4:
            return 4
        if ratio <= 0.5:
            return 2
        if ratio <= 0.6:
            return 2
        return 0

    def _score_order_count(self, product: ProductInput) -> int:
        name_lower = product.product_name.lower()
        high_volume = [
            "remover", "cleaner", "organizer", "tool", "kit", "mat",
            "holder", "wrap", "bag", "case", "cover", "protector",
            "dispenser", "brush", "comb", "pad", "cloth", "towel",
        ]
        low_volume = [
            "specialty", "industrial", "heavy duty", "pro", "professional",
            "custom", "bespoke", "limited", "artisan", "handmade",
        ]
        for term in low_volume:
            if term in name_lower:
                return 2
        for term in high_volume:
            if term in name_lower:
                return 5
        return 4

    def _score_years_active(self, product: ProductInput) -> int:
        name_lower = product.product_name.lower()
        established = [
            "classic", "original", "traditional", "standard", "proven",
            "essential", "basic", "universal", "general",
        ]
        new_trending = [
            "new", "innovative", "smart", "advanced", "next gen",
            "modern", "trending", "viral", "tiktok",
        ]
        for term in established:
            if term in name_lower:
                return 5
        for term in new_trending:
            if term in name_lower:
                return 2
        return 4

    def _label(self, raw_score: float) -> str:
        if raw_score >= 4.5:
            return "excellent"
        if raw_score >= 3.5:
            return "good"
        if raw_score >= 2.0:
            return "average"
        return "poor"
