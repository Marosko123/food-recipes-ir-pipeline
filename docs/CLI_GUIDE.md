# Food Recipes Search CLI — Complete User Guide

**Author:** Maroš Bednár (AIS ID: 116822)  
**Email:** bednarmaros341@gmail.com  
**Version:** 1.0  
**Last Updated:** October 21, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Command Syntax](#command-syntax)
3. [Search Metrics](#search-metrics)
4. [Filter Options](#filter-options)
5. [Common Use Cases](#common-use-cases)
6. [Advanced Examples](#advanced-examples)
7. [Performance Tips](#performance-tips)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Basic Search (BM25)
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chicken pasta" \
  --k 5
```

### Get Help
```bash
python3 search_cli/run.py --help
```

---

## Command Syntax

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--index INDEX` | Path to index directory | `data/index/v1` |
| `--q QUERY` | Search query string | `"chicken pasta"` |

### Optional Arguments

| Argument | Default | Description | Example |
|----------|---------|-------------|---------|
| `--metric` | `bm25` | Ranking algorithm: `tfidf` or `bm25` | `--metric tfidf` |
| `--k` | `10` | Number of results to return | `--k 20` |
| `--filter` | None | JSON filter string | `--filter '{"max_total_minutes": 30}'` |

---

## Search Metrics

### BM25 (Recommended)
**Best Match 25** — Probabilistic ranking algorithm (industry standard)

**Characteristics:**
- Non-normalized scores (0 to ∞)
- Saturates term frequency (diminishing returns for repeated terms)
- Document length normalization (penalizes long documents)
- Better for production use

**Example:**
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chocolate cake" \
  --k 5
```

**Output:**
```
1. Mini Pound cake / Cupcakes With chocolate Bits
   Score: 37.8466
   URL: https://www.food.com/recipe/...
```

### TF-IDF
**Term Frequency–Inverse Document Frequency** — Classic vector space model

**Characteristics:**
- Normalized scores (0.0 to 1.0)
- Cosine similarity between query and document vectors
- Linear term frequency growth
- More interpretable scores

**Example:**
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric tfidf \
  --q "chocolate cake" \
  --k 5
```

**Output:**
```
1. Mini Pound cake / Cupcakes With chocolate Bits
   Score: 1.6942
   URL: https://www.food.com/recipe/...
```

### When to Use Which?

| Scenario | Recommended Metric |
|----------|-------------------|
| Production search | **BM25** |
| Academic/research | **TF-IDF** |
| Comparing algorithms | Both |
| Interpretable scores | **TF-IDF** |

---

## Filter Options

### Time Filters

```bash
# Recipes under 30 minutes
--filter '{"max_total_minutes": 30}'

# Recipes over 60 minutes
--filter '{"min_total_minutes": 60}'

# Quick prep recipes
--filter '{"max_prep_minutes": 15}'

# Long cooking recipes
--filter '{"min_cook_minutes": 120}'

# Time range
--filter '{"min_total_minutes": 30, "max_total_minutes": 60}'
```

### Rating Filters

```bash
# Highly rated recipes (4+ stars)
--filter '{"min_rating": 4.0}'

# Recipes with many reviews
--filter '{"min_review_count": 100}'

# Perfect recipes only
--filter '{"min_rating": 4.8, "min_review_count": 50}'
```

### Nutrition Filters

```bash
# Low calorie recipes
--filter '{"max_calories": 300}'

# High protein recipes
--filter '{"min_protein": 25}'

# Low carb recipes
--filter '{"max_carbs": 20}'

# Low fat recipes
--filter '{"max_fat": 10}'

# Low sugar recipes
--filter '{"max_sugar": 5}'

# Low sodium recipes
--filter '{"max_sodium": 500}'

# Combined nutrition filters
--filter '{"max_calories": 400, "min_protein": 30, "max_carbs": 25}'
```

### Category Filters

```bash
# Specific cuisine
--filter '{"cuisine": ["Italian", "Mediterranean"]}'

# Specific category
--filter '{"category": ["Dessert", "Snack"]}'

# Specific ingredients (must contain)
--filter '{"ingredients": ["chicken", "garlic"]}'

# Dietary preferences
--filter '{"dietary": ["vegetarian", "gluten-free"]}'

# Cooking method
--filter '{"cooking_method": ["baking", "grilling"]}'

# Meal type
--filter '{"meal_type": ["breakfast", "lunch"]}'
```

### Advanced Filters

```bash
# Recipe complexity
--filter '{"min_ingredients": 5, "max_ingredients": 10}'

--filter '{"min_instructions": 3, "max_instructions": 8}'

# Specific author
--filter '{"author": ["Chef John", "Gordon Ramsay"]}'

# Must have images
--filter '{"has_image": true}'

# Yield/servings
--filter '{"min_yield": 4, "max_yield": 8}'

# Keywords
--filter '{"keywords": ["quick", "easy", "healthy"]}'
```

---

## Common Use Cases

### 1. Quick Weeknight Dinner
**Goal:** Fast, easy, highly-rated recipes

```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chicken dinner" \
  --k 5 \
  --filter '{"max_total_minutes": 30, "min_rating": 4.0}'
```

### 2. Healthy Lunch
**Goal:** Low calorie, high protein, vegetarian

```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "salad bowl" \
  --k 5 \
  --filter '{"max_calories": 400, "min_protein": 15, "dietary": ["vegetarian"]}'
```

### 3. Party Dessert
**Goal:** Impressive, chocolate, well-reviewed

```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chocolate dessert" \
  --k 10 \
  --filter '{"min_rating": 4.5, "min_review_count": 50, "category": ["Dessert"]}'
```

### 4. Meal Prep Sunday
**Goal:** High yield, can be frozen, balanced nutrition

```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "meal prep chicken rice" \
  --k 5 \
  --filter '{"min_yield": 6, "max_calories": 500, "min_protein": 25}'
```

### 5. Italian Night
**Goal:** Authentic Italian, pasta-based, reasonable time

```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "pasta italian" \
  --k 10 \
  --filter '{"cuisine": ["Italian"], "max_total_minutes": 45, "min_rating": 4.0}'
```

### 6. Low-Carb Diet
**Goal:** Keto-friendly, high protein, low carbs

```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chicken vegetables" \
  --k 5 \
  --filter '{"max_carbs": 15, "min_protein": 30, "max_calories": 400}'
```

### 7. Kids-Friendly
**Goal:** Simple, familiar ingredients, quick

```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "kid friendly dinner" \
  --k 5 \
  --filter '{"max_ingredients": 8, "max_total_minutes": 30, "min_rating": 4.0}'
```

### 8. Breakfast Ideas
**Goal:** Morning meals, quick prep, energizing

```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "breakfast eggs" \
  --k 10 \
  --filter '{"max_prep_minutes": 15, "meal_type": ["breakfast"], "min_protein": 15}'
```

---

## Advanced Examples

### Multi-Filter Complex Search
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "mexican chicken" \
  --k 3 \
  --filter '{
    "max_total_minutes": 45,
    "min_rating": 4.0,
    "max_calories": 500,
    "min_protein": 25,
    "cuisine": ["Mexican"],
    "dietary": ["gluten-free"]
  }'
```

### Compare TF-IDF vs BM25
```bash
# TF-IDF search
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric tfidf \
  --q "pasta carbonara" \
  --k 5 > results_tfidf.txt

# BM25 search
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "pasta carbonara" \
  --k 5 > results_bm25.txt

# Compare
diff results_tfidf.txt results_bm25.txt
```

### Batch Search Script
```bash
#!/bin/bash
# batch_search.sh - Search multiple queries

QUERIES=(
  "chicken pasta"
  "chocolate cake"
  "mexican tacos"
  "italian pizza"
  "vegetarian soup"
)

for query in "${QUERIES[@]}"; do
  echo "=== Searching: $query ==="
  python3 search_cli/run.py \
    --index data/index/v1 \
    --metric bm25 \
    --q "$query" \
    --k 3
  echo ""
done
```

### Export Results to JSON
```bash
# Using jq to parse and format
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "pasta" \
  --k 10 \
  --filter '{"max_total_minutes": 30}' \
  2>/dev/null | grep -A 3 "^[0-9]" > results.txt
```

### Performance Benchmarking
```bash
#!/bin/bash
# benchmark_search.sh - Measure search performance

echo "Benchmarking search performance..."

for metric in tfidf bm25; do
  echo "Testing $metric..."
  time python3 search_cli/run.py \
    --index data/index/v1 \
    --metric $metric \
    --q "chicken pasta salad vegetables" \
    --k 20 \
    > /dev/null 2>&1
done
```

---

## Performance Tips

### 1. **Use BM25 for Faster Results**
BM25 is generally faster than TF-IDF for large result sets.

### 2. **Limit Results Count**
Use `--k` to limit results for faster response:
```bash
--k 10  # Fast
--k 100 # Slower
```

### 3. **Use Specific Queries**
More specific queries = fewer documents to score:
```bash
# Slow (broad query)
--q "food"

# Fast (specific query)
--q "italian pasta carbonara bacon"
```

### 4. **Filter Early**
Use filters to reduce search space:
```bash
# Without filter: searches all 5646 docs
--q "chicken"

# With filter: searches ~1200 docs
--q "chicken" --filter '{"max_total_minutes": 30}'
```

### 5. **Cache Index in Memory**
Index is loaded once per run. For multiple searches, keep process alive.

---

## Troubleshooting

### Problem: "Index directory not found"
**Solution:**
```bash
# Verify index exists
ls -la data/index/v1/

# Rebuild index if missing
python3 -m indexer.run \
  --input data/normalized/recipes.jsonl \
  --out data/index/v1
```

### Problem: "No results found"
**Possible causes:**
1. Query too specific
2. Filters too restrictive
3. Typos in query

**Solutions:**
```bash
# Try broader query
--q "chicken" # instead of "grilled chicken breast with herbs"

# Remove filters
# Remove --filter argument

# Check for typos
--q "pasta" # instead of "posta"
```

### Problem: "Empty query after tokenization"
**Cause:** Query contains only stopwords

**Solution:**
```bash
# Bad (only stopwords)
--q "the and or"

# Good (content words)
--q "chicken pasta"
```

### Problem: Invalid JSON in filter
**Cause:** Malformed JSON string

**Solutions:**
```bash
# Use single quotes outside, double quotes inside
--filter '{"max_total_minutes": 30}'

# Escape properly in scripts
FILTER="{\"max_total_minutes\": 30}"
--filter "$FILTER"

# Validate JSON first
echo '{"max_total_minutes": 30}' | python3 -m json.tool
```

### Problem: Slow search with filters
**Cause:** Complex filters require loading full recipe data

**Solution:**
```bash
# Use simpler filters when possible
--filter '{"max_total_minutes": 30}'  # Fast

# Avoid complex nutrition filters if not needed
--filter '{"max_calories": 300, "min_protein": 25, "max_fat": 10}'  # Slower
```

---

## Output Format

### Search Results Structure
```
Search Results for 'QUERY' (METRIC):
============================================================

1. Recipe Title with **highlighted** terms
   Score: XX.XXXX
   URL: https://www.food.com/recipe/...
   ID: doc_id

2. ...

Search Statistics:
  Queries processed: N
  Total results: M
  Average results per query: X.XX
```

### Interpreting Scores

**BM25 Scores:**
- Range: 0 to ∞ (unbounded)
- Typical: 10-40 for good matches
- Higher = better match
- Not normalized

**TF-IDF Scores:**
- Range: 0.0 to 1.0 (normalized)
- Typical: 0.5-1.0 for good matches
- Higher = better match
- Represents cosine similarity

### Highlighted Terms
Terms matching your query are wrapped in `**bold**`:
```
Mediterranean **chicken** and **pasta**
```

---

## Statistics Interpretation

### Queries Processed
Number of searches performed in current session.

### Total Results
Number of documents matching the query (before pagination).

### Average Results Per Query
Mean number of matching documents across all queries.

**Example:**
```
Search Statistics:
  Queries processed: 1
  Total results: 1219
  Average results per query: 1219.00
```
This means 1,219 documents contained "chicken" or "pasta".

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (invalid args, index not found, etc.) |

**Check exit code:**
```bash
python3 search_cli/run.py --index data/index/v1 --q "pasta" --k 5
echo $?  # 0 = success, 1 = error
```

---

## Integration Examples

### Shell Script Integration
```bash
#!/bin/bash
# search_wrapper.sh

QUERY="$1"
MAX_TIME="${2:-30}"

python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "$QUERY" \
  --k 5 \
  --filter "{\"max_total_minutes\": $MAX_TIME}"
```

**Usage:**
```bash
bash search_wrapper.sh "chicken pasta" 30
```

### Python Integration
```python
import subprocess
import json

def search_recipes(query, k=10, filters=None):
    cmd = [
        "python3", "search_cli/run.py",
        "--index", "data/index/v1",
        "--metric", "bm25",
        "--q", query,
        "--k", str(k)
    ]
    
    if filters:
        cmd.extend(["--filter", json.dumps(filters)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

# Example usage
results = search_recipes("chicken pasta", k=5, filters={"max_total_minutes": 30})
print(results)
```

---

## Filter Reference Table

### Complete Filter List

| Filter Key | Type | Description | Example |
|-----------|------|-------------|---------|
| `max_total_minutes` | int | Maximum total time | `30` |
| `min_total_minutes` | int | Minimum total time | `60` |
| `max_prep_minutes` | int | Maximum prep time | `15` |
| `max_cook_minutes` | int | Maximum cook time | `45` |
| `min_rating` | float | Minimum rating (0-5) | `4.0` |
| `max_rating` | float | Maximum rating (0-5) | `5.0` |
| `min_review_count` | int | Minimum review count | `100` |
| `max_calories` | int | Maximum calories | `500` |
| `min_calories` | int | Minimum calories | `200` |
| `max_protein` | float | Maximum protein (g) | `30` |
| `min_protein` | float | Minimum protein (g) | `20` |
| `max_carbs` | float | Maximum carbs (g) | `25` |
| `min_carbs` | float | Minimum carbs (g) | `10` |
| `max_fat` | float | Maximum fat (g) | `15` |
| `min_fat` | float | Minimum fat (g) | `5` |
| `max_sugar` | float | Maximum sugar (g) | `10` |
| `min_sugar` | float | Minimum sugar (g) | `0` |
| `max_sodium` | float | Maximum sodium (mg) | `500` |
| `min_sodium` | float | Minimum sodium (mg) | `0` |
| `cuisine` | list[str] | Cuisine types | `["Italian", "Mexican"]` |
| `category` | list[str] | Recipe categories | `["Dessert", "Main"]` |
| `ingredients` | list[str] | Must contain ingredients | `["chicken", "garlic"]` |
| `dietary` | list[str] | Dietary restrictions | `["vegetarian", "vegan"]` |
| `cooking_method` | list[str] | Cooking methods | `["baking", "grilling"]` |
| `meal_type` | list[str] | Meal types | `["breakfast", "dinner"]` |
| `author` | list[str] | Recipe authors | `["Chef John"]` |
| `has_image` | bool | Must have image | `true` |
| `min_ingredients` | int | Min ingredient count | `5` |
| `max_ingredients` | int | Max ingredient count | `10` |
| `min_instructions` | int | Min instruction steps | `3` |
| `max_instructions` | int | Max instruction steps | `8` |
| `min_yield` | int | Minimum servings | `4` |
| `max_yield` | int | Maximum servings | `8` |
| `keywords` | list[str] | Must contain keywords | `["quick", "easy"]` |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│               FOOD RECIPES SEARCH CLI QUICK REF                 │
├─────────────────────────────────────────────────────────────────┤
│ BASIC SEARCH                                                    │
│   python3 search_cli/run.py --index data/index/v1 \            │
│     --q "QUERY" --k 10                                          │
│                                                                 │
│ WITH METRIC                                                     │
│   --metric bm25      # BM25 (recommended)                      │
│   --metric tfidf     # TF-IDF                                  │
│                                                                 │
│ WITH FILTERS                                                    │
│   --filter '{"max_total_minutes": 30}'                         │
│   --filter '{"min_rating": 4.0, "max_calories": 500}'         │
│                                                                 │
│ COMMON FILTERS                                                  │
│   Time:       max_total_minutes, max_prep_minutes              │
│   Rating:     min_rating, min_review_count                     │
│   Nutrition:  max_calories, min_protein, max_carbs            │
│   Category:   cuisine, category, dietary                       │
│                                                                 │
│ HELP                                                            │
│   python3 search_cli/run.py --help                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Changelog

### Version 1.0 (October 21, 2025)
- Initial release
- BM25 and TF-IDF support
- 20+ filter types
- Comprehensive documentation

---

## Support

**Issues or Questions?**
- Author: Maroš Bednár
- Email: bednarmaros341@gmail.com
- AIS ID: 116822

**Project Repository:**
- GitHub: food-recipes-ir-pipeline

---

**Happy Searching! 🍳🔍**
