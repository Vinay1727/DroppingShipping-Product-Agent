from typing import Dict, Optional
from datetime import datetime

from ..config import settings
from ..models import ProductInput, EngineResult, FinalReport, ProviderResult
from ..providers import GoogleTrendsProvider, AmazonProvider, RedditProvider
from ..engines.trend_engine import TrendEngine
from ..engines.demand_engine import DemandEngine
from ..engines.margin_engine import MarginEngine
from ..engines.seasonality_engine import SeasonalityEngine
from ..engines.intent_engine import IntentEngine
from ..engines.competition_engine import CompetitionEngine
from ..engines.content_engine import ContentEngine
from ..engines.supplier_engine import SupplierEngine
from ..engines.review_engine import ReviewEngine
from ..engines.logistics_engine import LogisticsEngine
from ..engines.scoring_engine import ScoringEngine


class ProductAgent:
    def __init__(self):
        self.providers: Dict[str, object] = {
            "google_trends": GoogleTrendsProvider(lookback_days=settings.TREND_LOOKBACK_DAYS),
            "amazon": AmazonProvider(),
            "reddit": RedditProvider(),
        }
        self.trend_engine = TrendEngine(lookback_days=settings.TREND_LOOKBACK_DAYS)
        self.demand_engine = DemandEngine()
        self.margin_engine = MarginEngine()
        self.seasonality_engine = SeasonalityEngine()
        self.intent_engine = IntentEngine()
        self.competition_engine = CompetitionEngine()
        self.content_engine = ContentEngine()
        self.supplier_engine = SupplierEngine()
        self.review_engine = ReviewEngine()
        self.logistics_engine = LogisticsEngine()
        self.scoring_engine = ScoringEngine()

    def analyze(self, product: ProductInput) -> FinalReport:
        provider_data = self._run_providers(product.product_name)

        engine_results: Dict[str, EngineResult] = {}

        trend_result = self.trend_engine.analyze(product.product_name, provider_data)
        engine_results["trend"] = trend_result

        demand_result = self.demand_engine.analyze(product, trend_result, provider_data)
        engine_results["demand"] = demand_result

        margin_result = self.margin_engine.analyze(product)
        engine_results["margin"] = margin_result

        seasonality_result = self.seasonality_engine.analyze(product, trend_result)
        engine_results["seasonality"] = seasonality_result

        intent_result = self.intent_engine.analyze(product, trend_result)
        engine_results["intent"] = intent_result

        competition_result = self.competition_engine.analyze(product, provider_data)
        engine_results["competition"] = competition_result

        content_result = self.content_engine.analyze(product)
        engine_results["content"] = content_result

        supplier_result = self.supplier_engine.analyze(product)
        engine_results["supplier"] = supplier_result

        review_result = self.review_engine.analyze(product, provider_data)
        engine_results["reviews"] = review_result

        logistics_result = self.logistics_engine.analyze(product)
        engine_results["logistics"] = logistics_result

        report = self.scoring_engine.score(engine_results, product.product_name)
        report.generated_at = datetime.now().isoformat()

        return report

    def _run_providers(self, product_name: str) -> Dict[str, ProviderResult]:
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = provider.fetch(product_name)
            except Exception as e:
                results[name] = ProviderResult(
                    source=name,
                    success=False,
                    error=str(e),
                )
        return results
