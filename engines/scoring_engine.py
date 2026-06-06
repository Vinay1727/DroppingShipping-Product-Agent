from typing import Dict, Optional

from product_agent.models import EngineResult, FinalReport, HealthReport, ProviderHealth


class ScoringEngine:
    ENGINE_ORDER = [
        "trend", "demand", "margin", "seasonality", "intent",
        "competition", "content", "supplier", "reviews", "logistics",
    ]

    ENGINE_WEIGHTS = {
        "trend": 0.20,
        "demand": 0.20,
        "margin": 0.15,
        "seasonality": 0.10,
        "intent": 0.05,
        "competition": 0.10,
        "content": 0.05,
        "supplier": 0.05,
        "reviews": 0.05,
        "logistics": 0.05,
    }

    def score(
        self,
        engine_results: Dict[str, EngineResult],
        product_name: str,
        health: Optional[HealthReport] = None,
    ) -> FinalReport:
        normalized_scores = {}
        total_confirmed = 0
        total_checked = 0
        raw_sum = 0.0

        for engine_name in self.ENGINE_ORDER:
            result = engine_results.get(engine_name)
            if result is None:
                continue
            normalized = result.score / result.max_score if result.max_score > 0 else 0
            normalized_scores[engine_name] = max(0.0, min(1.0, normalized))
            raw_sum += result.score
            total_confirmed += result.details.get("sources_confirmed", 0)
            total_checked += result.details.get("sources_checked", 0)

        product_score = min(raw_sum, 100.0)
        confidence_score = self._calculate_confidence(engine_results, health)
        survival_probability = self._calculate_survival(engine_results)
        decision = self._make_decision(product_score)

        return FinalReport(
            product_name=product_name,
            product_score=round(product_score, 1),
            confidence_score=round(confidence_score, 1),
            survival_probability=round(survival_probability, 1),
            decision=decision,
            engine_scores=engine_results,
            summary=self._generate_summary(product_score, decision, normalized_scores),
            health=health,
            generated_at="",
        )

    def _calculate_confidence(
        self,
        engine_results: Dict[str, EngineResult],
        health: Optional[HealthReport] = None,
    ) -> float:
        if health:
            priority1_working = sum(
                1 for p in health.providers if p.priority == 1 and p.status == "working"
            )
            priority1_total = sum(
                1 for p in health.providers if p.priority == 1
            )
            if priority1_total > 0:
                return (priority1_working / priority1_total) * 100.0

        total_confirmed = 0
        total_checked = 0
        for result in engine_results.values():
            total_confirmed += result.details.get("sources_confirmed", 0)
            total_checked += result.details.get("sources_checked", 0)
        return (total_confirmed / total_checked * 100.0) if total_checked > 0 else 0.0

    def _calculate_survival(self, engine_results: Dict[str, EngineResult]) -> float:
        total_weight = 0.0
        weighted_score = 0.0
        available = 0

        for engine, weight in self.ENGINE_WEIGHTS.items():
            result = engine_results.get(engine)
            if result is None:
                continue
            normalized = result.score / result.max_score if result.max_score > 0 else 0
            weighted_score += normalized * weight
            total_weight += weight
            available += 1

        if total_weight == 0 or available == 0:
            return 50.0

        survival = (weighted_score / total_weight) * 100.0
        return max(5.0, min(95.0, survival))

    def _make_decision(self, score: float) -> str:
        if score >= 90:
            return "Strong Buy"
        if score >= 80:
            return "Buy"
        if score >= 70:
            return "Watchlist"
        if score >= 60:
            return "Risky"
        return "Reject"

    def _generate_summary(self, score: float, decision: str, normalized: Dict[str, float]) -> str:
        strengths = []
        weaknesses = []
        for engine, ns in normalized.items():
            if ns >= 0.7:
                strengths.append(engine)
            elif ns < 0.4:
                weaknesses.append(engine)

        summary_parts = []
        summary_parts.append(f"{decision.upper()} - Score: {score:.0f}/100")

        if strengths:
            summary_parts.append(f"Strengths: {', '.join(strengths)}")
        if weaknesses:
            summary_parts.append(f"Weaknesses: {', '.join(weaknesses)}")
        if len(weaknesses) > 3:
            summary_parts.append("Multiple risk factors detected - proceed with caution")

        return " | ".join(summary_parts)

    def _empty_report(self, product_name: str) -> FinalReport:
        return FinalReport(
            product_name=product_name,
            product_score=0.0,
            confidence_score=0.0,
            survival_probability=0.0,
            decision="Reject",
            engine_scores={},
            summary="No data available to score",
        )
