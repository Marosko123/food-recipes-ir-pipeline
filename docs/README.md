# Food Recipes Documentation

This directory contains the complete documentation for the Food Recipes project.

## Documentation Structure

- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Complete API reference and usage examples
- **[README.md](../README.md)** - Main project documentation and quick start guide

## Project Overview

Food Recipes is a comprehensive Recipes Information Retrieval (IR) Pipeline that provides:

- **Web Crawling:** Automated recipe collection from food.com
- **Data Parsing:** Intelligent HTML parsing with JSON-LD support  
- **Search Engine:** TF-IDF and BM25 ranking algorithms
- **Entity Linking:** Wikipedia-based ingredient and cuisine linking
- **Web Interface:** Modern, responsive Next.js frontend
- **Wikipedia Integration:** Comprehensive recipe knowledge base

## Quick Start

1. **Installation:**
   ```bash
   python setup_and_launch.py --install-deps
   ```

2. **Run the application:**
   ```bash
   python setup_and_launch.py --gui
   ```

3. **Access the web interface:**
   ```bash
   python api_server.py
   # Then visit http://localhost:5000
   ```

## Core Components

### Pipeline Phases

- **Phase A:** Seed extraction from sitemaps and robots.txt
- **Phase B:** Web crawling with rate limiting and retry logic
- **Phase C:** HTML parsing with JSON-LD and fallback heuristics
- **Phase D:** Search index construction and ranking algorithms
- **Phase E:** Entity linking with Wikipedia integration
- **Phase F:** Wikipedia data collection and processing

### Data Formats

- **Raw HTML:** `data/raw/{domain}/{doc_id}.html`
- **Normalized JSONL:** `data/normalized/recipes.jsonl`
- **Search Index:** `data/index/v1/` (terms.tsv, postings.tsv, docmeta.tsv)
- **Entity Links:** `data/entities/links.jsonl`

## Development

For development setup and contribution guidelines, see the main [README.md](../README.md).

## Support

- **Author:** Maroš Bednár
- **Email:** bednarmaros341@gmail.com
- **AIS ID:** 116822
