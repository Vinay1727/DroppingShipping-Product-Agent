from typing import Dict

from ..models import EngineResult, FinalReport


class ScoringEngine:
    ENGINE_ORDER = [
        "trend", "demand", "margin", "seasonality", "intent",
        "competition", "content", "supplier", "reviews", "logistics",
    ]

    def score(self, engine_results: Dict[str, EngineResult], product_name: str) -> FinalReport:
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
        confidence_score = (total_confirmed / total_checked * 100.0) if total_checked > 0 else 0.0
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
            generated_at="",
        )

    def _calculate_survival(self, engine_results: Dict[str, EngineResult]) -> float:
        scores = {
            "trend": engine_results.get("trend"),
            "demand": engine_results.get("demand"),
            "seasonality": engine_results.get("seasonality"),
            "intent": engine_results.get("intent"),
        }
        total = sum(er.score for er in scores.values() if er is not None)
        survival = (total / 60.0) * 100.0
        return max(5.0, min(99.0, survival))

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
