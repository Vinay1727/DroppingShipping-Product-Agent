from ..config import settings
from ..models import EngineResult, ProductInput


class MarginEngine:
    def analyze(self, product: ProductInput) -> EngineResult:
        try:
            cost = product.supplier_price
            price = product.selling_price

            if cost <= 0 or price <= 0:
                return EngineResult(
                    score=0.0, max_score=15.0, confidence=0.5,
                    details={"error": "Prices must be positive", "margin_percent": 0},
                    error="Invalid prices",
                )

            margin_percent = ((price - cost) / price) * 100.0
            roi_percent = ((price - cost) / cost) * 100.0 if cost > 0 else 0

            if margin_percent >= 80:
                score = 15.0
            elif margin_percent >= 70:
                score = 12.0
            elif margin_percent >= 60:
                score = 8.0
            else:
                score = 0.0

            margin_ratio = margin_percent / 100.0
            confidence = min(0.9, 0.4 + margin_ratio * 0.5)

            return EngineResult(
                score=round(score, 2),
                max_score=15.0,
                confidence=round(confidence, 2),
                details={
                    "cost": cost,
                    "price": price,
                    "profit": round(price - cost, 2),
                    "margin_percent": round(margin_percent, 2),
                    "roi_percent": round(roi_percent, 2),
                    "min_margin_threshold": settings.MIN_MARGIN_PERCENT,
                    "meets_threshold": margin_percent >= settings.MIN_MARGIN_PERCENT,
                    "sources_confirmed": 1,
                    "sources_checked": 1,
                },
            )
        except Exception as e:
            return EngineResult(
                score=0.0, max_score=15.0, confidence=0.3,
                details={"error": str(e)}, error=str(e),
            )
