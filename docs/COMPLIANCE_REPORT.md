# ✅ Validation Report: Compliance with Course Requirements

This document validates the project against the specific constraints provided by the instructor.

## 🟢 Summary: FULLY COMPLIANT
The project strictly adheres to all "Allowed" and "Recommended" technologies and avoids all "Disallowed" ones.

---

## 📋 Detailed Validation

### 1. 🗄️ Databases (SQL vs NoSQL vs Files)
*   **Rule:** SQL databases are **FORBIDDEN**. Use CSV/TSV or NoSQL.
*   **Project Status:** ✅ **Compliant**
    *   **Storage:** Data is stored in **JSONL** (Line-delimited JSON) and **TSV** (Tab-Separated Values) files in the `data/` directory.
    *   **Verification:** No usage of `sqlite3`, `PostgreSQL`, or `MySQL`.
    *   **Files:** `data/normalized/recipes.jsonl`, `entities/wiki_gazetteer.tsv`.

### 2. 🐍 Programming Languages
*   **Rule:** Python and Java are highly recommended.
*   **Project Status:** ✅ **Compliant**
    *   **Core:** Written in **Python 3.14**.
    *   **Underlying:** Uses **Java** (JVM) for PyLucene and Apache Spark.

### 3. ⚡ Distributed Processing
*   **Rule:** Spark is recommended.
*   **Project Status:** ✅ **Compliant**
    *   **Implementation:** Uses **Apache Spark (PySpark)** in `spark_jobs/enwiki_spark_parser.py` to process the 27GB Wikipedia XML dump.
    *   **Why:** To filter culinary entities from millions of articles efficiently.

### 4. 🔍 Indexing
*   **Rule:** Lucene/PyLucene recommended. Custom index allowed.
*   **Project Status:** ✅ **Compliant**
    *   **Primary:** Uses **PyLucene** (via `lupyne` wrapper) for the production index (`index/lucene/v2`).
    *   **Secondary:** Includes a **Custom Python Indexer** (TSV-based) in `indexer/run.py` as a baseline/educational implementation.

### 5. 🖥️ Search Interface
*   **Rule:** Command line (CLI) is sufficient.
*   **Project Status:** ✅ **Compliant (Exceeds)**
    *   **CLI:** Fully functional CLI in `search_cli/run.py`.
    *   **Bonus:** Includes a Next.js Web UI (allowed as an extra).

### 6. 📊 Evaluation
*   **Rule:** Evaluation is required (Gold standard or manual).
*   **Project Status:** ✅ **Compliant**
    *   **Implementation:** `eval/run.py` calculates **Precision@k**, **Recall@k**, and **MAP**.
    *   **Data:** Uses manually created "Gold Standard" relevance judgments in `eval/qrels.tsv`.

### 7. 🚫 Forbidden Libraries (Pure Python)
*   **Rule:** `re`, `requests`, `selenium` allowed. **NO `pandas`, NO `NLTK`**.
*   **Project Status:** ✅ **Compliant**
    *   **Pandas:** **NOT USED**. Data processing is done using standard Python `json`, `csv` modules, and Spark DataFrames (which are allowed).
    *   **NLTK:** **NOT USED**. Tokenization is done using `re` (Regex) and PyLucene's `StandardAnalyzer`.
    *   **Allowed Libs Used:** `requests` (Crawler), `re` (Parser), `ahocorasick` (Enrichment).

---

## 🛠️ Technology Stack Summary

| Component | Technology Used | Status |
| :--- | :--- | :--- |
| **Database** | JSONL / TSV Files | ✅ Allowed |
| **Language** | Python 3.14 | ✅ Recommended |
| **Big Data** | Apache Spark (PySpark) | ✅ Recommended |
| **Indexing** | PyLucene (Java wrapper) | ✅ Recommended |
| **NLP/Text** | Regex (`re`), Aho-Corasick | ✅ Allowed |
| **Forbidden** | Pandas, NLTK, SQL | ✅ **AVOIDED** |
