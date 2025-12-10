# 📦 Inštalačná Príručka - VINF Food Recipes IR Pipeline

**Autor:** Maroš Bednár  
**Dátum:** December 2025

---

## 📋 Obsah

1. [Požiadavky](#požiadavky)
2. [Rýchla inštalácia](#rýchla-inštalácia)
3. [Podrobná inštalácia](#podrobná-inštalácia)
4. [Spustenie jednotlivých modulov](#spustenie-jednotlivých-modulov)
5. [Riešenie problémov](#riešenie-problémov)

---

## Požiadavky

### Systémové požiadavky
- **OS:** macOS, Linux, Windows (WSL)
- **Python:** 3.10+ (odporúčaný 3.13 alebo 3.14)
- **RAM:** Minimálne 4 GB (8 GB odporúčané pre Spark)
- **Disk:** Minimálne 5 GB voľného miesta

### Python závislosti
```
requests>=2.28.0        # HTTP crawling
lxml>=4.9.0             # HTML parsing
numpy>=1.24.0           # Numerické výpočty
pyspark>=3.4.0          # Wikipedia processing (optional)
pyahocorasick>=2.0.0    # Entity matching (optional)
```

---

## Rýchla inštalácia

```bash
# 1. Klonovanie repozitára
git clone https://github.com/Marosko123/food-recipes-ir-pipeline.git
cd food-recipes-ir-pipeline

# 2. Vytvorenie virtuálneho prostredia
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# alebo: venv\Scripts\activate  # Windows

# 3. Inštalácia závislostí
pip install -r packaging/requirements.txt

# 4. Overenie inštalácie
python -m pytest tests/test_integration.py -v
```

---

## Podrobná inštalácia

### Krok 1: Python prostredie

#### macOS
```bash
# Inštalácia Python pomocou Homebrew
brew install python@3.13

# Vytvorenie venv
python3.13 -m venv venv
source venv/bin/activate
```

#### Linux (Ubuntu/Debian)
```bash
# Inštalácia Python
sudo apt update
sudo apt install python3.13 python3.13-venv python3-pip

# Vytvorenie venv
python3.13 -m venv venv
source venv/bin/activate
```

#### Windows
```powershell
# Inštalácia Python z python.org
# Potom:
python -m venv venv
venv\Scripts\activate
```

### Krok 2: Základné závislosti

```bash
# Upgrade pip
pip install --upgrade pip

# Inštalácia základných závislostí
pip install -r packaging/requirements.txt
```

### Krok 3: Voliteľné závislosti

#### PySpark (pre Wikipedia processing)
```bash
# Java je potrebná pre Spark
# macOS: brew install openjdk@17
# Linux: sudo apt install openjdk-17-jdk

pip install pyspark>=3.4.0
```

#### PyLucene (pre Lucene index)
```bash
# PyLucene vyžaduje komplexnú inštaláciu
# Odporúčaný postup:
pip install lupyne  # Lupyne wrapper (jednoduchšie)

# Pre natívny PyLucene pozri:
# https://lucene.apache.org/pylucene/install.html
```

#### Aho-Corasick (pre entity matching)
```bash
pip install pyahocorasick
```

---

## Spustenie jednotlivých modulov

### 🕷️ 1. Crawler

```bash
# Základné spustenie (100 receptov)
python -m crawler.run --output data/raw --limit 100

# Plné crawlovanie (5,000+ receptov, ~2 hodiny)
python -m crawler.run --output data/raw --limit 10000

# S vlastným user-agent
python -m crawler.run --output data/raw --limit 100 --user-agent "VINFBot/1.0"
```

**Výstup:** `data/raw/www.food.com/*.html`

### 📄 2. Parser

```bash
# Parsovanie stiahnutých HTML
python -m parser.run --input data/raw --output data/normalized/recipes_foodcom.jsonl

# S detailným výstupom
python -m parser.run --input data/raw --output data/normalized/recipes_foodcom.jsonl --verbose
```

**Výstup:** `data/normalized/recipes_foodcom.jsonl` (jeden recept na riadok)

### 🌐 3. Wikipedia Spark Parser

```bash
# Stiahnuť Wikipedia dump (20 GB)
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2

# Spustenie Spark parsera
spark-submit spark_jobs/enwiki_spark_parser.py \
    --input enwiki-latest-pages-articles.xml.bz2 \
    --output data/normalized/wiki_culinary.jsonl
```

**Výstup:** `data/normalized/wiki_culinary.jsonl` (~9,700 kulinárskych článkov)

### 🔗 4. Entity Enricher

```bash
# Obohatenie receptov o Wikipedia entity
python -m entities.recipe_enricher \
    --recipes data/normalized/recipes_foodcom.jsonl \
    --wiki data/normalized/wiki_culinary.jsonl \
    --output data/normalized/recipes_enriched.jsonl
```

**Výstup:** `data/normalized/recipes_enriched.jsonl`

### 📚 5. Simple Indexer

```bash
# Vytvorenie Simple indexu (TSV súbory)
python -m indexer.simple_indexer \
    --mode build \
    --input data/normalized/recipes_enriched.jsonl \
    --output index/v1

# Info o indexe
python -m indexer.simple_indexer --mode info --input index/v1
```

**Výstup:**
```
index/v1/
├── terms.tsv       # term → df, idf
├── postings.tsv    # term → field, docId, tf
├── docmeta.tsv     # docId → metadata
└── field_lengths.json
```

### 🔍 6. Lucene Indexer

```bash
# Vytvorenie Lucene indexu (vyžaduje PyLucene)
python -m indexer.lucene_indexer \
    --input data/normalized/recipes_enriched.jsonl \
    --output index/v2 \
    --similarity bm25

# TF-IDF variant
python -m indexer.lucene_indexer \
    --input data/normalized/recipes_enriched.jsonl \
    --output index/v2_tfidf \
    --similarity tfidf
```

**Výstup:** `index/v2/` (Lucene binárne súbory)

### 🔎 7. Search CLI

```bash
# Vyhľadávanie v Simple indexe
python -m search_cli.run --index index/v1 --metric bm25 --q "chicken pasta" --k 10

# Vyhľadávanie v Lucene indexe
python -m search_cli.run --index index/v2 --metric bm25 --q "chocolate cake" --k 5

# S filtrami (len Lucene)
python -m search_cli.run --index index/v2 --metric bm25 --q "chicken" --k 10 \
    --filter '{"max_total_minutes": 30}'

# JSON výstup
python -m search_cli.run --index index/v1 --metric bm25 --q "pasta" --k 5 --json

# Quiet mód (len JSON)
python -m search_cli.run --index index/v1 --metric bm25 --q "pasta" --k 5 --json --quiet
```

### 📊 8. Evaluation

```bash
# Spustenie benchmarku
python -m eval.run --index index/v1 --queries eval/queries.tsv --qrels eval/qrels.tsv

# Porovnanie indexov
python -m eval.compare_indexes --index1 index/v1 --index2 index/v2
```

### 🧪 9. Testy

```bash
# Všetky unit testy
python -m pytest tests/ -v

# Integračné testy
python -m pytest tests/test_integration.py -v

# S coverage
python -m pytest tests/ --cov=. --cov-report=html
```

---

## Kompletný workflow (krok za krokom)

```bash
# === FÁZA 1: SETUP ===
git clone https://github.com/Marosko123/food-recipes-ir-pipeline.git
cd food-recipes-ir-pipeline
python3 -m venv venv
source venv/bin/activate
pip install -r packaging/requirements.txt

# === FÁZA 2: CRAWLING ===
python -m crawler.run --output data/raw --limit 1000
# Výsledok: ~1000 HTML súborov v data/raw/

# === FÁZA 3: PARSING ===
python -m parser.run --input data/raw --output data/normalized/recipes_foodcom.jsonl
# Výsledok: recipes_foodcom.jsonl s ~1000 receptami

# === FÁZA 4: INDEXING ===
python -m indexer.simple_indexer --mode build \
    --input data/normalized/recipes_foodcom.jsonl \
    --output index/v1
# Výsledok: Simple index v index/v1/

# === FÁZA 5: SEARCH ===
python -m search_cli.run --index index/v1 --metric bm25 --q "chicken" --k 10
# Výsledok: Top 10 receptov s "chicken"

# === FÁZA 6: VERIFY ===
python -m pytest tests/test_integration.py -v
# Výsledok: Všetky testy by mali prejsť
```

---

## Riešenie problémov

### ModuleNotFoundError

```bash
# Uistite sa že je aktivované venv
source venv/bin/activate

# Skontrolujte PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Lupyne/PyLucene nie je dostupný

```bash
# Pre PyLucene:
# 1. Nainštalujte Java JDK 17+
# 2. Stiahnite PyLucene z Apache
# 3. Skompilujte podľa návodu

# Alternatívne použite Simple index (v1) namiesto Lucene (v2)
python -m search_cli.run --index index/v1 --metric bm25 --q "chicken" --k 10
```

### PySpark nefunguje

```bash
# Overte Java
java -version  # Potrebujete 11+ alebo 17+

# Nastavte JAVA_HOME
export JAVA_HOME=$(/usr/libexec/java_home -v 17)  # macOS
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64  # Linux

# Overte Spark
pyspark --version
```

### Pamäťové problémy pri Spark

```bash
# Zvýšte pamäť
spark-submit --driver-memory 4g --executor-memory 4g \
    spark_jobs/enwiki_spark_parser.py ...
```

### Index je prázdny

```bash
# Skontrolujte či existujú vstupné dáta
ls -la data/normalized/recipes_enriched.jsonl
wc -l data/normalized/recipes_enriched.jsonl

# Spustite parser znova
python -m parser.run --input data/raw --output data/normalized/recipes_foodcom.jsonl --verbose
```

---

## Súbory projektu

```
food-recipes-ir-pipeline/
├── crawler/              # Web crawler
│   ├── __init__.py
│   ├── frontier.py       # URL frontier (BFS)
│   ├── robots.py         # robots.txt parser
│   ├── run.py            # Hlavný script
│   └── sitemap.py        # Sitemap parser
├── parser/               # HTML parser
│   ├── __init__.py
│   ├── html_parser.py    # JSON-LD + Regex extrakcia
│   └── run.py            # Hlavný script
├── indexer/              # Indexery
│   ├── __init__.py
│   ├── simple_indexer.py # Simple TSV index
│   └── lucene_indexer.py # PyLucene index
├── search_cli/           # Vyhľadávanie
│   ├── __init__.py
│   ├── run.py            # Search CLI
│   └── lupyne_searcher.py # Lupyne wrapper
├── entities/             # Entity linking
│   ├── __init__.py
│   ├── recipe_enricher.py # Aho-Corasick matcher
│   └── wiki_gazetteer.tsv # Wikipedia entity list
├── spark_jobs/           # Spark parsery
│   └── enwiki_spark_parser.py
├── eval/                 # Evaluácia
│   ├── run.py
│   └── benchmark_queries.py
├── tests/                # Testy
│   ├── test_parser.py
│   ├── test_enricher.py
│   ├── test_search.py
│   └── test_integration.py
├── data/                 # Dátové súbory
│   ├── raw/              # HTML súbory
│   ├── normalized/       # JSONL súbory
│   └── index/            # (staré) index súbory
├── index/                # Index súbory
│   ├── v1/               # Simple index (TSV)
│   └── v2/               # Lucene index
├── docs/                 # Dokumentácia
├── packaging/            # Packaging
│   ├── requirements.txt
│   └── run.sh
└── README.md
```

---

## Kontakt

**Autor:** Maroš Bednár  
**Email:** xbednarm1@stuba.sk  
**GitHub:** [Marosko123](https://github.com/Marosko123)

---

*Vytvorené pre VINF projekt - December 2025*
