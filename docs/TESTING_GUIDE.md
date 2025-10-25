# Testing Guide — Food Recipes IR Pipeline (Lupyne + BM25)

This guide provides comprehensive instructions for testing the Lupyne-based recipe search index, including basic searches, filtered queries, and evaluation runs.

---

## Prerequisites

Ensure you have:
- **PyLucene 10.0.0** and **Lupyne 3.3** installed (see `LUPYNE_INSTALL.md`)
- **Homebrew Python 3.14** (or compatible): `/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14`
- **Completed index build**: `index/lucene/v2/` exists with 5,646 recipes

---

## 1. Verify Index Exists

```bash
# Check index structure
ls -lh index/lucene/v2/

# Expected output: segments_* files, write.lock, etc.
# Total size: ~10-15 MB

# Count documents (using Python)
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 -c "
import lucene
lucene.initVM()
from lupyne import engine
searcher = engine.IndexSearcher('index/lucene/v2')
print(f'Total documents: {searcher.count()}')
"
# Expected: Total documents: 5646
```

---

## 2. Basic Search Queries

### Simple Query (No Filters)

```bash
# Search for "mexican chicken" (top 10 results)
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "mexican chicken" \
  --k 10

# Expected: 10 results with BM25 scores, URLs, and titles
```

### Multi-Term Query

```bash
# Search for "chocolate cake dessert"
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "chocolate cake dessert" \
  --k 5

# Expected: Chocolate cake recipes with dessert variations
```

### Cuisine-Specific Query

```bash
# Search for Italian pasta dishes
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "italian pasta" \
  --k 10

# Expected: Italian pasta recipes (carbonara, bolognese, etc.)
```

---

## 3. Filtered Searches

### Time-Constrained Query

```bash
# Quick recipes under 30 minutes
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "quick dinner" \
  --k 10 \
  --filter '{"max_total_minutes": 30}'

# Expected: Only recipes with total_minutes <= 30
```

### Must-Include Ingredients

```bash
# Recipes containing both garlic and tomato
# NOTE: Uses full-text search in ingredients_text field (not exact keyword match)
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "pasta sauce" \
  --k 10 \
  --filter '{"include_ingredients": ["garlic", "tomato"]}'

# Expected: Pasta sauce recipes with garlic AND tomato
# Sample results: "Shrimp and Pasta in a Tomato-Chile Cream Sauce", "Pasta Amatriciana"
```

### Cuisine Filter (OR)

```bash
# Mexican OR Italian cuisine
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "rice dish" \
  --k 10 \
  --filter '{"cuisine": ["Mexican", "Italian"]}'

# Expected: Recipes tagged as Mexican OR Italian
```

### Combined Filters

```bash
# Quick Mexican chicken under 45 minutes with specific ingredients
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "chicken tacos" \
  --k 5 \
  --filter '{
    "max_total_minutes": 45,
    "include_ingredients": ["chicken", "tortilla"]
  }'

# Expected: Chicken tacos/Mexican dishes under 45 min with chicken + tortilla
# Sample results: "Margarita Chicken", "Brazilian Chicken and Black Beans"
```

**Note:** `include_ingredients` uses **full-text search** in the `ingredients_text` field, not exact keyword matching. This means:
- "chicken" will match "chicken breast", "rotisserie chicken", etc.
- Ingredient terms are analyzed (lowercase, tokenized)
- More flexible than exact matching but less precise

---

## 4. Similarity Comparison (BM25 vs TF-IDF)

Currently, similarity is set at **indexing time** (not query time in Lupyne). To compare:

### BM25 (Default)

```bash
# Already using BM25 (index built with --similarity bm25)
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "chocolate chip cookies" \
  --k 5 \
  --similarity bm25
```

### TF-IDF (Requires Re-Indexing)

