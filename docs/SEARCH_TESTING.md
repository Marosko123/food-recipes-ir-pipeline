# 🧪 Search Testing Guide

## Quick Start

Run all search tests with one command:

```bash
./test_searches.sh
```

Or directly with Python:

```bash
python3 test_all_searches.py
```

## What It Tests

The test suite automatically runs:

### 1. **Basic Searches** (BM25)
- `"chicken pasta"` - Common recipe search
- `"chocolate cake dessert"` - Dessert search
- `"mexican tacos"` - Cuisine-specific search

### 2. **Algorithm Comparison** (if Lupyne index available)
- `"italian pasta"` with BM25
- `"italian pasta"` with TF-IDF
- Compare scoring algorithms

### 3. **Time Filters** (if Lupyne index available)
- Quick dinner recipes `< 30 minutes`
- Easy breakfast recipes `< 15 minutes`

### 4. **Ingredient Filters** (if Lupyne index available)
- Recipes with `garlic + tomato`
- Recipes with `chicken + lemon`

### 5. **Cuisine Filters** (if Lupyne index available)
- Mexican OR Italian dishes
- Asian OR Chinese soups

### 6. **Combined Filters** (if Lupyne index available)
- Quick Mexican chicken `< 45 min + chicken + Mexican`

### 7. **Edge Cases**
- Empty query
- Non-existent terms
- Stopwords only

## Output Files

After running, you'll get:

1. **Detailed Log:** `data/logs/search_test.log`
   - Every test execution
   - Top 5 results per test
   - Scores, titles, Wikipedia entities
   - Performance metrics

2. **Summary JSON:** `data/logs/search_test_summary.json`
   - Machine-readable summary
   - All test results
   - Performance statistics

## View Results

```bash
# View full log
cat data/logs/search_test.log

# View with pager
less data/logs/search_test.log

# View summary JSON (pretty-printed)
cat data/logs/search_test_summary.json | python3 -m json.tool

# Quick summary (last 20 lines)
tail -20 data/logs/search_test.log
```

## Example Output

```
================================================================================
  TEST: Basic Search - Chicken Pasta
================================================================================
Query: 'chicken pasta'
Metric: BM25
Top-k: 10
Search completed in 0.123s
Results found: 10

TOP RESULTS:

  #1 [18.4532] Chicken Pasta Carbonara
      Doc ID: abc123
      Time: 25 min
      Cuisine: Italian
      Wiki Entities: 5
      Entity Breakdown: {'ingredient': 3, 'cuisine': 1, 'technique': 1}

  #2 [16.8901] Creamy Garlic Chicken Pasta
      Doc ID: def456
      Time: 30 min
      Cuisine: Italian
      Wiki Entities: 4
      Entity Breakdown: {'ingredient': 3, 'technique': 1}

...

================================================================================
TEST SUMMARY
================================================================================
Total Tests: 15
Successful: 15
Failed: 0
Success Rate: 100.0%

RESULTS BREAKDOWN:
  ✓ Basic Search - Chicken Pasta: 10 results in 0.123s
  ✓ Basic Search - Chocolate Cake: 10 results in 0.098s
  ✓ Mexican Tacos: 10 results in 0.105s
  ...

PERFORMANCE STATS:
  Total Search Time: 1.854s
  Average Search Time: 0.124s
  Fastest Search: 0.098s
  Slowest Search: 0.187s

Test Suite Duration: 2.15s
```

## Requirements

- **Index must exist:**
  - Lupyne: `index/lucene/v2/` (recommended)
  - OR TSV: `data/index/v1/` (baseline)

- **Build index if missing:**
  ```bash
  ./packaging/run.sh index_lucene  # Lupyne (full features)
  ./packaging/run.sh index         # TSV (basic)
  ```

## Troubleshooting

### "No index found"
```bash
# Build Lupyne index (recommended)
./packaging/run.sh index_lucene

# Or TSV index (basic)
./packaging/run.sh index
```

### "Import lucene failed"
- Lupyne tests will be skipped automatically
- TSV tests will still run
- Install PyLucene for full test coverage (see `LUPYNE_INSTALL.md`)

### "No results found"
- Check if recipes are indexed:
  ```bash
  python3 -c "
  from lupyne import engine
  import lucene
  lucene.initVM()
  s = engine.IndexSearcher('index/lucene/v2')
  print(f'Documents: {s.count}')
  "
  ```

## Custom Tests

Edit `test_all_searches.py` to add your own test queries:

```python
# Add new test
self.test_query(
    searcher,
    query="your custom query",
    k=10,
    filters={"max_total_minutes": 30},
    test_name="My Custom Test",
    metric="bm25"
)
```

## Integration with CI/CD

Run tests automatically:

```bash
# Run tests and check exit code
./test_searches.sh
if [ $? -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
```

---

**Author:** Maroš Bednár (AIS 116822)  
**Project:** Food Recipes IR Pipeline
