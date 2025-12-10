# 🍳 Food Recipes Information Retrieval System

A comprehensive End-to-End Information Retrieval system for cooking recipes, enriched with culinary knowledge from Wikipedia. This project demonstrates a full data pipeline from crawling to search, utilizing advanced IR techniques, Apache Spark, and PyLucene.

## 1. System Overview

### 1.1 Architecture

The system consists of 6 main components:

*   **Crawler**: Downloads HTML pages from Food.com respecting `robots.txt`.
*   **Parser**: Extracts structured data using a dual-layer approach (JSON-LD + Regex).
*   **Spark Wikipedia Parser**: Processes Wikipedia XML dumps using Apache Spark.
*   **Enricher**: Links recipes to Wikipedia entities using the **Aho-Corasick** algorithm.
*   **Indexer**: Builds an inverted index using **PyLucene** (BM25 ranking model).
*   **Searcher**: Provides millisecond-latency search with advanced filtering capabilities.

### 1.2 Data Sources

| Source | Description | Count |
| :--- | :--- | :--- |
| **Food.com** | Recipes with ingredients, instructions, and metadata | **5,646** recipes |
| **Wikipedia** | Culinary articles (enwiki dump) | **9,693** articles |
| **Gazetteer** | Entities for linking (including redirects) | **42,837** entities |

---

## 2. Crawler

### 2.1 Implementation

The crawler (`crawler/run.py`) is designed to be polite and robust:
*   **Robots.txt compliance**: Automatically parses and respects `Disallow` rules.
*   **Politeness**: Enforces a 1-second delay between requests.
*   **Storage**: Saves raw HTML files to `data/raw/www.food.com/`.

### 2.2 Statistics

*   **Downloaded Files**: 5,646 HTML files
*   **Target Domain**: www.food.com
*   **Content Type**: Recipes with images and metadata

---

## 3. Parser

### 3.1 Dual-Layer Parsing

To ensure maximum data quality, the parser uses a fallback strategy:
1.  **JSON-LD**: Extracts structured Schema.org data (primary source).
2.  **HTML Regex**: Fallback extraction from HTML structure if JSON-LD is missing.

### 3.2 Extracted Fields

| Field | Type | Example |
| :--- | :--- | :--- |
| `id` | string | "59018" |
| `title` | string | "Macaroon Pie Crust" |
| `ingredients` | list | ["1 1/3 cups macaroons", "1/2 cup margarine"] |
| `instructions` | list | ["Preheat oven to 375°F", ...] |
| `times` | dict | `{"prep": 5, "cook": 7, "total": 12}` |
| `cuisine` | list | ["French", "Kosher"] |
| `nutrition` | dict | `{"calories": "601.4", "fat": "45.5"}` |

### 3.3 Statistics

*   **Processed Files**: 5,646
*   **Success Rate**: 100%
*   **Processing Speed**: 200.9 recipes/sec
*   **Avg Ingredients**: 9.4 per recipe
*   **Avg Steps**: 7.0 per recipe

---

## 4. Wikipedia Spark Parser

### 4.1 Distributed Processing

We use **Apache Spark** to efficiently process the massive Wikipedia XML dump. The process runs in two phases:
1.  **Redirect Collection**: Maps all aliases/redirects to their canonical titles.
2.  **Article Extraction**: Filters and extracts culinary articles using the redirect map.

### 4.2 Filtering Logic

Articles are identified as "culinary" based on:
*   **Infoboxes**: `Infobox food`, `Infobox ingredient`, `Infobox prepared food`.
*   **Categories**: Foods, Dishes, Ingredients, Cuisines.
*   **Keywords**: Presence of multiple signals like "cooking", "recipe", "edible".

### 4.3 Statistics

*   **Total Culinary Articles**: **9,693**
    *   Dishes: 5,855 (60.4%)
    *   Ingredients: 3,441 (35.5%)
    *   Condiments: 169 (1.7%)
    *   Cuisines: 122 (1.3%)
*   **Enrichment Data**:
    *   With Origin Country: 5,372 (55.4%)
    *   With History Section: 3,569 (36.8%)
    *   Redirects Mapped: 30,321

---

## 5. Recipe Enricher (Entity Linking)

### 5.1 Algorithm

We use the **Aho-Corasick** algorithm for efficient multi-pattern string matching. This allows us to search for **42,837** entities simultaneously in recipe texts with linear time complexity $O(n + m + z)$.

### 5.2 Enrichment Process

For each recipe:
1.  Combine text fields (title + ingredients + instructions).
2.  Find all entity occurrences using the Aho-Corasick automaton.
3.  Link to Wikipedia metadata (abstract, origin, history).
4.  **Infer Cuisine**: Based on the origin of identified ingredients (e.g., Soy Sauce -> Asian).

