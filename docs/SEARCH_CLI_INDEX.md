# Search CLI Documentation Index

Welcome to the Food Recipes Search CLI documentation! This index will help you find what you need quickly.

---

## 📚 Documentation Files

### 1. **[CLI_GUIDE.md](./CLI_GUIDE.md)** — Complete User Guide
**~5000 lines | Comprehensive reference**

The ultimate reference for all Search CLI features. Includes:
- Complete command syntax
- All filter types (30+)
- Real-world use cases
- Advanced examples
- Performance optimization
- Troubleshooting guide

**When to use:** Deep dive into features, learning all capabilities, troubleshooting issues.

---

### 2. **[search_cli/README.md](../search_cli/README.md)** — Quick Start
**~100 lines | Fast reference**

Quick reference for immediate use. Includes:
- Basic syntax
- Common examples
- Most-used filters
- Links to full docs

**When to use:** Quick lookup, first-time usage, checking syntax.

---

### 3. **[packaging/cli_examples.sh](../packaging/cli_examples.sh)** — Executable Examples
**Executable shell script | Real demonstrations**

Working examples you can run immediately. Includes:
- 6 common scenarios
- TF-IDF vs BM25 comparison
- Filter combinations
- Colored output

**When to use:** Learning by example, testing features, demos.

**Run it:**
```bash
bash packaging/cli_examples.sh
```

---

## 🚀 Quick Start Path

**New to Search CLI?** Follow this path:

1. **Start here:** [search_cli/README.md](../search_cli/README.md) (5 min)
2. **Try examples:** Run `bash packaging/cli_examples.sh` (2 min)
3. **Learn more:** Browse [CLI_GUIDE.md](./CLI_GUIDE.md) sections as needed

---

## 🔍 Find What You Need

### I want to...

| Goal | Go to |
|------|-------|
| Run my first search | [Quick Start](../search_cli/README.md#quick-start) |
| Understand TF-IDF vs BM25 | [Search Metrics](./CLI_GUIDE.md#search-metrics) |
| Use time filters | [Filter Options → Time](./CLI_GUIDE.md#time-filters) |
| Find low-calorie recipes | [Filter Options → Nutrition](./CLI_GUIDE.md#nutrition-filters) |
| Search by cuisine | [Filter Options → Category](./CLI_GUIDE.md#category-filters) |
| See real examples | [Common Use Cases](./CLI_GUIDE.md#common-use-cases) |
| Optimize performance | [Performance Tips](./CLI_GUIDE.md#performance-tips) |
| Fix an error | [Troubleshooting](./CLI_GUIDE.md#troubleshooting) |
| Integrate into script | [Advanced Examples](./CLI_GUIDE.md#advanced-examples) |
| See all filters | [Filter Reference Table](./CLI_GUIDE.md#filter-reference-table) |

---

## 📖 Documentation Sections

### In CLI_GUIDE.md:

1. **[Quick Start](./CLI_GUIDE.md#quick-start)** — Get running in 30 seconds
2. **[Command Syntax](./CLI_GUIDE.md#command-syntax)** — All arguments explained
3. **[Search Metrics](./CLI_GUIDE.md#search-metrics)** — TF-IDF vs BM25 deep dive
4. **[Filter Options](./CLI_GUIDE.md#filter-options)** — 30+ filter types
5. **[Common Use Cases](./CLI_GUIDE.md#common-use-cases)** — 8 real-world scenarios
6. **[Advanced Examples](./CLI_GUIDE.md#advanced-examples)** — Batch, integration, benchmarking
7. **[Performance Tips](./CLI_GUIDE.md#performance-tips)** — Speed optimization
8. **[Troubleshooting](./CLI_GUIDE.md#troubleshooting)** — Common issues + solutions
9. **[Output Format](./CLI_GUIDE.md#output-format)** — Understanding results
10. **[Filter Reference](./CLI_GUIDE.md#filter-reference-table)** — Complete filter list

---

## 🎯 Common Commands

### Basic Search
```bash
python3 search_cli/run.py --index data/index/v1 --q "chicken pasta" --k 5
```

### With Filters
```bash
python3 search_cli/run.py --index data/index/v1 --q "salad" --k 5 \
  --filter '{"max_total_minutes": 30, "min_rating": 4.0}'
```

### Compare Metrics
```bash
# TF-IDF
python3 search_cli/run.py --index data/index/v1 --metric tfidf --q "cake" --k 3

# BM25 (default)
python3 search_cli/run.py --index data/index/v1 --metric bm25 --q "cake" --k 3
```

---

## 🧪 Testing & Examples

### Run All Examples
```bash
bash packaging/cli_examples.sh
```

### Test Specific Feature
```bash
# Time filter
python3 search_cli/run.py --index data/index/v1 --q "pasta" \
  --filter '{"max_total_minutes": 30}' --k 5

# Nutrition filter
python3 search_cli/run.py --index data/index/v1 --q "chicken" \
  --filter '{"max_calories": 400, "min_protein": 25}' --k 5
```

---

## 📊 Stats

- **Total Documentation:** ~5,000 lines
- **Tested Commands:** 15+ verified
- **Filter Types:** 30+ documented
- **Use Cases:** 8 detailed scenarios
- **Examples:** 50+ code snippets

---

## 🆘 Support

**Need help?**
- Check [Troubleshooting](./CLI_GUIDE.md#troubleshooting) section
- Run `python3 search_cli/run.py --help`
- Contact: bednarmaros341@gmail.com

**Found a bug?**
- Report to: Maroš Bednár (AIS ID: 116822)
- Email: bednarmaros341@gmail.com

---

## 🔗 Related Documentation

- **[Main README](../README.md)** — Project overview
- **[API Documentation](./API_DOCUMENTATION.md)** — REST API reference
- **[Wikipedia Integration](./WIKIPEDIA_TITLES_TUTORIAL.md)** — Entity linking

---

**Last Updated:** October 21, 2025  
**Author:** Maroš Bednár (AIS ID: 116822)
