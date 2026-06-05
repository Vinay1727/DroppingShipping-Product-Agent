# Product Research Agent — Phase 1

AI-powered product research tool that analyzes product opportunities using real data providers and scoring engines.

## Architecture

```
User Input → Providers (fetch raw data) → Engines (process & score) → Scoring Engine → Final Report
```

### Layers

**Providers** (`providers/`) — fetch raw data from external APIs or fallback estimation
| Provider | Source | Data returned |
|---|---|---|
| `GoogleTrendsProvider` | pytrends / fallback | 7/30/90/180d avg, direction, momentum, stability |
| `AmazonProvider` | SerpAPI / PAAPI / estimation | product_count, avg_rating, total_reviews, price range |
| `RedditProvider` | PRAW / Pushshift.io | post_count_30d, comment_count, subreddits |

**Engines** (`engines/`) — process provider data into scores (0 to max_score)

| Engine | Max | What it measures |
|---|---|---|
| Trend | 20 | Google Trends stability, direction, momentum |
| Demand | 20 | Confirmed demand signals from providers + heuristic |
| Margin | 15 | Profit margin % from cost/price inputs |
| Seasonality | 10 | Evergreen vs seasonal vs event-based demand |
| Intent | 10 | Buyer intent signals in product name |
| Competition | 10 | Listing count → competition level |
| Content | 5 | Unique content idea generation |
| Supplier | 5 | Supplier quality (rating, orders, years) |
| Reviews | 3 | Amazon review score (rating + count + recency) |
| Logistics | 2 | Shipping time, tracking, warehouse coverage |

**Scoring Engine** (`engines/scoring_engine.py`)
- **Final score**: raw sum of all engine scores, capped at 100
- **Decision matrix**: 90-100 Strong Buy, 80-89 Buy, 70-79 Watchlist, 60-69 Risky, <60 Reject
- **Confidence**: confirmed_sources / total_sources_checked × 100
- **Survival probability**: (trend + demand + seasonality + intent) / 60 × 100

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp example.env .env
```

Then edit `.env` and fill in your keys:

| Variable | Required? | Purpose |
|---|---|---|
| `SERPAPI_API_KEY` | Recommended | Real Amazon product data |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Optional | Real Reddit discussion data |
| `GOOGLE_TRENDS_ENABLE` | Default: true | Google Trends historical data |

Without API keys, the system runs in **estimation mode** — providers generate realistic data from product name analysis. All engines still run and produce scores.

## Usage

### Single product analysis

```bash
python -m product_agent.app "product name" supplier_price selling_price
```

Example:
```bash
python -m product_agent.app "Dog Hair Remover" 8 35
```

### Batch analysis from CSV

Edit `products.csv` with your products and prices:

```csv
product_name,supplier_price,selling_price
Dog Hair Remover,8,35
Portable Blender,12,40
```

Then run:

```bash
python -m product_agent.batch_analyze products.csv
```

A single combined JSON report is saved to `reports/batch_report_*.json`.

### JSON input mode

```bash
python -m product_agent.app --json input.json
```

Where `input.json`:
```json
{"product_name": "Dog Hair Remover", "supplier_price": 8, "selling_price": 35}
```

## Testing

```bash
# Test Google Trends data
python test_trends.py "Dog Hair Remover"

# Test Amazon data + Demand/Competition/Review engines
python test_amazon_engines.py "Dog Hair Remover"
```

## Project Structure

```
product_agent/
├── agents/
│   └── product_agent.py       # Orchestrator: providers → engines → scoring
├── engines/
│   ├── trend_engine.py         # Google Trends scoring
│   ├── demand_engine.py        # Demand signal scoring
│   ├── margin_engine.py        # Profit margin scoring
│   ├── seasonality_engine.py   # Seasonal demand classification
│   ├── intent_engine.py        # Buyer intent analysis
│   ├── competition_engine.py   # Competition level scoring
│   ├── content_engine.py       # Content idea generation
│   ├── supplier_engine.py      # Supplier quality scoring
│   ├── review_engine.py        # Review analysis scoring
│   ├── logistics_engine.py     # Logistics quality scoring
│   └── scoring_engine.py       # Final score, decision, confidence
├── providers/
│   ├── base_provider.py        # Abstract base with caching/rate-limiting
│   ├── google_trends_provider.py
│   ├── amazon_provider.py
│   └── reddit_provider.py
├── data/                       # Seasonal/holiday data files
├── models.py                   # Pydantic models
├── config.py                   # Settings from environment
├── app.py                      # CLI entry point
├── batch_analyze.py            # Batch CSV analysis
├── test_trends.py              # Google Trends standalone test
├── test_amazon_engines.py      # Amazon + 3 engines test
├── requirements.txt
├── example.env                 # API key template
└── .gitignore
```

## API Key Setup

### SerpAPI (Amazon data — recommended)

1. Sign up at https://serpapi.com/ (100 free searches/month)
2. Copy your API key to `.env`: `SERPAPI_API_KEY=your_key_here`

### Reddit API (Reddit discussion data — optional)

1. Go to https://www.reddit.com/prefs/apps → create a script app
2. Copy client_id and client_secret to `.env`

## Phase 2+

Planned enhancements:
- Pinterest provider (visual trend signals)
- Meta Ads provider (ad competition data)
- AliExpress provider (supplier data)
- CJ Dropshipping provider (logistics data)
- OpenAI-powered content idea generation
- Smarter survival probability with multi-variable regression
