from ..models import EngineResult, ProductInput


class LogisticsEngine:
    def analyze(self, product: ProductInput) -> EngineResult:
        try:
            shipping_score = self._score_shipping_time(product)
            tracking_score = self._score_tracking_availability(product)
            warehouse_score = self._score_warehouse_location(product)

            raw = (shipping_score + tracking_score + warehouse_score) / 3.0
            score = raw
            label = self._label(raw)

            confidence = 0.4 + (raw / 2.0) * 0.5

            return EngineResult(
                score=round(min(score, 2.0), 2),
                max_score=2.0,
                confidence=round(min(confidence, 0.95), 2),
                details={
                    "shipping_time": shipping_score,
                    "tracking_availability": tracking_score,
                    "warehouse_location": warehouse_score,
                    "logistics_quality": label,
                    "sources_confirmed": 1,
                    "sources_checked": 1,
                },
            )
        except Exception as e:
            return EngineResult(
                score=1.0, max_score=2.0, confidence=0.3,
                details={"error": str(e)}, error=str(e),
            )

    def _score_shipping_time(self, product: ProductInput) -> int:
        name_lower = product.product_name.lower()
        fast_ship = [
            "mat", "pad", "cloth", "wrap", "film", "sheet", "card",
            "sticker", "label", "tag", "band", "strap", "tape",
            "cap", "lid", "cover", "sleeve", "bag", "pouch",
            "remover", "cleaner", "organizer", "tool", "kit",
        ]
        slow_ship = [
            "machine", "device", "appliance", "furniture", "table",
            "chair", "cabinet", "rack", "frame", "structure",
            "dumbbell", "weight", "bench", "tire", "wheel",
            "liquid", "oil", "spray", "aerosol", "battery",
            "fitness", "gym", "treadmill", "bike",
        ]
        for term in fast_ship:
            if term in name_lower:
                return 2
        for term in slow_ship:
            if term in name_lower:
                return 0
        return 1

    def _score_tracking_availability(self, product: ProductInput) -> int:
        price = product.selling_price
        if price >= 50:
            return 2
        if price >= 20:
            return 1
        return 0

    def _score_warehouse_location(self, product: ProductInput) -> int:
        name_lower = product.product_name.lower()
        widely_stocked = [
            "mat", "pad", "cloth", "wrap", "bag", "case", "cover",
            "tool", "kit", "remover", "cleaner", "organizer",
            "holder", "strap", "band", "clip", "hook",
        ]
        specialty = [
            "industrial", "heavy duty", "commercial", "medical",
            "surgical", "laboratory", "scientific", "custom",
        ]
        for term in widely_stocked:
            if term in name_lower:
                return 2
        for term in specialty:
            if term in name_lower:
                return 0
        return 1

    def _label(self, raw_score: float) -> str:
        if raw_score >= 1.5:
            return "excellent"
        if raw_score >= 0.5:
            return "average"
        return "poor"
