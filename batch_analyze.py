import csv
import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from .models import ProductInput
from .agents.product_agent import ProductAgent
from .config import settings


def batch_analyze(csv_path: str, output_path: str = None):
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        products = list(reader)

    if not products:
        print("No products found in CSV")
        sys.exit(1)

    print(f"Loaded {len(products)} products from {csv_path}")
    print()

    agent = ProductAgent()
    all_results = []

    for i, row in enumerate(products, 1):
        name = row.get("product_name", "").strip()
        try:
            cost = float(row.get("supplier_price", 0))
            price = float(row.get("selling_price", 0))
        except (ValueError, TypeError):
            print(f"  [{i}] SKIPPED {name!r} — invalid prices")
            all_results.append({
                "product_name": name,
                "error": f"Invalid prices: supplier_price={row.get('supplier_price')}, selling_price={row.get('selling_price')}",
            })
            continue

        product = ProductInput(
            product_name=name,
            supplier_price=cost,
            selling_price=price,
        )

        print(f"  [{i}/{len(products)}] {name} (cost=${cost:.0f}, price=${price:.0f}) ... ", end="", flush=True)
        try:
            report = agent.analyze(product)
            entry = {
                "product_name": report.product_name,
                "product_score": report.product_score,
                "confidence_score": report.confidence_score,
                "survival_probability": report.survival_probability,
                "decision": report.decision,
                "summary": report.summary,
                "generated_at": report.generated_at,
                "supplier_price": cost,
                "selling_price": price,
                "engine_scores": {
                    k: {
                        "score": v.score,
                        "max_score": v.max_score,
                        "confidence": v.confidence,
                        "details": v.details,
                        "error": v.error,
                    }
                    for k, v in report.engine_scores.items()
                },
            }
            all_results.append(entry)
            print(f"{report.product_score:.0f}/100 → {report.decision}")
        except Exception as e:
            print(f"ERROR: {e}")
            all_results.append({
                "product_name": name,
                "supplier_price": cost,
                "selling_price": price,
                "error": str(e),
            })

    combined = {
        "generated_at": datetime.now().isoformat(),
        "total_products": len(all_results),
        "results": all_results,
    }

    if not output_path:
        safe_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(settings.REPORT_OUTPUT_FOLDER, f"batch_report_{safe_ts}.json")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(combined, f, indent=2)

    print()
    print(f"Combined report saved to: {output_path}")
    print()

    print("Summary:")
    print(f"  {'Product':<25} {'Score':>6} {'Decision':<15}")
    print(f"  {'-'*25} {'-'*6} {'-'*15}")
    for r in all_results:
        if "error" in r and r.get("error"):
            print(f"  {r['product_name']:<25} {'ERR':>6} {r['error']:<15}")
        else:
            print(f"  {r['product_name']:<25} {r['product_score']:>5.0f}/100 {r['decision']:<15}")


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "products.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    batch_analyze(csv_path, output_path)


if __name__ == "__main__":
    main()