```bash
# Build TF-IDF index (separate index directory)
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 indexer/lucene_indexer.py \
  --input data/normalized/recipes_enriched.jsonl \
  --output index/lucene/v2_tfidf \
  --similarity tfidf

# Search TF-IDF index
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2_tfidf \
  --q "chocolate chip cookies" \
  --k 5 \
  --similarity tfidf
```

---

## 5. Evaluation Runs

### Run Evaluation on All Queries

```bash
# Execute evaluation script (uses eval/queries.tsv and eval/qrels.tsv)
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 eval/run.py \
  --index index/lucene/v2 \
  --queries eval/queries.tsv \
  --qrels eval/qrels.tsv \
  --output eval/runs/lucene_bm25_$(date +%Y%m%d_%H%M%S).tsv \
  --similarity bm25

# Output: TREC-formatted run file in eval/runs/
# Metrics: Precision@10, Recall@10, MAP
```

### Calculate Metrics

```bash
# After generating run file, calculate metrics
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 eval/run.py \
  --run eval/runs/lucene_bm25_*.tsv \
  --qrels eval/qrels.tsv \
  --metrics

# Output: P@5, P@10, Recall@10, MAP (appended to eval/metrics.tsv)
```

---

## 6. Wikipedia Knowledge Verification

### Check Wiki Links in Results

```bash
# Search and show full details (including wiki_abstracts)
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "basil pesto" \
  --k 3 \
  --verbose

# Expected: Results include wiki_abstracts field with Wikipedia knowledge
```

### Verify Wiki Entity Linking

```bash
# Check how many recipes have Wikipedia links
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 -c "
import json
with open('data/normalized/recipes_enriched.jsonl') as f:
    recipes = [json.loads(line) for line in f]
    
with_wiki = sum(1 for r in recipes if r.get('wiki_links'))
total_links = sum(len(r.get('wiki_links', [])) for r in recipes)

print(f'Recipes with wiki_links: {with_wiki}/{len(recipes)} ({with_wiki/len(recipes)*100:.1f}%)')
print(f'Total Wikipedia links: {total_links}')
print(f'Average links per recipe: {total_links/len(recipes):.2f}')
"

# Expected:
# Recipes with wiki_links: 5144/5646 (91.1%)
# Total Wikipedia links: 14102
# Average links per recipe: 2.50
```

---

## 7. Performance Benchmarks

### Indexing Speed

```bash
# Re-index and time it
time /usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 indexer/lucene_indexer.py \
  --input data/normalized/recipes_enriched.jsonl \
  --output index/lucene/v2_test \
  --similarity bm25

# Expected: ~2-3 seconds for 5,646 documents on modern hardware
# Log shows: "Indexing time: X.XX seconds"
```

### Search Latency

```bash
# Measure search time
time /usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "italian pasta carbonara" \
  --k 100

# Expected: <1 second for 100 results
```

---

## 8. Advanced Testing

### Range Query Testing

```bash
# Recipes between 15-30 minutes
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 search_cli/run.py \
  --index index/lucene/v2 \
  --q "easy dinner" \
  --k 20 \
  --filter '{
    "min_total_minutes": 15,
    "max_total_minutes": 30
  }'
```

### Keyword Field Exact Match

```bash
# Exact match on ingredient keyword field
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 -c "
import lucene
lucene.initVM()
from lupyne import engine

searcher = engine.IndexSearcher('index/lucene/v2')

# Create term query for exact ingredient
from org.apache.lucene.index import Term
from org.apache.lucene.search import TermQuery

term = Term('ingredients_kw', 'chicken')
query = TermQuery(term)
hits = searcher.search(query, count=5)

print(f'Recipes with exact ingredient \"chicken\": {hits.count}')
for hit in hits:
    print(f'- {hit[\"title_text\"][:60]}')
"
```

---

## 9. Common Issues & Troubleshooting

### Issue: "0 results found"

