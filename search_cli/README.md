# Search CLI — Quick Reference

Command-line interface for searching recipes using TF-IDF or BM25 ranking algorithms.

## Quick Start

```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chicken pasta" \
  --k 5
```

## Usage

```bash
python3 search_cli/run.py [OPTIONS]

Required:
  --index INDEX    Path to index directory (e.g., data/index/v1)
  --q QUERY        Search query string

Optional:
  --metric METRIC  Ranking algorithm: tfidf or bm25 (default: bm25)
  --k K           Number of results to return (default: 10)
  --filter JSON   JSON filter string (optional)
  --help          Show help message
```

## Examples

### Basic Search
```bash
# BM25 search (recommended)
python3 search_cli/run.py --index data/index/v1 --q "chocolate cake" --k 5

# TF-IDF search
python3 search_cli/run.py --index data/index/v1 --metric tfidf --q "pasta" --k 10
```

### With Time Filter
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --q "dinner" \
  --k 5 \
  --filter '{"max_total_minutes": 30}'
```

### With Multiple Filters
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --q "salad" \
  --k 5 \
  --filter '{"max_calories": 300, "min_rating": 4.0}'
```

## Common Filters

| Filter | Example | Description |
|--------|---------|-------------|
| `max_total_minutes` | `30` | Maximum cooking time |
| `min_rating` | `4.0` | Minimum recipe rating |
| `max_calories` | `500` | Maximum calories |
| `min_protein` | `25` | Minimum protein (g) |
| `cuisine` | `["Italian"]` | Cuisine type |

---

## 🎯 Demo Commands — Copy & Paste

### 1️⃣ Basic BM25 Search
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chocolate cake" \
  --k 5
```
**Returns:** Top 5 chocolate cake recipes ranked by BM25 score (relevance-based)

---

### 2️⃣ TF-IDF vs BM25 Comparison
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric tfidf \
  --q "chicken pasta" \
  --k 5
```

```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chicken pasta" \
  --k 5
```
**Returns:** Same query, different ranking algorithms — compare scores and ordering

---

### 3️⃣ Quick Weeknight Dinner (Time Filter)
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chicken dinner" \
  --k 5 \
  --filter '{"max_total_minutes": 30}'
```
**Returns:** Fast chicken dinner recipes (≤30 min total time)

---

### 4️⃣ Healthy Lunch (Nutrition Filters)
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "salad chicken" \
  --k 5 \
  --filter '{"max_calories": 400, "min_protein": 25}'
```
**Returns:** Healthy salads with max 400 calories and min 25g protein

---

### 5️⃣ Italian Night (Multi-Filter)
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "italian pasta" \
  --k 5 \
  --filter '{"cuisine": ["Italian"], "max_total_minutes": 45, "min_rating": 4.0}'
```
**Returns:** Italian pasta recipes under 45 minutes with 4+ star ratings

---

### 6️⃣ Party Dessert (High Ratings)
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "dessert cake" \
  --k 5 \
  --filter '{"min_rating": 4.5, "min_review_count": 50}'
```
**Returns:** Popular desserts with 4.5+ stars and 50+ reviews