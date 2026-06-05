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
from ..models import ProviderResult
from .base_provider import BaseProvider


class GoogleTrendsProvider(BaseProvider):
    WORKING_TIMEFRAMES = ["today 5-y", "today 3-m", "today 1-m"]

    def __init__(self, lookback_days: int = 180):
        self.lookback_days = lookback_days

    def _do_fetch(self, product_name: str) -> ProviderResult:
        if not settings.GOOGLE_TRENDS_ENABLE:
            return ProviderResult(
                source="GoogleTrendsProvider",
                success=False,
                error="Google Trends disabled in config",
            )

        if not PYTRENDS_AVAILABLE:
            return ProviderResult(
                source="GoogleTrendsProvider",
                success=False,
                error="pytrends library not available",
            )

        lookback_map = {
            30: "today 1-m",
            90: "today 3-m",
            180: "today 5-y",
            365: "today 5-y",
            1825: "today 5-y",
        }
        preferred_tf = lookback_map.get(self.lookback_days, "today 5-y")
        timeframes = [preferred_tf] + [t for t in self.WORKING_TIMEFRAMES if t != preferred_tf]

        last_error = None
        series = None

        for tf in timeframes:
            try:
                pytrends = TrendReq(hl="en-US", tz=360, retries=2, backoff_factor=0.5)
            except TypeError:
                pytrends = TrendReq(hl="en-US", tz=360)

            try:
                pytrends.build_payload(
                    [product_name], cat=0, timeframe=tf, geo="", gprop=""
                )
                df = pytrends.interest_over_time()
            except ResponseError as e:
                last_error = f"timeframe={tf} failed: {e}"
                continue

            if df.empty:
                last_error = f"timeframe={tf} returned empty data"
                continue

            if "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])

            series = df[product_name]
            break

        if series is None:
            return ProviderResult(
                source="GoogleTrendsProvider",
                success=False,
                error=last_error or "All timeframes failed",
            )

        total_points = len(series)

        seven = float(series.tail(min(7, total_points)).mean())
        thirty = float(series.tail(min(30, total_points)).mean())
        ninety = float(series.tail(min(90, total_points)).mean())
        one_eighty = float(series.tail(min(180, total_points)).mean())

        denom = max(ninety, thirty)
        stability = min(ninety, thirty) / denom if denom > 0 else 0.0

        if total_points >= 2:
            x = np.arange(len(series))
            slope = float(np.polyfit(x, series.values, 1)[0])
        else:
            slope = 0.0

        if slope > 0.5:
            direction = "rising"
        elif slope < -0.5:
            direction = "declining"
        else:
            direction = "stable"

        if total_points >= 60:
            recent = float(series.tail(30).mean())
            older = float(series.tail(60).head(30).mean())
            momentum = (recent - older) / (older + 1)
        else:
            momentum = 0.0

        return ProviderResult(
            source="GoogleTrendsProvider",
            success=True,
            data={
                "seven_day_avg": round(seven, 2),
                "thirty_day_avg": round(thirty, 2),
                "ninety_day_avg": round(ninety, 2),
                "one_eighty_day_avg": round(one_eighty, 2),
                "direction": direction,
                "momentum": round(momentum, 4),
                "stability": round(stability, 4),
                "series_length": total_points,
            },
        )
