# ⌨️ Command Reference

This document provides a complete reference for running the Food Recipes IR Pipeline.

---

## 🛠 Setup

Before running any commands, ensure you have the dependencies installed:

```bash
# Create and activate virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r packaging/requirements.txt
```

---

## 🚀 The "Easy Way" (Full Stack)

To start the entire application (API Server + Frontend) with a single command:

```bash
./start_all.sh
```

This will:
1.  Check for necessary data and indices.
2.  Start the Python API server on port `8000`.
3.  Start the Next.js Frontend on port `3000`.
4.  Open the application in your browser.

To stop everything:
```bash
./stop_all.sh
```

---

## 🔧 The "Hard Way" (Manual Pipeline Execution)

If you want to run individual stages of the pipeline manually, use the `packaging/run.sh` wrapper script.

### 1. Crawling (Data Collection)
Download raw HTML recipes from Food.com.

```bash
# Download 100 recipes (for testing)
./packaging/run.sh crawl 100

# Download 5000 recipes (production)
./packaging/run.sh crawl 5000
```
*Output:* `data/raw/*.html`

### 2. Parsing (Normalization)
Extract structured data (JSON-LD) from the raw HTML files.

```bash
./packaging/run.sh parse

# Or directly with Python:
python -m parser.run --raw data/raw --out data/normalized --verbose
```
*Output:* `data/normalized/recipes_foodcom.jsonl`

### 3. Wikipedia Processing
Extract culinary entities from the Wikipedia XML dump.

```bash
# Test on a small sample (fast)
./packaging/run.sh wiki_parse_test

# Process the FULL dump (takes hours, requires PySpark)
./packaging/run.sh wiki_parse
```
*Output:* `data/normalized/wiki_culinary.jsonl` and `entities/wiki_gazetteer.tsv`

### 4. Enrichment (Entity Linking)
Link recipes to Wikipedia entities using the Aho-Corasick algorithm.

```bash
./packaging/run.sh enrich
```
*Output:* `data/normalized/recipes_enriched.jsonl`

### 5. Indexing
Build the inverted index for fast searching.

```bash
# Build Simple TSV Index (Fast, no dependencies)
python -m indexer.run --input data/normalized/recipes_enriched.jsonl --out index/v1

# Build PyLucene BM25 Index (Recommended)
python -m indexer.lucene_indexer --input data/normalized/recipes_enriched.jsonl --output index/v2 --similarity bm25

# Build PyLucene TF-IDF Index
python -m indexer.lucene_indexer --input data/normalized/recipes_enriched.jsonl --output index/v2_tfidf --similarity tfidf
```
*Output:* `index/v1/` (TSV), `index/v2/` (Lucene BM25), `index/v2_tfidf/` (Lucene TF-IDF)

---

## 🔍 Search Commands (CLI)

### Basic Search Syntax

```bash
python -m search_cli.run --index <INDEX_PATH> --metric <bm25|tfidf> --q "<QUERY>" --k <NUM_RESULTS>
```

### Output Formats

| Flag | Description | Use Case |
|------|-------------|----------|
| (none) | Full formatted output with Wikipedia entities | **Demo/Presentation** |
| `--detail` | Detailed recipe info from JSONL | **Full recipe view** |
| `--json` | JSON output with all metadata | **Programmatic use** |
| `--quiet` | Minimal: `doc_id\tscore` per line | **Scripting/Benchmarks** |

---

### 📋 Simple TSV Index (index/v1)

```bash
# BM25 - Default output (full with highlights)
python -m search_cli.run --index index/v1 --metric bm25 --q "italian sausage soup" --k 5

# BM25 - JSON output (for programmatic use)
python -m search_cli.run --index index/v1 --metric bm25 --q "italian sausage soup" --k 5 --json

# BM25 - Quiet output (for benchmarks - just doc_id and score)
python -m search_cli.run --index index/v1 --metric bm25 --q "italian sausage soup" --k 5 --quiet

# TF-IDF - Default output
python -m search_cli.run --index index/v1 --metric tfidf --q "italian sausage soup" --k 5

# TF-IDF - JSON output
python -m search_cli.run --index index/v1 --metric tfidf --q "italian sausage soup" --k 5 --json
```

---

### 🔷 PyLucene BM25 Index (index/v2)

```bash
# BM25 - Full output with Wikipedia entities
python -m search_cli.run --index index/v2 --metric bm25 --q "mexican beef tacos" --k 5

# BM25 - Detailed recipe info
python -m search_cli.run --index index/v2 --metric bm25 --q "mexican beef tacos" --k 5 --detail

# BM25 - JSON output
python -m search_cli.run --index index/v2 --metric bm25 --q "mexican beef tacos" --k 5 --json

# BM25 - Quiet/minimal output
python -m search_cli.run --index index/v2 --metric bm25 --q "mexican beef tacos" --k 5 --quiet

# BM25 with TIME FILTER (max 30 minutes)
python -m search_cli.run --index index/v2 --metric bm25 --q "pasta" --k 5 --filter '{"max_total_minutes": 30}'

# BM25 with CUISINE FILTER
python -m search_cli.run --index index/v2 --metric bm25 --q "chicken" --k 5 --filter '{"cuisine": "Italian"}'

# BM25 with MULTIPLE FILTERS
python -m search_cli.run --index index/v2 --metric bm25 --q "soup" --k 5 --filter '{"max_total_minutes": 45, "cuisine": "Asian"}'
```

