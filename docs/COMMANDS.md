# ⌨️ Command Reference

This document provides a complete reference for running the Food Recipes IR Pipeline.

## 🛠 Setup

Before running any commands, ensure you have the dependencies installed:

```bash
# Create and activate virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r packaging/requirements.txt
```

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
# Build PyLucene Index (Recommended - BM25)
./packaging/run.sh index_lucene

# Build Simple TSV Index (Legacy/Baseline)
./packaging/run.sh index
```
*Output:* `index/v2/` (PyLucene) or `index/v1/` (TSV)

### 6. Search (CLI)
Test the search engine directly from the terminal.

```bash
# Search using PyLucene (supports filters)
./packaging/run.sh search_lucene "mexican chicken"

# Search with specific number of results
./packaging/run.sh search_lucene "pasta" 5

# Search using Legacy TSV index
./packaging/run.sh search "pasta"
```

## 📊 Evaluation

Run standard IR metrics (Precision@k, Recall@k, MAP, NDCG) to evaluate search quality.

```bash
./packaging/run.sh eval
```
*Output:* `eval/metrics.tsv`

## 🧹 Cleanup

To remove all generated data and start fresh:

```bash
./packaging/run.sh clean
```
**Warning:** This deletes all downloaded and processed data!
