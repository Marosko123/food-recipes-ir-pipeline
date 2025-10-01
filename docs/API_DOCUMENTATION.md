# Food Recipes - API Documentation

**Author:** Maroš Bednár  
**Email:** bednarmaros341@gmail.com  
**AIS ID:** 116822  
**Version:** 1.0.0

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Setup & Launch API](#setup--launch-api)
3. [Crawler API](#crawler-api)
4. [Parser API](#parser-api)
5. [Indexer API](#indexer-api)
6. [Search API](#search-api)
7. [Entity Linking API](#entity-linking-api)
8. [Wikipedia Collection API](#wikipedia-collection-api)
9. [Web API](#web-api)
10. [Data Formats](#data-formats)
11. [Error Handling](#error-handling)

---

## 🎯 Overview

The Food Recipes project provides a comprehensive API for recipe information retrieval, including web crawling, parsing, indexing, search, and entity linking capabilities.

### Base URLs

- **Setup & Launch:** `python setup_and_launch.py`
- **Web API:** `http://localhost:8000/api/`
- **Frontend:** `http://localhost:3000/`

---

## 🚀 Setup & Launch API

### Main Launcher

**Script:** `setup_and_launch.py`

#### Command Line Options

```bash
python setup_and_launch.py [options]
```

**Options:**
- `--cli` - Force CLI mode
- `--gui` - Force GUI mode  
- `--install-deps` - Install dependencies only
- `--status` - Show project status only
- `--help` - Show help message

#### Examples

```bash
# GUI Mode (Recommended)
python setup_and_launch.py --gui

# CLI Mode
python setup_and_launch.py --cli

# Install Dependencies
python setup_and_launch.py --install-deps

# Check Status
python setup_and_launch.py --status
```

#### GUI Interface

The GUI provides:
- **System Information Display**
- **Project Status Monitoring**
- **One-click Phase Execution**
- **Real-time Output Display**
- **Data Management Tools**

---

## 🕷️ Crawler API

### Main Crawler

**Script:** `crawler/run.py`

#### Phase A: Seed Extraction

```bash
python -m crawler.run --phase seeds [options]
```

**Options:**
- `--seed` - Base URL (default: https://www.food.com)
- `--out` - Output directory (default: data/seed_analysis)
- `--qps` - Queries per second (default: 0.5)
- `--timeout` - Request timeout (default: 15)
- `--user-agent` - User agent string

**Output:**
- `data/seed_analysis/recipe_seeds.txt` - List of recipe URLs
- `data/seed_analysis/seed_stats.json` - Collection statistics
- `data/seed_analysis/report.md` - Detailed report

#### Phase B: Web Crawling

```bash
python -m crawler.run --phase crawl [options]
```

**Options:**
- `--seeds` - Seed URLs file
- `--out` - Output directory (default: data/raw)
- `--limit` - Maximum pages to crawl (default: 1000)
- `--qps` - Queries per second (default: 0.3)
- `--timeout` - Request timeout (default: 20)
- `--retries` - Number of retries (default: 3)

**Output:**
- `data/raw/{domain}/{doc_id}.html` - Raw HTML files
- `data/crawl.log` - Crawling logs

#### Examples

```bash
# Extract seeds
python -m crawler.run --phase seeds --out data/seed_analysis --qps 0.5

# Crawl pages
python -m crawler.run --phase crawl --seeds data/seed_analysis/recipe_seeds.txt --out data/raw --limit 1000 --qps 0.3
```

---

## 📝 Parser API

### Main Parser

**Script:** `parser/run.py`

```bash
python -m parser.run [options]
```

**Options:**
- `--raw` - Raw HTML directory (default: data/raw)
- `--out` - Output file (default: data/normalized/recipes.jsonl)
- `--stats` - Statistics file (default: data/normalized/parse_stats.json)
- `--workers` - Number of worker processes (default: 4)

**Output:**
- `data/normalized/recipes.jsonl` - Parsed recipe data
- `data/normalized/parse_stats.json` - Parsing statistics
- `data/parse.log` - Parsing logs

#### Example

```bash
python -m parser.run --raw data/raw --out data/normalized/recipes.jsonl
```

---

## 🔍 Indexer API

### Main Indexer

**Script:** `indexer/run.py`

```bash
python -m indexer.run [options]
```

**Options:**
- `--input` - Input JSONL file (default: data/normalized/recipes.jsonl)
- `--out` - Output directory (default: data/index/v1)
- `--min-df` - Minimum document frequency (default: 2)
- `--max-df` - Maximum document frequency (default: 0.8)

**Output:**
- `data/index/v1/terms.tsv` - Term statistics
- `data/index/v1/postings.tsv` - Inverted index
- `data/index/v1/docmeta.tsv` - Document metadata

#### Example

```bash
python -m indexer.run --input data/normalized/recipes.jsonl --out data/index/v1
```

---

## 🔎 Search API

### Main Search CLI

**Script:** `search_cli/run.py`

```bash
python -m search_cli.run [options]
```

**Options:**
- `--index` - Index directory (default: data/index/v1)
- `--metric` - Ranking metric (tfidf|bm25, default: bm25)
- `--q` - Search query
- `--k` - Number of results (default: 10)
- `--filter` - JSON filter string
- `--fields` - Search fields (default: title,ingredients,instructions)

**Output:** JSON results with scores and snippets

#### Examples

```bash
# Basic search
python -m search_cli.run --index data/index/v1 --metric bm25 --q "chicken pasta" --k 10

# Filtered search
python -m search_cli.run --index data/index/v1 --metric bm25 --q "chicken pasta" --k 10 --filter '{"max_total_minutes":30,"cuisine":["Italian"]}'
```

---

## 🏷️ Entity Linking API

### Gazetteer Builder

**Script:** `entities/gazetteer_builder.py`

```bash
python -m entities.gazetteer_builder [options]
```

**Options:**
- `--output` - Output file (default: data/entities/gazetteer_ingredients.tsv)
- `--size` - Number of ingredients (default: 100)

**Output:**
- `data/entities/gazetteer_ingredients.tsv` - Ingredient gazetteer

### Entity Linker

**Script:** `entities/linker.py`

```bash
python -m entities.linker [options]
```

**Options:**
- `--input` - Input JSONL file
- `--gazetteer` - Gazetteer TSV file
- `--output` - Output JSONL file

**Output:**
- `data/entities/links.jsonl` - Entity links

#### Examples

```bash
# Build gazetteer
python -m entities.gazetteer_builder --output data/entities/gazetteer_ingredients.tsv

# Link entities
python -m entities.linker --input data/normalized/recipes.jsonl --gazetteer data/entities/gazetteer_ingredients.tsv --output data/entities/links.jsonl
```

---

## 📚 Wikipedia Collection API

### Main Collector

**Script:** `run_wikipedia_collection.py`

```bash
python run_wikipedia_collection.py [options]
```

**Options:**
- `--output` - Output directory (default: data/wikipedia_recipes)
- `--max-recipes` - Maximum recipes (default: 1000)
- `--max-ingredients` - Maximum ingredients (default: 500)
- `--test` - Test mode (50 recipes, 25 ingredients)
- `--verbose` - Verbose output
- `--categories-only` - Only category-based collection
- `--search-only` - Only search-based collection

**Output:**
- `data/wikipedia_recipes/wikipedia_recipes.jsonl` - Wikipedia recipes
- `data/wikipedia_recipes/wikipedia_ingredients.jsonl` - Wikipedia ingredients
- `data/wikipedia_recipes/collection_stats.json` - Collection statistics

#### Examples

```bash
# Test collection
python run_wikipedia_collection.py --test

# Full collection
python run_wikipedia_collection.py --max-recipes 1000 --max-ingredients 500

# Categories only
python run_wikipedia_collection.py --categories-only --max-recipes 500
```

---

## 🌐 Web API

### Flask API Server

**Script:** `api_server.py`

```bash
python api_server.py
```

**Base URL:** `http://localhost:8000`

#### Endpoints

##### Health Check

**GET** `/api/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-26T20:00:00Z",
  "version": "1.0.0"
}
```

##### Search Recipes

**POST** `/api/search`

**Request Body:**
```json
{
  "query": "chicken pasta",
  "metric": "bm25",
  "k": 10,
  "filter": {
    "max_total_minutes": 30,
    "cuisine": ["Italian"]
  }
}
```

**Response:**
```json
{
  "query": "chicken pasta",
  "metric": "bm25",
  "results": [
    {
      "doc_id": "12345",
      "title": "Chicken Pasta",
      "url": "https://www.food.com/recipe/...",
      "score": 0.85,
      "snippet": "Delicious chicken pasta recipe...",
      "ingredients": ["chicken", "pasta", "tomato"],
      "cooking_time": 30,
      "cuisine": ["Italian"]
    }
  ],
  "total_results": 1,
  "search_time_ms": 45
}
```

##### Get Recipe Details

**GET** `/api/recipe/{doc_id}`

**Response:**
```json
{
  "doc_id": "12345",
  "title": "Chicken Pasta",
  "url": "https://www.food.com/recipe/...",
  "ingredients": ["chicken", "pasta", "tomato"],
  "instructions": ["Step 1", "Step 2"],
  "times": {
    "prep_minutes": 15,
    "cook_minutes": 30,
    "total_minutes": 45
  },
  "cuisine": ["Italian"],
  "category": ["Main Course"],
  "yield": 4,
  "author": "Chef Name",
  "nutrition": {
    "calories": 450
  },
  "ratings": {
    "average": 4.5,
    "count": 100
  },
  "images": ["https://..."],
  "description": "Recipe description..."
}
```

##### Get Statistics

**GET** `/api/stats`

**Response:**
```json
{
  "total_recipes": 101,
  "total_ingredients": 500,
  "total_cuisines": 15,
  "index_size": 1633,
  "last_updated": "2025-09-26T20:00:00Z"
}
```

---

## 📊 Data Formats

### Recipe JSONL Format

Each line in the JSONL file represents one recipe:

```json
{
  "id": "12345",
  "url": "https://www.food.com/recipe/...",
  "title": "Recipe Title",
  "ingredients": ["ingredient1", "ingredient2"],
  "instructions": ["step1", "step2"],
  "times": {
    "prep_minutes": 15,
    "cook_minutes": 30,
    "total_minutes": 45
  },
  "cuisine": ["Italian"],
  "category": ["Main Course"],
  "tools": ["pan", "knife"],
  "yield": 4,
  "author": "Chef Name",
  "nutrition": {
    "calories": 450,
    "protein": 25,
    "carbs": 40,
    "fat": 15
  },
  "ratings": {
    "average": 4.5,
    "count": 100
  },
  "images": ["https://..."],
  "description": "Recipe description...",
  "keywords": ["tag1", "tag2"],
  "publication_date": "2023-01-01",
  "difficulty": "medium"
}
```

### Index Format

#### Terms TSV
```
term	df	idf
chicken	45	0.23
pasta	32	0.45
```

#### Postings TSV
```
term	field	docId	tf
chicken	title	12345	2
chicken	ingredients	12345	1
```

#### DocMeta TSV
```
docId	url	title	len_title	len_ing	len_instr
12345	https://...	Chicken Pasta	13	45	234
```

### Entity Links JSONL Format

```json
{
  "doc_id": "12345",
  "field": "ingredients",
  "start_offset": 10,
  "end_offset": 17,
  "surface": "chicken",
  "wiki_title": "Chicken",
  "confidence": 0.95
}
```

---

## ❌ Error Handling

### Common Error Codes

- **400 Bad Request** - Invalid request parameters
- **404 Not Found** - Resource not found
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "Search query cannot be empty",
    "details": "The 'query' parameter is required"
  },
  "timestamp": "2025-09-26T20:00:00Z"
}
```

### Rate Limiting

- **Crawler:** 0.3 requests per second
- **Wikipedia API:** 1 request per second
- **Web API:** 100 requests per minute per IP

### Retry Logic

- **Crawler:** 3 retries with exponential backoff
- **Wikipedia API:** 3 retries with 1-second delay
- **Web API:** No retry logic (client responsibility)

---

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
export FLASK_ENV=development
export FLASK_DEBUG=1
export API_HOST=0.0.0.0
export API_PORT=8000

# Crawler Configuration
export CRAWLER_QPS=0.3
export CRAWLER_TIMEOUT=20
export CRAWLER_RETRIES=3

# Wikipedia Configuration
export WIKIPEDIA_QPS=1.0
export WIKIPEDIA_TIMEOUT=30
```

### Configuration Files

- `config.json` - Main configuration
- `logging.conf` - Logging configuration
- `robots.txt` - Crawler rules

---

## 📈 Performance

### Benchmarks

- **Crawling:** ~25 pages per minute
- **Parsing:** ~100 recipes per minute
- **Indexing:** ~1000 recipes per minute
- **Search:** <50ms average response time

### Optimization Tips

1. **Use appropriate QPS rates** for crawling
2. **Enable parallel processing** for parsing
3. **Use SSD storage** for better I/O performance
4. **Increase memory** for large datasets
5. **Use connection pooling** for web requests

---

## 🧪 Testing

### Unit Tests

```bash
python -m pytest tests/
```

### Integration Tests

```bash
python -m pytest tests/integration/
```

### API Tests

```bash
python -m pytest tests/api/
```

### Load Tests

```bash
python -m pytest tests/load/
```

---

## 📚 Examples

### Complete Workflow

```bash
# 1. Setup
python setup_and_launch.py --install-deps

# 2. Extract seeds
python -m crawler.run --phase seeds --out data/seed_analysis

# 3. Crawl pages
python -m crawler.run --phase crawl --seeds data/seed_analysis/recipe_seeds.txt --out data/raw --limit 100

# 4. Parse recipes
python -m parser.run --raw data/raw --out data/normalized/recipes.jsonl

# 5. Build index
python -m indexer.run --input data/normalized/recipes.jsonl --out data/index/v1

# 6. Test search
python -m search_cli.run --index data/index/v1 --metric bm25 --q "chicken pasta" --k 5

# 7. Launch web interface
python api_server.py &
cd frontend && python -m http.server 3000 &
```

### Python API Usage

```python
from search_cli.run import SearchEngine

# Initialize search engine
se = SearchEngine('data/index/v1')

# Search recipes
results = se.search('chicken pasta', metric='bm25', k=10)

# Print results
for result in results:
    print(f"{result['title']}: {result['score']:.3f}")
```

---

## 🆘 Support

For questions, issues, or contributions:

- **Email:** bednarmaros341@gmail.com
- **Project:** Food Recipes - Recipes IR Pipeline
- **AIS ID:** 116822

---

**Last Updated:** September 26, 2025  
**Version:** 1.0.0
