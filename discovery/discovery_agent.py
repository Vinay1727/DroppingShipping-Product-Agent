import json
import logging
import os
import sys
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discovery.google_trends_discovery import discover_from_trends
from discovery.reddit_discovery import discover_from_reddit
from discovery.discovery_scoring import rank_candidates, filter_strong_products, STRONG_PRODUCT_MIN_SCORE
from discovery.product_filter import filter_candidates
from discovery.product_memory import init_db, save_discovery_result, save_research_result, save_daily_snapshot

from config import settings
from models import ProductInput
from agents.product_agent import ProductAgent


def discover_products(max_candidates=100):
    all_candidates = []

    logger.info("Discovering from Google Trends...")
    try:
        trends = discover_from_trends(max_candidates=max_candidates // 2)
        logger.info(f"  Found {len(trends)} candidates from Google Trends")
        all_candidates.extend(trends)
    except Exception as e:
        logger.warning(f"  Google Trends discovery failed: {e}")

    logger.info("Discovering from Reddit...")
    try:
        reddit = discover_from_reddit(max_candidates=max_candidates // 2)
        logger.info(f"  Found {len(reddit)} candidates from Reddit")
        all_candidates.extend(reddit)
    except Exception as e:
        logger.warning(f"  Reddit discovery failed: {e}")

    all_candidates = _deduplicate(all_candidates)

    logger.info(f"Total unique candidates after dedup: {len(all_candidates)}")

    qualified, rejected = filter_candidates(all_candidates)
    if not qualified:
        logger.warning("No qualified product candidates found!")
        return [], rejected

    scored = rank_candidates(qualified, top_n=100)
    strong = filter_strong_products(scored)
    logger.info(f"Strong products (score ≥ {STRONG_PRODUCT_MIN_SCORE}): {len(strong)}/{len(scored)}")

    if len(strong) < 10:
        weak = [c for c in scored if c.get("discovery_score", 0) < STRONG_PRODUCT_MIN_SCORE]
        needed = min(10 - len(strong), len(weak))
        if needed > 0:
            logger.info(f"Padding with top {needed} lower-scored products")
            strong.extend(weak[:needed])
    strong = strong[:50]
    return strong, rejected


def _deduplicate(candidates):
    seen = set()
    unique = []

    for c in candidates:
        product = c.get("product", "").strip().lower()
        if not product or product in seen:
            continue
        seen.add(product)
        unique.append(c)

    return unique


def analyze_top_candidates(candidates, top_n=10):
    results = []
    agent = ProductAgent()

    logger.info(f"\nAnalyzing top {top_n} candidates...")

    for i, c in enumerate(candidates[:top_n]):
        product_name = c["product"]
        logger.info(f"  [{i+1}/{top_n}] {product_name}...")

        try:
            product = ProductInput(
                product_name=product_name,
                supplier_price=0.0,
                selling_price=0.0,
            )
            report = agent.analyze(product)

            results.append({
                "rank": i + 1,
                "product": product_name,
                "discovery_source": c.get("source", "unknown"),
                "discovery_score": c.get("discovery_score", 0),
                "product_score": report.product_score,
                "confidence_score": report.confidence_score,
                "survival_probability": report.survival_probability,
                "decision": report.decision,
                "summary": report.summary,
                "health": report.health.model_dump() if report.health else None,
            })

        except Exception as e:
            logger.warning(f"    Error analyzing {product_name}: {e}")
            results.append({
                "rank": i + 1,
                "product": product_name,
                "discovery_source": c.get("source", "unknown"),
                "discovery_score": c.get("discovery_score", 0),
                "error": str(e),
            })

        time.sleep(0.5)

    return results


def generate_report(candidates, analyzed, rejected=None, output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "reports")

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"top_opportunities_{timestamp}.json"
    path = os.path.join(output_dir, filename)

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_candidates_discovered": len(candidates) + len(rejected) if rejected else len(candidates),
        "qualified_candidates": len(candidates),
        "rejected_candidates": len(rejected) if rejected else 0,
        "candidates": candidates,
        "top_10_analysis": analyzed,
    }
    if rejected:
        report["rejected"] = rejected[:50]

    with open(path, "w") as f:
        json.dump(report, f, indent=2)

    return path


def print_results(analyzed):
    print()
    print("=" * 70)
    print("  TOP 10 OPPORTUNITIES")
    print("=" * 70)
    print()
    print(f"  {'Rank':<6} {'Product':<30} {'Score':<8} {'Confidence':<12} {'Decision':<12}")
    print("  " + "-" * 68)

    for r in analyzed:
        score = r.get("product_score", 0)
        conf = r.get("confidence_score", 0)
        decision = r.get("decision", "Error")
        product = r["product"][:28]
        rank = r["rank"]
        print(f"  {rank:<6} {product:<30} {score:<8.0f} {conf:<12.0f} {decision:<12}")

    print()
    print(f"  Full report saved with all {len(analyzed)} analyzed candidates")


def main():
    logger.info("=" * 60)
    logger.info("  PRODUCT DISCOVERY AGENT")
    logger.info("=" * 60)

    init_db()

    candidates, rejected = discover_products(max_candidates=100)

    if not candidates:
        print()
        print("  No qualified product candidates found.")
        if rejected:
            print(f"  ({len(rejected)} candidates rejected by product filter)")
        return

    print()
    print(f"  Top 50 Qualified Candidates ({len(rejected)} rejected by filter):")
    print(f"  {'#':<4} {'Product':<35} {'Source':<16} {'Score':<8} {'Category':<12}")
    print(f"  " + "-" * 75)
    for i, c in enumerate(candidates[:50], 1):
        product = c["product"][:33]
        source = c.get("source", "?")
        score = c.get("discovery_score", 0)
        category = c.get("category", "?")
        if source == "google_trends":
            extra = f"growth={c.get('growth', 0)}"
        elif source == "reddit":
            extra = f"mentions={c.get('mentions', 0)}"
        else:
            extra = f"score={c.get('discovery_score', 0)}"
        print(f"  {i:<4} {product:<35} {source:<16} {score:<8} {category:<12} ({extra})")

    for c in candidates:
        save_discovery_result(
            product_name=c["product"],
            discovery_score=c.get("discovery_score", 0),
            source=c.get("source", "unknown"),
            category=c.get("category"),
        )

    analyzed = analyze_top_candidates(candidates, top_n=10)

    for r in analyzed:
        if "error" not in r:
            save_research_result(
                product_name=r["product"],
                product_score=r.get("product_score", 0),
                confidence_score=r.get("confidence_score"),
                survival_probability=r.get("survival_probability"),
                decision=r.get("decision"),
            )

    save_daily_snapshot()

    report_path = generate_report(candidates, analyzed, rejected=rejected)
    print_results(analyzed)
    print(f"\n  Report: {report_path}")


if __name__ == "__main__":
    if "--memory" in sys.argv:
        from discovery.product_memory import memory_main
        memory_main()
    elif "--product" in sys.argv:
        from discovery.product_memory import print_product_detail
        idx = sys.argv.index("--product") + 1
        if idx < len(sys.argv):
            print_product_detail(sys.argv[idx])
        else:
            print("Usage: python -m discovery.discovery_agent --memory")
    else:
        main()
