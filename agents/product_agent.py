from typing import Dict, Optional
from datetime import datetime

from product_agent.config import settings
from product_agent.models import ProductInput, EngineResult, FinalReport, HealthReport, ProviderResult
from product_agent.providers import GoogleTrendsProvider, AmazonProvider, RedditProvider, SearchProvider
from product_agent.engines.trend_engine import TrendEngine
from product_agent.engines.demand_engine import DemandEngine
from product_agent.engines.margin_engine import MarginEngine
from product_agent.engines.seasonality_engine import SeasonalityEngine
from product_agent.engines.intent_engine import IntentEngine
from product_agent.engines.competition_engine import CompetitionEngine
from product_agent.engines.content_engine import ContentEngine
from product_agent.engines.supplier_engine import SupplierEngine
from product_agent.engines.review_engine import ReviewEngine
from product_agent.engines.logistics_engine import LogisticsEngine
from product_agent.engines.scoring_engine import ScoringEngine


class ProductAgent:
    PROVIDER_CONFIG = [
        ("google_trends", GoogleTrendsProvider, {"lookback_days": settings.TREND_LOOKBACK_DAYS}),
        ("reddit", RedditProvider, {}),
        ("search", SearchProvider, {}),
        ("amazon", AmazonProvider, {}),
    ]

    def __init__(self):
        self.providers: Dict[str, object] = {}
        for name, cls, kwargs in self.PROVIDER_CONFIG:
            self.providers[name] = cls(**kwargs)

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
        health = self._build_health_report()

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

        report = self.scoring_engine.score(engine_results, product.product_name, health=health)
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

    def _build_health_report(self) -> HealthReport:
        provider_healths = []
        for name, provider in self.providers.items():
            health = provider.check_health()
            provider_healths.append(health)

        priority1 = [p for p in provider_healths if p.priority == 1]
        priority1_working = sum(1 for p in priority1 if p.status == "working")
        priority1_total = len(priority1)

        if priority1_total > 0:
            coverage = (priority1_working / priority1_total) * 100.0
        else:
            coverage = 0.0

        if coverage >= 100:
            trust = "High"
        elif coverage >= 66:
            trust = "Medium"
        elif coverage >= 33:
            trust = "Low"
        else:
            trust = "Very Low"

        return HealthReport(
            providers=provider_healths,
            real_data_coverage=round(coverage, 0),
            trust_level=trust,
        )
