# Food Recipes - End-to-End Information Retrieval Pipeline

**Author:** Maroš Bednár  
**Email:** bednarmaros341@gmail.com  
**AIS ID:** 116822  
**Course:** VINF (Information Retrieval)  

## 📋 Project Overview

This project implements a complete information retrieval pipeline for food recipes, crawling and indexing recipe data to create a searchable database. The system covers the entire IR workflow from web crawling to query evaluation, with a focus on robust, scalable implementation using only core Python libraries.

## 🎯 Project Goals

- **Primary Data Source:** https://www.food.com/ (respecting robots.txt)
- **Pipeline Components:** Web Crawler → Parser/Normalizer → Indexer → Search CLI → Entity Extraction → Spark Processing → Evaluation
- **Storage Strategy:** File-based only (TSV/JSONL/Parquet) - No SQL databases
- **Search Algorithms:** TF-IDF and BM25 ranking with field-aware scoring
- **Entity Linking:** Ingredient and cuisine detection with Wikipedia linking
- **Big Data Processing:** Apache Spark jobs for gazetteer construction

## 🛠 Technology Stack

### **Core Languages**
- **Python** (primary implementation language)
- **Shell/Bash** (automation scripts)
- **PySpark** (distributed processing)

### **Allowed Libraries**
- Standard library: `re`, `argparse`, `json`, `gzip`, `hashlib`, `pathlib`, `logging`
- HTTP requests: `requests`
- HTML parsing: `lxml`, `beautifulsoup4`
- String matching: `ahocorasick`
- Big data: `pyspark`
- Progress tracking: `tqdm`

### **Prohibited Libraries**
- ❌ `pandas`, `nltk`
- ❌ External indexers (Elasticsearch, Solr)
- ❌ External databases
- ❌ Any libraries not explicitly listed in allowed list

## 🏗 System Architecture

```
project/
├── crawler/           # Web crawling modules
├── parser/           # HTML parsing and normalization
├── indexer/          # Inverted index construction
├── search_cli/       # Command-line search interface
├── entities/         # Entity extraction and Wikipedia linking
├── spark_jobs/       # Apache Spark processing jobs
├── eval/             # Evaluation metrics and queries
├── packaging/        # Deployment and dependency management
├── docs/             # Documentation
├── data/             # Raw and processed data
└── tests/            # Unit tests
```

## 📊 Data Pipeline Flow

1. **Web Intelligence & Seed Discovery**
   - Parse `robots.txt` and respect crawling policies
   - Extract URLs from XML sitemaps
   - Discover recipe pages through A-Z browsing
   - Identify high-value content hubs

2. **Polite Web Crawling**
   - Rate-limited requests (configurable QPS)
   - Exponential backoff on failures
   - Custom User-Agent with contact information
   - Canonical URL deduplication

3. **Content Extraction & Normalization**
   - JSON-LD schema.org/Recipe parsing (preferred)
   - Robust HTML fallback extraction
   - Structured data normalization
   - Time standardization to minutes

4. **Inverted Index Construction**
   - Field-aware indexing (title, ingredients, instructions)
   - TF-IDF and BM25 scoring preparation
   - Efficient posting list storage

5. **Search & Retrieval**
   - Multiple ranking algorithms
   - JSON-based query filtering
   - Snippet generation with highlighting
   - Top-K result ranking

6. **Entity Processing**
   - Ingredient mention detection
   - Wikipedia entity linking
   - Gazetteer construction via Spark

7. **Evaluation & Metrics**
   - Precision@K and Recall@K computation
   - Mean Average Precision (MAP)
   - Algorithm comparison framework

## 🗂 Data Formats

### **Raw Data**
- **HTML Storage:** `data/raw/{domain}/{doc_id}.html`

### **Normalized Recipes**
- **Format:** JSONL (`data/normalized/recipes.jsonl`)
- **Schema:** `id`, `url`, `title`, `ingredients[]`, `instructions[]`, `times{prep,cook,total}`, `cuisine[]`, `category[]`, `tools[]`, `yield`, `author`, `nutrition`, `ratings`

### **Search Index**
- **Terms:** `index/v1/terms.tsv` → `term \t df \t idf`
- **Postings:** `index/v1/postings.tsv` → `term \t field \t docId \t tf`
- **Document Metadata:** `index/v1/docmeta.tsv` → `docId \t url \t title \t len_title \t len_ing \t len_instr`

### **Entity Data**
- **Gazetteer:** `entities/gazetteer_ingredients.tsv` → `surface \t wiki_title \t norm`
- **Links:** `entities/links.jsonl` → `docId \t field \t start \t end \t surface \t wiki_title`

### **Evaluation Data**
- **Queries:** `eval/queries.tsv` → `qid \t query \t filters_json`
- **Relevance:** `eval/qrels.tsv` → `qid \t docId \t rel`
- **Results:** `eval/results_{metric}.tsv` → `qid \t docId \t rank \t score`

## 🚀 Usage Examples

### **Web Crawling**
```bash
python -m crawler.run --seed https://www.food.com/ --limit 2000 --qps 0.5 --out data/raw
```

