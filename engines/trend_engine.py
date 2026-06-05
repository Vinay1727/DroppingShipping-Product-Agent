import warnings
from typing import Optional

import numpy as np

warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from pytrends.request import TrendReq
    from pytrends.exceptions import ResponseError
    PYTRENDS_AVAILABLE = True
except Exception:
    PYTRENDS_AVAILABLE = False
    TrendReq = None
    ResponseError = Exception

from ..config import settings
from ..models import EngineResult, TrendMetrics, ProviderResult


class TrendEngine:
    def __init__(self, lookback_days: int = 180):
        self.lookback_days = lookback_days

    def analyze(self, product_name: str, provider_data: Optional[dict[str, ProviderResult]] = None) -> EngineResult:
        provider_result = None
        if provider_data:
            provider_result = provider_data.get("google_trends")

        if provider_result and provider_result.success and provider_result.data:
            return self._score_from_provider(provider_result.data)

        return self._fetch_and_score(product_name)

    def _score_from_provider(self, data: dict) -> EngineResult:
        metrics = TrendMetrics(
            seven_day_avg=data.get("seven_day_avg", 0),
            thirty_day_avg=data.get("thirty_day_avg", 0),
            ninety_day_avg=data.get("ninety_day_avg", 0),
            one_eighty_day_avg=data.get("one_eighty_day_avg", 0),
            direction=data.get("direction", "stable"),
            momentum=data.get("momentum", 0),
            stability=data.get("stability", 0),
        )
        score = self._calculate_score(metrics)
        return EngineResult(
            score=round(score, 2),
            max_score=20.0,
            confidence=round(metrics.stability, 2),
            details={
                "seven_day_avg": metrics.seven_day_avg,
                "thirty_day_avg": metrics.thirty_day_avg,
                "ninety_day_avg": metrics.ninety_day_avg,
                "one_eighty_day_avg": metrics.one_eighty_day_avg,
                "direction": metrics.direction,
                "momentum": metrics.momentum,
                "stability": metrics.stability,
                "sources_confirmed": 1,
                "sources_checked": 1,
                "data_source": "google_trends_provider",
            },
        )

    def _fetch_and_score(self, product_name: str) -> EngineResult:
        if not settings.GOOGLE_TRENDS_ENABLE:
            return self._fallback_result("Google Trends disabled in config")

        try:
            series = self._fetch_trends(product_name)
            metrics = self._calculate_metrics(series)
            score = self._calculate_score(metrics)
            return EngineResult(
                score=round(score, 2),
                max_score=20.0,
                confidence=round(metrics.stability, 2),
                details={
                    "seven_day_avg": round(metrics.seven_day_avg, 2),
                    "thirty_day_avg": round(metrics.thirty_day_avg, 2),
                    "ninety_day_avg": round(metrics.ninety_day_avg, 2),
                    "one_eighty_day_avg": round(metrics.one_eighty_day_avg, 2),
                    "direction": metrics.direction,
                    "momentum": round(metrics.momentum, 4),
                    "stability": round(metrics.stability, 4),
                    "sources_confirmed": 1,
                    "sources_checked": 1,
                    "data_source": "inline_pytrends",
                },
            )
        except Exception as e:
            return self._fallback_result(str(e))

    def _fetch_trends(self, product_name: str):
        if not PYTRENDS_AVAILABLE:
            raise ValueError("pytrends library not available")

        lookback_map = {
            30: "today 1-m",
            90: "today 3-m",
            180: "today 6-m",
            365: "today 1-y",
            1825: "today 5-y",
        }
        tf = lookback_map.get(self.lookback_days, "today 6-m")
        try:
            pytrends = TrendReq(hl="en-US", tz=360, retries=2, backoff_factor=0.5)
        except TypeError:
            pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload(
            [product_name], cat=0, timeframe=tf, geo="", gprop=""
        )
        df = pytrends.interest_over_time()
        if df.empty:
            raise ValueError("No trend data returned from Google Trends")
        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])
        return df[product_name]

    def _calculate_metrics(self, series) -> TrendMetrics:
        total_points = len(series)
        seven = series.tail(min(7, total_points)).mean()
        thirty = series.tail(min(30, total_points)).mean()
        ninety = series.tail(min(90, total_points)).mean()
        one_eighty = series.tail(min(180, total_points)).mean()

        denom = max(ninety, thirty)
        stability = min(ninety, thirty) / denom if denom > 0 else 0.0

        if total_points >= 2:
            x = np.arange(len(series))
            slope = np.polyfit(x, series.values, 1)[0]
        else:
            slope = 0.0

        if slope > 0.5:
            direction = "rising"
        elif slope < -0.5:
            direction = "declining"
        else:
            direction = "stable"

        if total_points >= 60:
            recent = series.tail(30).mean()
            older = series.tail(60).head(30).mean()
            momentum = (recent - older) / (older + 1)
        else:
            momentum = 0.0

        return TrendMetrics(
            seven_day_avg=seven,
            thirty_day_avg=thirty,
            ninety_day_avg=ninety,
            one_eighty_day_avg=one_eighty,
            direction=direction,
            momentum=momentum,
            stability=stability,
        )

    def _calculate_score(self, metrics: TrendMetrics) -> float:
        base = metrics.stability * 20.0

        if metrics.direction == "rising":
            base += 3.0
        elif metrics.direction == "declining":
            base -= 5.0

        if metrics.momentum > 0.05:
            base += 2.0
        elif metrics.momentum < -0.05:
            base -= 2.0

        if metrics.seven_day_avg > metrics.thirty_day_avg:
            base += 2.0
        elif metrics.seven_day_avg < metrics.thirty_day_avg * 0.5:
            base -= 3.0

        return max(0.0, min(20.0, base))

    def _fallback_result(self, reason: str) -> EngineResult:
        return EngineResult(
            score=10.0,
            max_score=20.0,
            confidence=0.3,
            details={
                "seven_day_avg": 0,
                "thirty_day_avg": 0,
                "ninety_day_avg": 0,
                "one_eighty_day_avg": 0,
                "direction": "unknown",
                "momentum": 0,
                "stability": 0,
                "fallback_reason": reason,
                "sources_confirmed": 0,
                "sources_checked": 1,
                "data_source": "fallback",
            },
            error=reason,
        )
