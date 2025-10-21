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

## Full Documentation

For complete documentation including all filters, advanced examples, and troubleshooting:

📖 **[Complete CLI Guide](../docs/CLI_GUIDE.md)**

## Support

- **Author:** Maroš Bednár
- **Email:** bednarmaros341@gmail.com
- **AIS ID:** 116822
