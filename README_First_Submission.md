# Food Recipes IR Pipeline — First Submission (Phase 1)

**Author:** Maroš Bednár  
**Email:** bednarmaros341@gmail.com  
**AIS ID:** 116822  
**Submission Date:** October 2025  
**Course:** VINF (Information Retrieval)

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Components Overview](#components-overview)
4. [Installation & Setup](#installation--setup)
5. [Pipeline Execution Guide](#pipeline-execution-guide)
6. [Search Metrics Implementation](#search-metrics-implementation)
7. [Demo Scenarios](#demo-scenarios)
8. [Technical Details](#technical-details)
9. [Statistics](#statistics)

---

## 🎯 Project Overview

### Mission
Build a complete **recipes information retrieval pipeline** from food.com with:
- **Crawler:** Respectful web scraping with robots.txt compliance
- **Parser:** JSON-LD extraction + robust HTML fallback
- **Indexer:** Custom inverted index with field-aware scoring
- **Search:** Two ranking metrics (TF-IDF & BM25) with comprehensive filters

### Data Source
- **Website:** https://www.food.com
- **Collected:** 5,646 recipes (2.2 GB raw HTML)
- **Normalized:** 12 MB JSONL (structured data)
- **Indexed:** 9,822 unique terms, 444,130 postings

### Key Features
✅ Robots.txt compliant crawler with QPS throttling  
✅ Dual extraction strategy (JSON-LD + HTML heuristics)  
✅ Custom inverted index (no external libraries)  
✅ **Two ranking algorithms:** TF-IDF (cosine) + BM25 (Okapi)  
✅ 30+ filter types (time, rating, nutrition, category)  
✅ Field-aware scoring (title=3.0, ingredients=2.0, instructions=1.0)

---

## 🏗️ System Architecture

### High-Level Flow

```
┌─────────────────┐
│   food.com      │
│  (Source Data)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│   CRAWLER       │─────▶│  Raw HTML Files  │
│  (robots.txt    │      │  2.2 GB          │
│   QPS=0.5)      │      │  5,646 files     │
└─────────────────┘      └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐      ┌─────────────────┐
                         │     PARSER       │─────▶│ Normalized JSONL│
                         │  (JSON-LD +      │      │  12 MB          │
                         │   HTML fallback) │      │  5,646 recipes  │
                         └──────────────────┘      └────────┬────────┘
                                                            │
                                                            ▼
                                                   ┌──────────────────┐
                                                   │    INDEXER       │
                                                   │  (Inverted Index)│
                                                   │  - Tokenization  │
                                                   │  - TF/IDF calc   │
                                                   │  - Field weights │
                                                   └────────┬─────────┘
                                                            │
                                                            ▼
                                                   ┌──────────────────┐
                                                   │  Index Files     │
                                                   │  - terms.tsv     │
                                                   │  - postings.tsv  │
                                                   │  - docmeta.tsv   │
                                                   └────────┬─────────┘
                                                            │
                                                            ▼
                                                   ┌──────────────────┐
                                                   │   SEARCH CLI     │
                                                   │  - TF-IDF        │
                                                   │  - BM25          │
                                                   │  - Filters       │
                                                   └──────────────────┘
```

---

## 🔧 Components Overview

### 1. Crawler (`crawler/`)
**Purpose:** Download recipe pages from food.com

**Features:**
- ✅ Robots.txt compliance (never visit disallowed paths)
- ✅ QPS throttling (0.5 requests/second)
- ✅ Exponential backoff on errors
- ✅ URL deduplication (by hash)
- ✅ Sitemap parsing for seed discovery

**Output:** `data/raw/www.food.com/{doc_id}.html`

---

### 2. Parser (`parser/`)
**Purpose:** Extract structured data from raw HTML

**Strategy:**
1. **Primary:** JSON-LD `schema.org/Recipe` extraction
2. **Fallback:** HTML structure heuristics (headings, lists)

**Features:**
- ✅ Time normalization (ISO-8601 → minutes)
- ✅ Robust field extraction (title, ingredients, instructions)
- ✅ Nutrition data parsing
- ✅ Rating and review count extraction

**Output:** `data/normalized/recipes.jsonl`

**Schema:**
```json
{
  "id": "239890",
  "url": "https://www.food.com/recipe/...",
  "title": "Mediterranean Chicken and Pasta",
  "ingredients": ["chicken breast", "pasta", ...],
  "instructions": ["Step 1...", "Step 2...", ...],
  "times": {"prep": 10, "cook": 15, "total": 25},
  "cuisine": ["Mediterranean"],
  "category": ["Main Course"],
  "ratings": {"avg": 4.5, "count": 123},
  "nutrition": {"calories": 450, "protein": 35, ...}
}
```

---

### 3. Indexer (`indexer/`)
**Purpose:** Build inverted index for fast search

**Algorithm:**
```python
def build_index(recipes):
    terms = {}       # term -> (df, idf)
    postings = {}    # term -> [(field, docId, tf), ...]
    
    for recipe in recipes:
        for field in ['title', 'ingredients', 'instructions']:
            tokens = tokenize(recipe[field])  # lowercase, stopwords
            
            for term in tokens:
                tf = count(term, tokens)
                postings[term].append((field, recipe.id, tf))
    
    for term in postings:
        df = count_unique_docs(postings[term])
        idf = log(N / df)
        terms[term] = (df, idf)
    
    save_tsv("terms.tsv", terms)
    save_tsv("postings.tsv", postings)
```

**Output Files:**
- `data/index/v1/terms.tsv` — `term | df | idf`
- `data/index/v1/postings.tsv` — `term | field | docId | tf`
- `data/index/v1/docmeta.tsv` — `docId | url | title | len_title | len_ing | len_instr`

**Features:**
- ✅ Tokenization (lowercase, stopword removal)
- ✅ Field-aware indexing (title, ingredients, instructions)
- ✅ Document length tracking (for BM25)
- ✅ IDF calculation: `log(N / df)`

---

### 4. Search CLI (`search_cli/`)
**Purpose:** Query recipes using two ranking algorithms

**Implemented Metrics:**

#### **TF-IDF (Cosine Similarity)**
```python
score = cosine_similarity(query_vector, doc_vector)

where:
  query_vector[term] = tf_query * idf
  doc_vector[term] = tf_doc * idf * field_weight
  
  cosine_similarity = dot(Q, D) / (||Q|| * ||D||)
```

**Characteristics:**
- Normalized scores (0.0 to 1.0)
- Interpretable similarity measure
- Classic vector space model

#### **BM25 (Okapi BM25)**
```python
score = Σ idf(term) * (tf * (k1+1)) / (tf + k1 * (1-b + b*(|D|/avgdl)))

where:
  k1 = 1.2  # term frequency saturation
  b = 0.75  # document length normalization
  |D| = document length in field
  avgdl = average document length
```

**Characteristics:**
- Non-normalized scores (0 to ∞)
- Saturating term frequency (diminishing returns)
- Document length penalty
- Industry standard (used in Elasticsearch)

**Field Weights:**
- `title`: 3.0 (highest importance)
- `ingredients`: 2.0 (medium importance)
- `instructions`: 1.0 (base importance)

---

## 🚀 Installation & Setup

### Prerequisites
```bash
# Required
Python 3.8+
pip

# Optional (for testing)
pytest
```

### Install Dependencies
```bash
pip3 install -r packaging/requirements.txt
```

**Required packages:**
- `requests` — HTTP requests
- `lxml` — HTML parsing
- `beautifulsoup4` — HTML parsing
- `tqdm` — Progress bars

---

## 📝 Pipeline Execution Guide

### Complete Pipeline (All Steps)

```bash
# Step 1: Extract seeds from sitemaps
bash packaging/run.sh seeds

# Step 2: Crawl recipe pages (example: 100 recipes)
bash packaging/run.sh crawl 100

# Step 3: Parse HTML to JSONL
bash packaging/run.sh parse

# Step 4: Build search index
bash packaging/run.sh index

# Step 5: Search recipes
bash packaging/run.sh search "chicken pasta"
```

---

### Detailed Step-by-Step

#### **Step 1: Seed Extraction**
```bash
python3 -m crawler.run \
  --phase seeds \
  --out data/seed_analysis \
  --qps 0.5
```

**Output:**
- `data/seed_analysis/recipe_seeds.txt` (298,000+ URLs)
- `data/seed_analysis/seed_stats.json` (statistics)

---

#### **Step 2: Crawling**
```bash
python3 -m crawler.run \
  --phase crawl \
  --seeds data/seed_analysis/recipe_seeds.txt \
  --out data/raw \
  --limit 5646 \
  --qps 0.5
```

**Output:**
- `data/raw/www.food.com/{doc_id}.html` (5,646 files)
- `data/logs/crawl.log` (detailed log)

**Note:** Our dataset has 5,646 pre-crawled recipes.

---

#### **Step 3: Parsing**
```bash
python3 -m parser.run \
  --raw data/raw \
  --out data/normalized/recipes.jsonl
```

**Output:**
- `data/normalized/recipes.jsonl` (5,646 lines, 12 MB)
- `data/logs/parse.log`

**Verify:**
```bash
# Count recipes
wc -l data/normalized/recipes.jsonl

# View first recipe
head -1 data/normalized/recipes.jsonl | python3 -m json.tool
```

---

#### **Step 4: Indexing**
```bash
python3 -m indexer.run \
  --input data/normalized/recipes.jsonl \
  --out data/index/v1
```

**Output:**
- `data/index/v1/terms.tsv` (9,822 terms)
- `data/index/v1/postings.tsv` (444,130 postings)
- `data/index/v1/docmeta.tsv` (5,646 docs)

**Verify:**
```bash
# Check file sizes
ls -lh data/index/v1/

# Count terms
wc -l data/index/v1/terms.tsv

# Sample terms
head -10 data/index/v1/terms.tsv
```

---

#### **Step 5: Searching**

**Basic BM25 Search:**
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chicken pasta" \
  --k 5
```

**TF-IDF Search:**
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric tfidf \
  --q "chocolate cake" \
  --k 5
```

**With Filters:**
```bash
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "italian pasta" \
  --k 5 \
  --filter '{"max_total_minutes": 30, "min_rating": 4.0}'
```

---

## 🔍 Search Metrics Implementation

### TF-IDF Implementation

**File:** `search_cli/run.py` → `search_tfidf()`

**Algorithm:**
1. **Tokenize query** → `['chicken', 'pasta']`
2. **Calculate query TF** → `{'chicken': 1, 'pasta': 1}`
3. **Build query vector** → `{term: tf * idf, ...}`
4. **For each document:**
   - Build doc vector: `{term: tf * idf * field_weight, ...}`
   - Calculate dot product: `sum(q[t] * d[t])`
   - Calculate magnitudes: `sqrt(sum(v^2))`
   - Cosine similarity: `dot / (||q|| * ||d||)`
5. **Sort by score descending**

**Code snippet:**
```python
# Calculate query magnitude
query_magnitude = sqrt(sum((tf * idf)^2 for term in query))

# Score documents
for term in query:
    for (field, doc_id, tf) in postings[term]:
        doc_tf_idf = tf * idf * field_weights[field]
        doc_scores[doc_id] += query_tf_idf * doc_tf_idf
        doc_magnitudes[doc_id] += doc_tf_idf^2

# Normalize by cosine similarity
for doc_id in doc_scores:
    magnitude = sqrt(doc_magnitudes[doc_id])
    cosine_sim = doc_scores[doc_id] / (query_magnitude * magnitude)
    results.append((doc_id, cosine_sim))
```

---

### BM25 Implementation

**File:** `search_cli/run.py` → `search_bm25()`

**Algorithm:**
1. **Calculate average document length** across all fields
2. **Tokenize query** → `['chicken', 'pasta']`
3. **For each term in query:**
   - Get IDF from index
   - For each document containing term:
     - Get term frequency (tf)
     - Get document length for field
     - Calculate BM25 component:
       ```
       score = idf * (tf * (k1+1)) / (tf + k1 * (1-b + b*(|D|/avgdl)))
       score *= field_weight
       ```
4. **Sum scores across all terms**
5. **Sort by score descending**

**Code snippet:**
```python
# Calculate average doc length
avg_doc_length = sum(meta['len_title'] + meta['len_ing'] + meta['len_instr']) / N

# Score documents
for term in query:
    df, idf = terms[term]
    
    for (field, doc_id, tf) in postings[term]:
        doc_length = get_field_length(doc_id, field)
        
        # BM25 formula
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
        
        bm25_score = idf * (numerator / denominator) * field_weights[field]
        doc_scores[doc_id] += bm25_score
```

---

## 🎬 Demo Scenarios

### Quick Demo Script
```bash
**Quick Demo:**
```bash
bash packaging/cli_examples.sh
```
```

This script demonstrates:
1. Basic BM25 search
2. Quick weeknight dinner (time + rating filters)
3. Healthy lunch (nutrition filters)
4. Italian night (cuisine + time filters)
5. Party dessert (rating filter)
6. TF-IDF vs BM25 comparison

---

### Manual Demo Commands

#### **Demo 1: Compare TF-IDF vs BM25**
```bash
# TF-IDF
python3 search_cli/run.py --index data/index/v1 --metric tfidf --q "chicken pasta" --k 3

# BM25
python3 search_cli/run.py --index data/index/v1 --metric bm25 --q "chicken pasta" --k 3
```

**Expected:** Similar top-3 ranking, but different scores.

---

#### **Demo 2: Time Filters**
```bash
# Recipes under 30 minutes
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "pasta" \
  --k 5 \
  --filter '{"max_total_minutes": 30}'
```

**Expected:** Only quick recipes (≤30 min total time).

---

#### **Demo 3: Nutrition Filters**
```bash
# Low calorie, high protein recipes
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "salad chicken" \
  --k 5 \
  --filter '{"max_calories": 400, "min_protein": 20}'
```

**Expected:** Healthy, protein-rich recipes.

---

#### **Demo 4: Complex Multi-Filter**
```bash
# Mexican recipes: quick, highly rated, moderate calories
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "mexican chicken" \
  --k 3 \
  --filter '{
    "max_total_minutes": 45,
    "min_rating": 4.0,
    "max_calories": 500
  }'
```

**Expected:** Well-rated Mexican recipes under 45 min and 500 cal.

---

## 🧪 Technical Details

### Tokenization
```python
def tokenize(text):
    # 1. Lowercase
    text = text.lower()
    
    # 2. Extract words (alphanumeric only)
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    
    # 3. Remove stopwords
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', ...}
    words = [w for w in words if w not in stopwords and len(w) > 1]
    
    return words
```

**Example:**
```
Input:  "Delicious Chicken & Pasta Recipe!"
Output: ['delicious', 'chicken', 'pasta', 'recipe']
```

---

### IDF Calculation
```python
idf = log(N / df)

where:
  N = total number of documents (5,646)
  df = document frequency (number of docs containing term)
```

**Example:**
- Term "chicken" appears in 523 documents
- IDF = log(5646 / 523) = log(10.8) = **2.38**

---

### Field Weights Rationale

| Field | Weight | Reason |
|-------|--------|--------|
| title | 3.0 | Most condensed, relevant information |
| ingredients | 2.0 | Critical for recipe matching |
| instructions | 1.0 | Verbose, less specific terms |

**Impact:**
- Term in title gets 3× boost vs. instructions
- Term in ingredients gets 2× boost vs. instructions

---

## 📊 Statistics

### Data Collection
```
Source:           food.com
Recipes crawled:  5,646
Raw HTML size:    2.2 GB
Normalized size:  12 MB
Success rate:     100% (parsing)
```

### Index Statistics
```
Unique terms:     9,822
Total postings:   444,130
Avg postings/term: 45.2
Documents:        5,646
Index size:       12 MB (TSV files)
```

### Performance
```
Index loading:    ~120 ms
Query (BM25):     ~60-100 ms
Query (TF-IDF):   ~50-90 ms
With filters:     +200-500 ms
```

### Coverage
```
Fields indexed:   3 (title, ingredients, instructions)
Filter types:     30+ (time, rating, nutrition, category)
Search metrics:   2 (TF-IDF, BM25)
```

---

## 📚 Additional Documentation

### Comprehensive Guides
- **[docs/CLI_GUIDE.md](docs/CLI_GUIDE.md)** — Complete CLI documentation (~5000 lines)
- **[search_cli/README.md](search_cli/README.md)** — Quick start guide
- ### Additional Resources

- **[packaging/cli_examples.sh](packaging/cli_examples.sh)** — Executable demo script

### Key Resources
- **Pseudocode:** See [System Architecture](#system-architecture) section
- **Algorithms:** See [Search Metrics Implementation](#search-metrics-implementation)
- **Demo:** See [Demo Scenarios](#demo-scenarios)

---

## 🎯 Submission Checklist

### Required Components
- [x] **Crawler** — Robots.txt compliant, QPS throttling
- [x] **Parser** — JSON-LD + HTML fallback
- [x] **Indexer** — Custom inverted index (no external libs)
- [x] **Search** — Two metrics (TF-IDF + BM25) ✅
- [x] **Filters** — 30+ types (time, rating, nutrition)
- [x] **Data** — 5,646 recipes crawled and indexed
- [x] **Pseudocode** — Provided in architecture section
- [x] **Demo** — Executable examples ready

### Implemented Features
- [x] Field-aware scoring (title/ingredients/instructions)
- [x] Stopword removal
- [x] Document length normalization (BM25)
- [x] Query term highlighting in results
- [x] Comprehensive filtering system
- [x] Statistics and logging

### NOT Implemented (Out of Scope for Phase 1)
- [ ] Lemmatization (explicitly not required)
- [ ] Stemming (not required)
- [ ] Wikipedia entity linking (Phase 2)
- [ ] Spark jobs (Phase 2)
- [ ] Evaluation metrics (Phase 2)

---

## 🎓 Presentation Notes

### Key Points to Demonstrate

1. **Pseudocode** (5 min)
   - Show architecture diagram
   - Explain indexer algorithm
   - Explain TF-IDF vs BM25 formulas

2. **Live Demo** (10 min)
   - Run `bash packaging/cli_examples.sh`
   - Show TF-IDF vs BM25 comparison
   - Demonstrate filters (time, rating, nutrition)
   - Show index statistics

3. **Technical Deep Dive** (5 min)
   - Tokenization process
   - IDF calculation example
   - Field weights impact
   - BM25 document length normalization

---

## 📞 Contact

**Author:** Maroš Bednár  
**Email:** bednarmaros341@gmail.com  
**AIS ID:** 116822

---

**Note:** This is the **Phase 1 submission** focused on crawler, parser, indexer, and search CLI with two ranking metrics (TF-IDF and BM25). Phase 2 will add Wikipedia entity linking, Spark jobs, and evaluation metrics.
