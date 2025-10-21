# 🍳 Food Recipes - Recipes IR Pipeline

**Author:** Maroš Bednár  
**Email:** bednarmaros341@gmail.com  
**AIS ID:** 116822  
**Project:** Complete Recipe Search Engine with AI-Powered Features

---

## 🎓 **University Submissions**

### **Phase 1 Submission (October 2025)** 
📘 **[README_First_Submission.md](README_First_Submission.md)** — Complete documentation for first project delivery

**Includes:**
- ✅ Crawler (robots.txt compliant, 5,646 recipes)
- ✅ Parser (JSON-LD + HTML fallback)
- ✅ Custom Indexer (inverted index, no external libs)
- ✅ **Two Search Metrics:** TF-IDF + BM25 (as required)
- ✅ Field-aware scoring (title=3.0, ingredients=2.0, instructions=1.0)
- ✅ 30+ filter types (time, rating, nutrition)
- ✅ Pseudocode & live demo guide

**Quick Demo:**
```bash
# Run all examples (for presentation)
bash packaging/cli_examples.sh
```

📖 **[docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md)** — Step-by-step presentation guide for teachers

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Project Structure](#project-structure)
5. [Usage](#usage)
6. [Phases](#phases)
7. [API Documentation](#api-documentation)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)
10. [License](#license)

---

## 🎯 Overview

Food Recipes is a comprehensive **Recipes Information Retrieval (IR) Pipeline** that provides:

- **Web Crawling:** Automated recipe collection from food.com
- **Data Parsing:** Intelligent HTML parsing with JSON-LD support
- **Search Engine:** TF-IDF and BM25 ranking algorithms
- **Entity Linking:** Wikipedia-based ingredient and cuisine linking
- **Web Interface:** Modern, responsive frontend
- **Wikipedia Integration:** Comprehensive recipe knowledge base

### Key Features

- 🔍 **Advanced Search:** TF-IDF and BM25 ranking with field-aware scoring
- 🏷️ **Entity Linking:** Automatic ingredient and cuisine classification
- 📚 **Wikipedia Integration:** 1000+ recipes from Wikipedia knowledge base
- 🌐 **Web Interface:** Modern, responsive frontend with real-time search
- 📊 **Analytics:** Comprehensive statistics and performance metrics
- 🚀 **Scalable:** Designed for large-scale recipe processing

---

## 🚀 Quick Start

### ⚡ **5-Minute Setup** (Phase 1 Demo)

📘 **See [QUICKSTART.md](QUICKSTART.md) for complete step-by-step guide**

```bash
# 1. Crawl 100 recipes
./packaging/run.sh crawl 100

# 2. Parse HTML → JSON
./packaging/run.sh parse

# 3. Build index
./packaging/run.sh index

# 4. Search!
./packaging/run.sh search "chicken pasta"

# 5. Run 10 Q&A demo scenarios
bash packaging/cli_examples.sh
```

**📖 Documentation:**
- **[QUICKSTART.md](QUICKSTART.md)** - Fastest way to get started (5 min)
- **[README_First_Submission.md](README_First_Submission.md)** - Phase 1 overview (pseudocode + metrics)
- **[docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md)** - Presentation guide for teachers
- **[docs/CLI_GUIDE.md](docs/CLI_GUIDE.md)** - Complete CLI reference

---

### 🖥️ Full Application Setup

### 1. Clone and Setup
```bash
git clone <repository-url>
cd VINF
python setup_and_launch.py
```

### 2. Install Dependencies
```bash
# Automatic installation
python setup_and_launch.py --install-deps

# Or manual installation
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r packaging/requirements.txt
```

### 3. Run the Application
```bash
# GUI Mode (Recommended)
python setup_and_launch.py --gui

# CLI Mode
python setup_and_launch.py --cli

# Check Status
python setup_and_launch.py --status
```

---

## 📦 Installation

### System Requirements

- **Python:** 3.8 or higher
- **Memory:** 4GB RAM minimum, 8GB recommended
- **Storage:** 2GB free space
- **Network:** Internet connection for web crawling

### Supported Platforms

- ✅ **macOS** (tested on macOS 14.6.0)
- ✅ **Linux** (Ubuntu 20.04+, CentOS 7+)
- ✅ **Windows** (Windows 10+)

### Dependencies

#### Core Dependencies
```bash
requests>=2.25.0          # HTTP requests
beautifulsoup4>=4.9.0     # HTML parsing
lxml>=4.6.0               # XML/HTML processing
ahocorasick>=2.0.0        # String matching
tqdm>=4.60.0              # Progress bars
```

#### Optional Dependencies
```bash
pyspark>=3.0.0            # Spark processing (Phase F)
tkinter                   # GUI interface (usually included with Python)
```

### Installation Methods

#### Method 1: Automatic Setup (Recommended)
```bash
python setup_and_launch.py --install-deps
```

#### Method 2: Manual Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r packaging/requirements.txt
```

#### Method 3: Development Installation
```bash
# Clone repository
git clone <repository-url>
cd VINF

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .
```

---

## 📁 Project Structure

```
VINF/
├── 📁 crawler/              # Web crawling (Phases A & B)
│   ├── run.py              # Main crawler script
│   ├── robots.py           # robots.txt handling
│   ├── sitemap.py          # Sitemap parsing
│   ├── util.py             # Utility functions
│   └── frontier.py         # URL queue management
│
├── 📁 parser/               # HTML parsing (Phase C)
│   ├── run.py              # Main parser script
│   ├── json_ld_parser.py   # JSON-LD extraction
│   └── html_parser.py      # HTML fallback parsing
│
├── 📁 indexer/              # Search indexing (Phase D)
│   └── run.py              # Inverted index builder
│
├── 📁 search_cli/           # Search interface (Phase D)
│   └── run.py              # TF-IDF and BM25 search
│
├── 📁 entities/             # Entity linking (Phase E)
│   ├── matcher.py          # Aho-Corasick matching
│   ├── linker.py           # Entity linking
│   └── gazetteer_builder.py # Gazetteer creation
│
├── 📁 spark_jobs/           # Spark processing (Phase F)
│   └── __init__.py         # Spark job modules
│
├── 📁 frontend-nextjs/      # Next.js web interface
│   ├── src/                # Source code
│   ├── package.json        # Dependencies
│   └── next.config.js      # Next.js configuration
│
├── 📁 data/                 # All project data
│   ├── raw/                # Raw HTML files
│   ├── normalized/         # Parsed recipe data (recipes.jsonl)
│   ├── index/              # Search indices
│   ├── entities/           # Entity linking data
│   ├── wikipedia_recipes/  # Wikipedia data
│   └── seed_analysis/      # Seed extraction results
│
├── 📁 packaging/            # Deployment files
│   ├── requirements.txt    # Python dependencies
│   └── run.sh              # Shell script runner
│
├── 📁 docs/                 # Documentation
│   ├── README.md           # Documentation overview
│   └── API_DOCUMENTATION.md # API reference
│
├── 📁 tests/                # Test files
│   └── test_*.py           # Unit tests
│
├── setup_and_launch.py     # Main launcher script
├── api_server.py           # Flask API server
└── README.md               # This documentation
```

---

## 🎮 Usage

### GUI Mode (Recommended)

Launch the graphical interface:
```bash
python setup_and_launch.py --gui
```

The GUI provides:
- 📊 **System Status:** Real-time project status
- 🔧 **Dependency Management:** Automatic installation
- 🚀 **Phase Execution:** One-click phase running
- 📈 **Progress Monitoring:** Real-time output display
- 🧹 **Data Management:** Clean and reset functionality

### CLI Mode

Launch the command-line interface:
```bash
python setup_and_launch.py --cli
```

Available commands:
- `1` - Show Project Status
- `2` - Install Dependencies
- `3-8` - Run Individual Phases
- `9` - Test Search CLI
- `10` - Launch Frontend
- `11` - Run All Phases
- `12` - Clean Project Data
- `13` - Show Documentation
- `14` - Help & Troubleshooting

### Direct Phase Execution

Run phases directly:
```bash
# Phase A: Seed Extraction
python -m crawler.run --phase seeds --out data/seed_analysis --qps 0.5

# Phase B: Web Crawling
python -m crawler.run --phase crawl --seeds data/seed_analysis/recipe_seeds.txt --out data/raw --limit 1000 --qps 0.3

# Phase C: Parsing
python -m parser.run --raw data/raw --out data/normalized/recipes.jsonl

# Phase D: Indexing
python -m indexer.run --input data/normalized/recipes.jsonl --out data/index/v1

# Phase E: Entity Linking
python -m entities.gazetteer_builder
python -m entities.linker --input data/normalized/recipes.jsonl --gazetteer data/entities/gazetteer_ingredients.tsv --output data/entities/links.jsonl

# Phase F: Wikipedia Collection
python run_wikipedia_collection.py --max-recipes 1000 --max-ingredients 500
```

### Search Interface

Test the search functionality:
```bash
# TF-IDF Search
python -m search_cli.run --index data/index/v1 --metric tfidf --q "chicken pasta" --k 10

# BM25 Search
python -m search_cli.run --index data/index/v1 --metric bm25 --q "chicken pasta" --k 10

# Filtered Search
python -m search_cli.run --index data/index/v1 --metric bm25 --q "chicken pasta" --k 10 --filter '{"max_total_minutes":30,"cuisine":["Italian"]}'
```

### Web Interface

Launch the web interface:
```bash
# Start API server
python api_server.py

# Start Next.js frontend (in another terminal)
cd frontend-nextjs && npm run dev

# Access at http://localhost:3000
```

---

## 🔄 Phases

### Phase A: Seed Extraction
**Purpose:** Extract recipe URLs from sitemaps and robots.txt

**Input:** None  
**Output:** `data/seed_analysis/recipe_seeds.txt`

**Features:**
- robots.txt compliance
- Sitemap parsing (XML, XML.gz)
- URL canonicalization
- Deduplication

### Phase B: Web Crawling
**Purpose:** Download HTML pages from recipe URLs

**Input:** `data/seed_analysis/recipe_seeds.txt`  
**Output:** `data/raw/*.html`

**Features:**
- Rate limiting (0.3 QPS)
- Retry logic with exponential backoff
- Session management
- Progress tracking

### Phase C: Parsing
**Purpose:** Extract structured data from HTML pages

**Input:** `data/raw/*.html`  
**Output:** `data/normalized/recipes.jsonl`

**Features:**
- JSON-LD extraction (primary)
- HTML fallback parsing
- Data validation
- Image extraction

### Phase D: Indexing & Search
**Purpose:** Build search index and implement search algorithms

**Input:** `data/normalized/recipes.jsonl`  
**Output:** `data/index/v1/`

**Features:**
- Inverted index construction
- TF-IDF ranking
- BM25 ranking
- Field-aware scoring

### Phase E: Entity Linking
**Purpose:** Link ingredients and cuisines to Wikipedia

**Input:** `data/normalized/recipes.jsonl`  
**Output:** `data/entities/links.jsonl`

**Features:**
- Aho-Corasick pattern matching
- Gazetteer-based linking
- Wikipedia integration
- Entity disambiguation

### Phase F: Wikipedia Collection
**Purpose:** Collect additional recipes from Wikipedia

**Input:** None  
**Output:** `data/wikipedia_recipes/`

**Features:**
- Category-based collection
- Search-based collection
- Structured data extraction
- Knowledge base enhancement

---

## 📚 API Documentation

### Search API

#### Endpoints

**GET /api/health**
- **Description:** Health check endpoint
- **Response:** `{"status": "healthy", "timestamp": "..."}`

**POST /api/search**
- **Description:** Search recipes
- **Body:**
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
- **Response:**
  ```json
  {
    "query": "chicken pasta",
    "metric": "bm25",
    "results": [
      {
        "doc_id": "12345",
        "title": "Chicken Pasta",
        "url": "https://...",
        "score": 0.85,
        "snippet": "..."
      }
    ]
  }
  ```

### Data Formats

#### Recipe JSONL Format
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
    "calories": 450
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

#### Index Format

**Terms TSV:** `term \t df \t idf`  
**Postings TSV:** `term \t field \t docId \t tf`  
**DocMeta TSV:** `docId \t url \t title \t len_title \t len_ing \t len_instr`

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Virtual Environment Issues
**Problem:** `venv` not found or not activated  
**Solution:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Dependency Installation Failures
**Problem:** pip install fails  
**Solution:**
```bash
pip install --upgrade pip
pip install --no-cache-dir -r packaging/requirements.txt
```

#### 3. Permission Errors
**Problem:** File permission denied  
**Solution:**
```bash
# On Unix systems
chmod +x setup_and_launch.py
chmod +x packaging/run.sh

# On Windows
# Run as Administrator or check file permissions
```

#### 4. Network Issues
**Problem:** Crawling fails due to network errors  
**Solution:**
- Check internet connection
- Verify firewall settings
- Reduce QPS rate: `--qps 0.1`
- Check robots.txt compliance

#### 5. Memory Issues
**Problem:** Out of memory during processing  
**Solution:**
- Reduce batch sizes
- Process data in smaller chunks
- Increase system memory
- Use streaming processing

#### 6. GUI Not Available
**Problem:** tkinter not found  
**Solution:**
```bash
# On Ubuntu/Debian
sudo apt-get install python3-tk

# On CentOS/RHEL
sudo yum install tkinter

# On macOS (usually included)
# No action needed

# On Windows (usually included)
# No action needed
```

### Debug Mode

Enable debug logging:
```bash
export PYTHONPATH=$PWD
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Run your command here
"
```

### Log Files

Check log files for detailed error information:
- `data/crawl.log` - Crawling logs
- `data/parse.log` - Parsing logs
- `data/wikipedia_collection.log` - Wikipedia collection logs

---

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit changes: `git commit -m "Add feature"`
5. Push to branch: `git push origin feature-name`
6. Create a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to all functions
- Include unit tests for new features

### Testing

Run tests:
```bash
python -m pytest tests/
```

### Documentation

- Update README.md for new features
- Add API documentation for new endpoints
- Include examples in docstrings

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📞 Support

For questions, issues, or contributions:

- **Email:** bednarmaros341@gmail.com
- **Project:** Food Recipes - Recipes IR Pipeline
- **AIS ID:** 116822

---

## 🎉 Acknowledgments

- **Food.com** for providing recipe data
- **Wikipedia** for comprehensive knowledge base
- **Python Community** for excellent libraries
- **Open Source Contributors** for inspiration and tools

---

## 📈 Future Enhancements

### Planned Features

- **Machine Learning:** Recipe recommendation system
- **Advanced Analytics:** Usage patterns and insights
- **Multi-language Support:** International recipe support
- **Mobile App:** Native mobile application
- **API Rate Limiting:** Production-ready API
- **Caching:** Redis-based caching system
- **Monitoring:** Comprehensive monitoring and alerting

### Phase G: Machine Learning (Future)
- Recipe recommendation engine
- Ingredient substitution suggestions
- Nutritional analysis
- Cooking time prediction

### Phase H: Advanced Analytics (Future)
- User behavior analysis
- Popular recipe trends
- Seasonal recipe recommendations
- Performance optimization

---

**Last Updated:** September 26, 2025  
**Version:** 1.0.0  
**Status:** Production Ready