### 5.3 Statistics

*   **Enriched Recipes**: 5,645 (99.98%)
*   **Total Wiki Links**: 139,717
*   **Unique Wiki Pages Linked**: **1,067**
*   **Avg Links per Recipe**: 24.75

---

## 6. Indexer (PyLucene)

### 6.1 Index Schema

The system uses **PyLucene** (via Lupyne) with a BM25 similarity model.

**Text Fields (Tokenized & Boosted):**
*   `title_text` (Boost: **2.0**)
*   `ingredients_text` (Boost: **1.5**)
*   `instructions_text` (Boost: **1.0**)
*   `wiki_abstracts` (Boost: **1.0**) - *Enriched content*

**Keyword Fields (Exact Match):**
*   `ingredients_kw`
*   `cuisine_kw`
*   `origin_country_kw`

**Numeric Fields:**
*   `total_minutes` (for range queries)

### 6.2 Performance

*   **Index Size**: ~52 MB
*   **Indexing Time**: ~15 seconds
*   **Documents**: 5,646

---

## 7. Searcher

### 7.1 Query Capabilities

| Query Type | Syntax | Example | Implementation |
| :--- | :--- | :--- | :--- |
| **Full-text** | plain text | `chocolate cake` | BM25Similarity |
| **Exact Phrase** | quotes | `"chocolate cake"` | PhraseQuery |
| **Fuzzy** | automatic | `chickn` → `chicken` | FuzzyQuery (edit dist 2) |
| **Boolean** | `+` / `-` | `chicken +garlic -onion` | BooleanQuery |
| **Filtering** | flags | `--cuisine italian` | TermQuery |
| **Range** | flags | `--max-time 30` | PointRangeQuery |

### 7.2 Benchmark

Average query times (over 25 test queries):
*   **BM25**: ~20 ms
*   **TF-IDF**: ~14 ms

---

## 8. Evaluation

### 8.1 Comparison vs Food.com
We compared our Top-1 results with Food.com's native search for 35 queries.
*   **Match Rate**: **~60%**
*   **100% Match** for specific dish names (e.g., "Beef Stew", "Tomato Soup").

### 8.2 Comparison vs Google Baseline
We manually evaluated relevance against Google's top results for 10 queries.
*   **Average Relevance Score**: **0.80 / 1.0**
*   **Precision@10**: High relevance for queries like "Pasta Carbonara" (0.90) and "Chocolate Cake" (0.85).

---

## 9. Usage Examples

### CLI Search

```bash
# Basic search
python -m search_cli.run --query "chocolate cake" --k 5

# Fuzzy search (typo tolerance)
python -m search_cli.run --query "chickn" --fuzzy

# Filter by ingredients (must have chicken & garlic, no beef)
python -m search_cli.run --query "dinner" --include "chicken,garlic" --exclude "beef"

# Filter by cuisine
python -m search_cli.run --query "pasta" --cuisine "italian"

# Filter by preparation time
python -m search_cli.run --query "quick dinner" --max-time 30
```

### Example Output

```text
Query: "chocolate cake"
Results (Top 3):

1. Devilishly Good Chocolate Cake (score: 23.44)
   URL: https://www.food.com/recipe/devilishly-good-chocolate-cake-279326
   Time: 65 min | Rating: 4.5★
   Cuisine: European
   
2. German Chocolate Cake (score: 23.30)
   URL: https://www.food.com/recipe/german-chocolate-cake-140464
   Time: 45 min | Rating: 5.0★
   Cuisine: German, European
   Wikipedia: "German chocolate cake, originally German's chocolate cake, is a layered 
              chocolate cake from the United States..."
```

---

## 10. Summary Statistics

| Component | Metric | Value |
| :--- | :--- | :--- |
| **Crawler** | Downloaded HTML | **5,646** |
| **Parser** | Parsing Success | **100%** |
| **Wikipedia** | Culinary Articles | **9,693** |
| **Enricher** | Unique Wiki Pages Linked | **1,067** |
| **Enricher** | Total Wiki Links | **139,717** |
| **Index** | Total Documents | **5,646** |
| **Search** | Avg Response Time | **~20 ms** |

## 📂 Project Structure

```
food-recipes-ir-pipeline/
├── crawler/              # Web crawler
├── parser/               # HTML parser
├── spark_jobs/           # Wikipedia Spark parser
├── entities/             # Recipe enricher
├── indexer/              # Simple + PyLucene indexer
├── search_cli/           # CLI search tool
├── eval/                 # Benchmarks and evaluation
├── frontend/             # Next.js web UI
├── data/
│   ├── raw/              # Raw HTML files
│   └── normalized/       # Processed JSONL files
└── index/                # Lucene index files
```