---

### 🔶 PyLucene TF-IDF Index (index/v2_tfidf)

```bash
# TF-IDF - Full output
python -m search_cli.run --index index/v2_tfidf --metric tfidf --q "vegan chocolate mousse" --k 5

# TF-IDF - JSON output
python -m search_cli.run --index index/v2_tfidf --metric tfidf --q "vegan chocolate mousse" --k 5 --json

# TF-IDF - Quiet output
python -m search_cli.run --index index/v2_tfidf --metric tfidf --q "vegan chocolate mousse" --k 5 --quiet
```

---

## 🧪 Benchmark Test Queries (5 queries × 4 systems)

### Query 1: "italian sausage soup"
```bash
# S1: Simple BM25
python -m search_cli.run --index index/v1 --metric bm25 --q "italian sausage soup" --k 5

# S2: Simple TF-IDF
python -m search_cli.run --index index/v1 --metric tfidf --q "italian sausage soup" --k 5

# L1: PyLucene BM25
python -m search_cli.run --index index/v2 --metric bm25 --q "italian sausage soup" --k 5

# L2: PyLucene TF-IDF
python -m search_cli.run --index index/v2_tfidf --metric tfidf --q "italian sausage soup" --k 5
```

### Query 2: "thai peanut noodles"
```bash
python -m search_cli.run --index index/v1 --metric bm25 --q "thai peanut noodles" --k 5
python -m search_cli.run --index index/v1 --metric tfidf --q "thai peanut noodles" --k 5
python -m search_cli.run --index index/v2 --metric bm25 --q "thai peanut noodles" --k 5
python -m search_cli.run --index index/v2_tfidf --metric tfidf --q "thai peanut noodles" --k 5
```

### Query 3: "low carb cheesecake"
```bash
python -m search_cli.run --index index/v1 --metric bm25 --q "low carb cheesecake" --k 5
python -m search_cli.run --index index/v1 --metric tfidf --q "low carb cheesecake" --k 5
python -m search_cli.run --index index/v2 --metric bm25 --q "low carb cheesecake" --k 5
python -m search_cli.run --index index/v2_tfidf --metric tfidf --q "low carb cheesecake" --k 5
```

### Query 4: "vegan chocolate mousse"
```bash
python -m search_cli.run --index index/v1 --metric bm25 --q "vegan chocolate mousse" --k 5
python -m search_cli.run --index index/v1 --metric tfidf --q "vegan chocolate mousse" --k 5
python -m search_cli.run --index index/v2 --metric bm25 --q "vegan chocolate mousse" --k 5
python -m search_cli.run --index index/v2_tfidf --metric tfidf --q "vegan chocolate mousse" --k 5
```

### Query 5: "mexican beef tacos"
```bash
python -m search_cli.run --index index/v1 --metric bm25 --q "mexican beef tacos" --k 5
python -m search_cli.run --index index/v1 --metric tfidf --q "mexican beef tacos" --k 5
python -m search_cli.run --index index/v2 --metric bm25 --q "mexican beef tacos" --k 5
python -m search_cli.run --index index/v2_tfidf --metric tfidf --q "mexican beef tacos" --k 5
```

---

## 📊 Evaluation

Run standard IR metrics (Precision@k, Recall@k, MAP, NDCG) to evaluate search quality.

```bash
# Default evaluation (BM25, k=5,10,20)
python -m eval.run --index index/v1 --metric bm25

# Evaluation with TF-IDF
python -m eval.run --index index/v1 --metric tfidf

# Custom K values
python -m eval.run --index index/v1 --metric bm25 --k 5 10

# Full evaluation with custom paths
python -m eval.run \
  --index index/v1 \
  --queries eval/queries.tsv \
  --qrels eval/qrels.tsv \
  --output eval/metrics_custom.tsv \
  --metric bm25 \
  --k 5 10 20
```
*Output:* `eval/metrics.tsv`

---

## 🧹 Cleanup

To remove all generated data and start fresh:

```bash
./packaging/run.sh clean
```
**Warning:** This deletes all downloaded and processed data!

---

## 📝 Quick Reference Table

| Task | Command |
|------|---------|
| Build Simple index | `python -m indexer.run --input data/normalized/recipes_enriched.jsonl --out index/v1` |
| Build Lucene BM25 | `python -m indexer.lucene_indexer --input data/normalized/recipes_enriched.jsonl --output index/v2` |
| Build Lucene TF-IDF | `python -m indexer.lucene_indexer --input data/normalized/recipes_enriched.jsonl --output index/v2_tfidf --similarity tfidf` |
| Search (preview) | `python -m search_cli.run --index index/v1 --metric bm25 --q "query" --k 5` |
| Search (JSON) | `python -m search_cli.run --index index/v1 --metric bm25 --q "query" --k 5 --json` |
| Search (quiet) | `python -m search_cli.run --index index/v1 --metric bm25 --q "query" --k 5 --quiet` |
| Search with filter | `python -m search_cli.run --index index/v2 --metric bm25 --q "pasta" --k 5 --filter '{"max_total_minutes": 30}'` |
| Evaluate | `python -m eval.run --index index/v1 --metric bm25` |