**Diagnosis:**
```bash
# Check if fields are indexed
/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14 -c "
import lucene
lucene.initVM()
from org.apache.lucene.index import DirectoryReader, MultiTerms
from org.apache.lucene.store import FSDirectory
from java.nio.file import Paths

directory = FSDirectory.open(Paths.get('index/lucene/v2'))
reader = DirectoryReader.open(directory)

for field in ['title_text', 'ingredients_text']:
    terms = MultiTerms.getTerms(reader, field)
    print(f'{field}: {\"INDEXED\" if terms else \"NOT indexed\"}')

reader.close()
"
```

**Solution:** Re-index with `indexOptions='DOCS_AND_FREQS_AND_POSITIONS'`

### Issue: "AlreadyClosedException" warning

**Explanation:** Lupyne cleanup bug (harmless), index reader closed prematurely.

**Workaround:** Ignore warning, search results are still valid.

### Issue: Filters not working

**Check filter syntax:**
```bash
# Correct JSON format (single quotes outside, double inside)
--filter '{"cuisine": ["Mexican"], "max_total_minutes": 30}'

# NOT: --filter "{\"cuisine\": [\"Mexican\"]}"
```

### Issue: "bytesPerDim" mismatch for time filter

**Error:**
```
java.lang.IllegalArgumentException: field="total_minutes" was indexed with bytesPerDim=8 but this query has bytesPerDim=4
```

**Explanation:** Lupyne `dimensions=1` uses 8-byte Long fields, not 4-byte Int.

**Solution:** Use `LongPoint.newRangeQuery()` instead of `IntPoint.newRangeQuery()` (already fixed in code).

### Issue: Ingredient filter returns unexpected results

**Explanation:** `include_ingredients` uses full-text search (analyzed/tokenized), not exact keyword matching.

**Examples:**
- Filter `"chicken"` matches: "chicken breast", "grilled chicken", "chicken thighs"
- Filter `"tomato"` matches: "tomatoes", "tomato sauce", "cherry tomatoes"

**Workaround:** Be specific with ingredient names, or use multiple terms (e.g., `["chicken breast"]`).

---

## 10. Expected Results Summary

| Query | Expected Top Result | Score Range |
|-------|-------------------|-------------|
| "mexican chicken nachos" | Nachos / Mexican Chicken | 15-20 |
| "chocolate cake" | Chocolate Cake recipes | 12-18 |
| "italian pasta" | Carbonara / Bolognese | 10-15 |
| "quick dinner" (< 30 min) | Fast recipes | 8-12 |

**Quality Metrics (from eval/metrics.tsv):**
- **P@10:** ~0.70-0.85 (precision at rank 10)
- **Recall@10:** ~0.60-0.75
- **MAP:** ~0.65-0.80 (mean average precision)

---

## 11. Cleanup

```bash
# Remove test indexes
rm -rf index/lucene/v2_test index/lucene/v2_tfidf

# Clear evaluation runs
rm -f eval/runs/*.tsv

# Reset logs
rm -f data/logs/*.log
```

---

## 12. Next Steps

1. **Run full evaluation** with `packaging/run.sh eval`
2. **Compare BM25 vs TF-IDF** by building both indexes and comparing metrics
3. **Analyze failed queries** in `eval/queries.tsv` with low scores
4. **Document findings** in `docs/wiki_3pages.md`

---

## Notes

- **Field Boosts:** Applied at query time (title^2.0, ingredients^1.5, instructions^1.0, wiki_abstracts^1.0)
- **Wikipedia Knowledge:** 91.1% of recipes have Wikipedia entity links (14,102 total links)
- **Index Size:** ~12 MB for 5,646 documents
- **Indexing Time:** ~2.8 seconds (BM25, with Wikipedia abstracts)
- **Search Latency:** <100ms for top-10 results

---

**For more details, see:**
- `LUPYNE_INSTALL.md` — Installation guide
- `docs/CLI_GUIDE.md` — Full CLI reference
- `docs/SEARCH_CLI_INDEX.md` — Search CLI documentation
- `.github/copilot-instructions.md` — Project requirements

---

**Version:** 2025-01-25 (Lupyne 3.3 + PyLucene 10.0.0)