### **Content Parsing**
```bash
python -m parser.run --raw data/raw --out data/normalized/recipes.jsonl
```

### **Index Construction**
```bash
python -m indexer.run --input data/normalized/recipes.jsonl --out index/v1
```

### **Recipe Search**
```bash
python -m search_cli.run --index index/v1 --metric bm25 --q "mexican chicken nachos" --k 10 --filter '{"max_total_minutes":30,"cuisine":["Mexican"]}'
```

### **Entity Processing**
```bash
spark-submit spark_jobs/build_gazetteer.py --wiki /path/to/enwiki --out entities/gazetteer_ingredients.tsv
```

### **Evaluation**
```bash
python -m eval.run --index index/v1 --metric tfidf --queries eval/queries.tsv --qrels eval/qrels.tsv --out eval/results_tfidf.tsv
```

### **Complete Pipeline**
```bash
# Run entire pipeline
./packaging/run.sh all

# Individual components
./packaging/run.sh crawl
./packaging/run.sh parse
./packaging/run.sh index
./packaging/run.sh search
./packaging/run.sh gazetteer
./packaging/run.sh eval
```

## 📈 Development Timeline

### **Phase A: Web Intelligence & Seed Extraction**
- Parse robots.txt and implement compliance checking
- Extract and process XML sitemaps
- Implement A-Z recipe enumeration
- Document crawl strategy and findings

### **Phase B: Crawler Implementation**
- Build polite, rate-limited web crawler
- Implement URL frontier with deduplication
- Add retry logic with exponential backoff
- Create comprehensive logging system

### **Phase C: Parser & Normalization**
- JSON-LD structured data extraction
- Robust HTML fallback parsing
- Data normalization and validation
- Schema compliance verification

### **Phase D: Indexer & Search CLI**
- Inverted index construction
- TF-IDF and BM25 implementation
- Field-aware scoring system
- Query filtering and result ranking

### **Phase E: Entity Extraction & Linking**
- Aho-Corasick pattern matching
- Wikipedia entity resolution
- Gazetteer construction and linking
- Entity mention detection

### **Phase F: Spark Processing**
- Wikipedia data processing
- Distributed gazetteer construction
- Performance optimization
- Scalability testing

### **Phase G: Evaluation Framework**
- Query set development
- Relevance judgment creation
- Metrics computation (P@K, R@K, MAP)
- Algorithm comparison analysis

## 📊 Success Metrics

### **Data Requirements**
- ✅ Total data size ≥ 500 MB (including Wikipedia subset)
- ✅ Successfully crawled recipe collection
- ✅ High-quality normalized recipe data

### **System Performance**
- ✅ Working end-to-end pipeline
- ✅ Fast search response times
- ✅ Accurate ranking algorithms
- ✅ Robust entity linking

### **Evaluation Results**
- ✅ Precision@K and Recall@K for ≥10 queries
- ✅ Comparative analysis of TF-IDF vs BM25
- ✅ Mean Average Precision computation
- ✅ Statistical significance testing

### **Code Quality**
- ✅ Comprehensive unit test coverage
- ✅ Deterministic and reproducible results
- ✅ Clear logging and error handling
- ✅ Docker-friendly deployment

### **Documentation**
- ✅ Complete technical documentation
- ✅ User guides and examples
- ✅ API reference documentation
- ✅ Performance benchmarks

## 🧪 Testing Strategy

- **Unit Tests:** Core functionality testing for each module
- **Integration Tests:** End-to-end pipeline validation
- **Performance Tests:** Scalability and response time measurement
- **Compliance Tests:** Library restriction and format validation
- **Regression Tests:** Automated quality assurance

## 📋 Quality Assurance

### **Automated Compliance Checks**
- No prohibited libraries (pandas, nltk, etc.)
- All CLI commands support `-h` help option
- Output formats match exact specifications
- Robots.txt compliance verification
- Deterministic result ordering

### **Data Quality Validation**
- Recipe parsing accuracy verification
- Time normalization correctness
- Entity linking precision measurement
- Index integrity checking

## 🔧 Development Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/Marosko123/food-recipes-ir-pipeline
   cd food-recipes-ir-pipeline
   ```

2. **Install Dependencies**
   ```bash
   pip install -r packaging/requirements.txt
   ```

3. **Run Tests**
   ```bash
   python -m pytest tests/
   ```

4. **Execute Pipeline**
   ```bash
   ./packaging/run.sh all
   ```

## 📚 Documentation Structure

- `docs/README.md` - Main project documentation
- `docs/wiki_3pages.md` - Detailed technical wiki
- `docs/slides_outline.md` - Presentation materials
- `docs/api_reference.md` - Module API documentation
- `docs/deployment_guide.md` - Production deployment instructions

## 🤝 Contributing

This is an academic project for the VINF course. For questions or clarifications, please contact:
- **Email:** bednarmaros341@gmail.com
- **Student ID:** 116822

## 📄 License

Academic project - all rights reserved. Created for educational purposes as part of the VINF (Information Retrieval) course.

---

**Last Updated:** September 2025  
**Status:** Active Development  
**Next Milestone:** Phase A - Web Intelligence Implementation