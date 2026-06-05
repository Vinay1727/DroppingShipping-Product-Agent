import sys
import json
import os

from dotenv import load_dotenv

load_dotenv()

from .models import ProductInput
from .agents.product_agent import ProductAgent
from .config import settings


def print_report(report):
    product = report.product_name
    score = report.product_score
    confidence = report.confidence_score
    survival = report.survival_probability
    decision = report.decision

    print()
    print(f"Product {product}")
    print()

    engine_names = {
        "trend": "trend stability",
        "demand": "demand confirmation",
        "margin": "margin",
        "seasonality": "seasonality",
        "intent": "market intent",
        "competition": "competition",
        "content": "content potential",
        "supplier": "supplier verification",
        "reviews": "review verification",
        "logistics": "logistics",
    }

    for key, label in engine_names.items():
        if key in report.engine_scores:
            er = report.engine_scores[key]
            print(f"  {label}: {er.score:.0f}/{er.max_score:.0f}")

    print()
    print(f"  Final score: {score:.0f}/100")
    print(f"  confidence: {confidence:.0f}%")
    print(f"  90-Day survival: {survival:.0f}%")
    print(f"  decision: {decision}")
    print()


def save_report(report, filename=None):
    folder = settings.REPORT_OUTPUT_FOLDER
    os.makedirs(folder, exist_ok=True)

    if not filename:
        safe_name = report.product_name.lower().replace(" ", "_")[:30]
        filename = f"{safe_name}_{report.generated_at[:10]}.json"

    path = os.path.join(folder, filename)
    data = {
        "product_name": report.product_name,
        "product_score": report.product_score,
        "confidence_score": report.confidence_score,
        "survival_probability": report.survival_probability,
        "decision": report.decision,
        "summary": report.summary,
        "generated_at": report.generated_at,
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
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def print_usage():
    print("AI Product Investment Analyst")
    print()
    print("Usage:")
    print('  python -m product_agent.app <product_name> <supplier_price> <selling_price>')
    print('  python -m product_agent.app --json <input_file>')
    print('  python -m product_agent.app --help')
    print()
    print("Arguments:")
    print("  product_name      Name of the product to analyze (in quotes)")
    print("  supplier_price    Your cost from supplier")
    print("  selling_price     Your intended selling price")
    print()
    print("Options:")
    print("  --json <file>     Read product input from JSON file")
    print("  --help            Show this help message")
    print()
    print("JSON input format:")
    print('  {"product_name": "dog hair remover", "supplier_price": 8, "selling_price": 35}')
    print()
    print("Example:")
    print('  python -m product_agent.app "dog hair remover" 8 35')
    print()
    print("Configuration:")
    print("  See example.env for environment variables")
    print("  GOOGLE_TRENDS_ENABLE=true  Enables Google Trends analysis")
    print("  MIN_MARGIN_PERCENT=60      Minimum acceptable margin threshold")


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h"):
        print_usage()
        sys.exit(0)

    if len(sys.argv) < 4:
        print_usage()
        sys.exit(1)

    if sys.argv[1] == "--json":
        with open(sys.argv[2]) as f:
            data = json.load(f)
        product = ProductInput(**data)
    else:
        product = ProductInput(
            product_name=sys.argv[1],
            supplier_price=float(sys.argv[2]),
            selling_price=float(sys.argv[3]),
        )

    agent = ProductAgent()
    report = agent.analyze(product)

    print_report(report)

    saved = save_report(report)
    print(f"  Report saved to: {saved}")


if __name__ == "__main__":
    main()
