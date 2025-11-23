# Operational Guide & Command Reference

This guide provides specific command sets for various operational scenarios, from fresh installation to daily development and demonstration.

## ❓ FAQ: Do I need to rerun commands?

**Q: When I want to run a proper search with very good indexes, do I need to rerun some commands every run?**

**A: NO.**
Once you have built the index (Phase D), it persists on disk in `index/lucene/v2/`. You can run the search command (`search_lucene`) thousands of times without rebuilding anything.

**You only need to re-run commands if:**
1.  **Data Changes:** You crawled new recipes or updated the Wikipedia dump.
2.  **Code Changes:** You modified the `indexer` logic (e.g., changed field weights or added new fields).
3.  **Fresh Start:** You want to clean everything and prove reproducibility.

---

## 🛠️ Scenario 1: New Project Setup (First Time)
**Goal:** Get the code running on a new machine.
**Time:** ~5-10 minutes.

```bash
# 1. Clone the repository
git clone <repo_url>
cd VINF

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r packaging/requirements.txt

# 4. Install PyLucene (Critical for "very good indexes")
# See LUPYNE_INSTALL.md for details. On macOS with Homebrew:
# brew install coady/tap/pylucene
# pip install "lupyne[graphql,rest]"
```

---

## 🏗️ Scenario 2: Fresh Build (End-to-End Pipeline)
**Goal:** Go from zero to a fully searchable engine.
**Time:** ~4-6 hours (mostly crawling & wiki parsing).

```bash
# 1. Clean old data (Optional)
./packaging/run.sh clean

# 2. Crawl Recipes (The longest part)
# For production (all recipes):
# ./packaging/run.sh crawl 50000
# For testing/demo (fast):
./packaging/run.sh crawl 1000

# 3. Parse HTML to JSON
./packaging/run.sh parse

# 4. Parse Wikipedia (Spark Job)
# Requires data/enwiki/enwiki-latest-pages-articles.xml.bz2
./packaging/run.sh wiki_parse

# 5. Enrich Recipes (Combine Food.com + Wiki)
./packaging/run.sh enrich

# 6. Build PyLucene Index (The "Very Good Index")
./packaging/run.sh index_lucene
```

---

## 🔄 Scenario 3: Simulation of Scraping (Incremental)
**Goal:** Demonstrate the crawler working without waiting hours.
**Time:** ~1-2 minutes.

If you already have data but want to show the teacher that the crawler works:

```bash
# Crawl just 10 new recipes to show the process
./packaging/run.sh crawl 10
```

*Note: The crawler is smart. If you run it on existing URLs, it checks `last-modified` headers. To force a re-download of specific pages, you'd typically clear `data/raw` or use a specific URL list.*

---

## 🔄 Scenario 4: Simulation of Indexing (Re-indexing)
**Goal:** Rebuild the index after changing code or data.
**Time:** ~30 seconds (for ~5k recipes).

```bash
# 1. (Optional) Clear old index to be sure
rm -rf index/lucene/v2

# 2. Run the indexer
./packaging/run.sh index_lucene
```

*Output should show:* `✅ PyLucene index built successfully!`

---

## 🔎 Scenario 5: Search & Demonstration
**Goal:** Show off the results.
**Time:** Instant.

### A. Interactive Search (CLI)
```bash
# Basic search
./packaging/run.sh search_lucene "mexican chicken"

# With filters (JSON syntax)
python3 search_cli/run.py \
    --index index/lucene/v2 \
    --q "pasta" \
    --filter '{"max_total_minutes": 30, "cuisine": "Italian"}'
```

### B. Automated Demo (The "Wow" Factor)
Run the pre-prepared script that cycles through 8 different complex query types:
```bash
./demo_queries.sh
```

---

## 📊 Scenario 6: Evaluation
**Goal:** Generate scientific metrics (MAP, P@k) for the report.
**Time:** ~5 seconds.

```bash
# Run evaluation script
./packaging/run.sh eval
```

*Results are saved to `eval/metrics.tsv`.*

---

## ⏱️ Estimated Times Summary

| Operation | Small Data (1k docs) | Full Data (50k+ docs) | Notes |
| :--- | :--- | :--- | :--- |
| **Crawl** | ~15 mins | ~15+ hours | Limited by politeness (1 request/sec) |
| **Parse** | < 1 min | ~5 mins | CPU bound, very fast |
| **Wiki Parse** | ~5 mins (sample) | ~2-4 hours | Spark job, depends on CPU cores |
| **Enrich** | < 1 min | ~10 mins | Dictionary lookups |
| **Index (Lucene)** | < 10 sec | ~2-3 mins | Very fast |
| **Search** | < 10 ms | < 50 ms | Instant |

---

## 📜 Command Cheat Sheet

| Task | Command |
| :--- | :--- |
| **Start GUI** | `python3 setup_and_launch.py --gui` |
| **Crawl** | `./packaging/run.sh crawl <limit>` |
| **Parse** | `./packaging/run.sh parse` |
| **Index** | `./packaging/run.sh index_lucene` |
| **Search** | `./packaging/run.sh search_lucene "<query>"` |
| **Demo** | `./demo_queries.sh` |
| **Test** | `./packaging/run.sh test` |
