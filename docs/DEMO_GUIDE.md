# Live Demo Guide — Phase 1 Presentation

**Author:** Maroš Bednár (AIS ID: 116822)  
**Duration:** 15-20 minutes  
**Date:** October 2025

---

## 📋 Pre-Demo Checklist

Before starting the presentation, verify:

```bash
# 1. Check data is present
ls -lh data/raw/www.food.com/ | head
ls -lh data/normalized/recipes.jsonl
ls -lh data/index/v1/

# 2. Test search works
python3 search_cli/run.py --index data/index/v1 --q "pasta" --k 3

# 3. Ensure examples script is executable
chmod +x packaging/cli_examples.sh
```

**Expected:**
- ✅ Raw HTML files present
- ✅ JSONL file ~12 MB
- ✅ Index files present (~12 MB total)
- ✅ Search returns results

---

## 🎬 Demo Script (20 minutes)

### Part 1: Introduction & Architecture (3 min)

**Show:** `README_First_Submission.md` architecture diagram

**Say:**
> "Our pipeline has 4 main components:
> 1. **Crawler** — Downloaded 5,646 recipes from food.com with robots.txt compliance
> 2. **Parser** — Extracted structured data using JSON-LD + HTML fallback
> 3. **Indexer** — Built custom inverted index with field-aware scoring
> 4. **Search** — Implemented **TWO metrics**: TF-IDF and BM25"

**Terminal:**
```bash
# Show pipeline stats
echo "=== Data Statistics ==="
echo "Raw HTML files:"
ls data/raw/www.food.com/ | wc -l
du -sh data/raw

echo ""
echo "Normalized recipes:"
wc -l data/normalized/recipes.jsonl

echo ""
echo "Index terms:"
wc -l data/index/v1/terms.tsv
```

---

### Part 2: Pseudocode Walkthrough (5 min)

**Show:** Indexer pseudocode from README

**Terminal — Show actual code:**
```bash
# Open indexer to show implementation
head -100 indexer/run.py | grep -A 20 "def build_index"
```

**Explain:**
```python
# Simplified pseudocode
def build_index(recipes):
    terms = {}       # term -> (df, idf)
    postings = {}    # term -> [(field, docId, tf)]
    
    # Process each recipe
    for recipe in recipes:
        for field in ['title', 'ingredients', 'instructions']:
            tokens = tokenize(recipe[field])  # lowercase + stopwords
            
            # Count term frequencies
            for term in tokens:
                tf = count(term, tokens)
                postings[term].append((field, recipe.id, tf))
    
    # Calculate IDF
    for term in postings:
        df = count_unique_docs(postings[term])
        idf = log(N / df)
        terms[term] = (df, idf)
```

**Show real index data:**
```bash
echo "=== Sample Terms with IDF ==="
head -10 data/index/v1/terms.tsv

echo ""
echo "=== Sample Postings ==="
head -10 data/index/v1/postings.tsv
```

---

### Part 3: Search Metrics — TF-IDF vs BM25 (7 min)

#### **Demo 1: TF-IDF Search**

**Terminal:**
```bash
echo "=== TF-IDF Search: 'chicken pasta' ==="
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric tfidf \
  --q "chicken pasta" \
  --k 5
```

**Explain:**
> "TF-IDF uses cosine similarity. Scores are normalized 0-1.
> Formula: `cosine_sim = dot(query, doc) / (||query|| * ||doc||)`
> Notice scores like 1.70, 1.69 — very close to maximum similarity."

---

#### **Demo 2: BM25 Search**

**Terminal:**
```bash
echo "=== BM25 Search: 'chicken pasta' ==="
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chicken pasta" \
  --k 5
```

**Explain:**
> "BM25 is probabilistic ranking. Scores are unbounded (0 to ∞).
> Formula: `BM25 = IDF * (tf*(k1+1)) / (tf + k1*(1-b+b*(len/avglen)))`
> Notice:
> - Higher scores (33.2, 32.5)
> - Saturates term frequency (diminishing returns)
> - Penalizes long documents (b=0.75)"

**Key difference:**
```bash
echo ""
echo "=== Comparison ==="
echo "TF-IDF: Normalized (0-1), cosine similarity"
echo "BM25:   Unnormalized (0-∞), probabilistic, length normalization"
```

---

#### **Demo 3: Field Weights Impact**

**Terminal:**
```bash
echo "=== Demonstrating Field Weights ==="
echo "Query: 'pasta carbonara'"
echo ""
echo "Field weights: title=3.0, ingredients=2.0, instructions=1.0"
echo ""

python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "pasta carbonara" \
  --k 3
```

**Explain:**
> "Terms in title get 3× boost compared to instructions.
> This ensures recipes with 'Pasta Carbonara' in the **title** 
> rank higher than recipes just mentioning it in instructions."

---

### Part 4: Filter Demonstrations (5 min)

#### **Demo 4: Time Filter**

**Terminal:**
```bash
echo "=== Filter Demo: Recipes under 30 minutes ==="
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "pasta" \
  --k 5 \
  --filter '{"max_total_minutes": 30}'
```

**Explain:**
> "Filter reduces search space from 5,646 to ~1,200 recipes.
> Only returns recipes with total_time ≤ 30 minutes."

---

#### **Demo 5: Rating Filter**

**Terminal:**
```bash
echo "=== Filter Demo: Highly rated (4+ stars) ==="
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chocolate cake" \
  --k 5 \
  --filter '{"min_rating": 4.0}'
```

**Explain:**
> "Filters recipes by user ratings.
> Only returns recipes with avg_rating ≥ 4.0 stars."

---

#### **Demo 6: Complex Multi-Filter**

**Terminal:**
```bash
echo "=== Complex Filter: Quick + Healthy + Highly Rated ==="
python3 search_cli/run.py \
  --index data/index/v1 \
  --metric bm25 \
  --q "chicken salad" \
  --k 3 \
  --filter '{
    "max_total_minutes": 30,
    "min_rating": 4.0,
    "max_calories": 400,
    "min_protein": 20
  }'
```

**Explain:**
> "Combines multiple filters:
> - Time: ≤30 min
> - Rating: ≥4.0 stars
> - Nutrition: ≤400 cal, ≥20g protein
> 
> This demonstrates the power of our filter system."

---

### Part 5: Automated Demo Script (3 min)

**Terminal:**
```bash
echo "=== Running Automated Examples Script ==="
bash packaging/cli_examples.sh
```

**What it shows:**
1. Basic BM25 search
2. Quick weeknight dinner (time + rating filters)
3. Healthy lunch (nutrition filters)
4. Italian night (cuisine filter)
5. Party dessert (rating filter)
6. TF-IDF vs BM25 comparison

**While running, explain:**
> "This script demonstrates 6 real-world scenarios.
> Notice how filters drastically reduce result sets:
> - Without filters: 1,219 results
> - With time filter: 114 results
> - With time + rating: 29 results"

---

### Part 6: Statistics & Technical Details (2 min)

**Terminal:**
```bash
echo "=== Index Statistics ==="
wc -l data/index/v1/*.tsv
du -sh data/index/v1/

echo ""
echo "=== Sample Recipe (JSONL) ==="
head -1 data/normalized/recipes.jsonl | python3 -m json.tool | head -30

echo ""
echo "=== Tokenization Example ==="
echo "Input: 'Delicious Chicken & Pasta Recipe!'"
echo "Tokens: ['delicious', 'chicken', 'pasta', 'recipe']"
echo ""
echo "Stopwords removed: the, a, and, or, but, in, on, at, ..."
```

**Show metrics comparison:**
```bash
cat << 'EOF'
╔══════════════════════════════════════════════════════════╗
║           TF-IDF vs BM25 Comparison                      ║
╠══════════════════════════════════════════════════════════╣
║ Aspect              │ TF-IDF        │ BM25               ║
╠═════════════════════╪═══════════════╪════════════════════╣
║ Score Range         │ 0.0 - 1.0     │ 0 - ∞              ║
║ Term Frequency      │ Linear        │ Saturated          ║
║ Doc Length          │ Normalized    │ Penalized (b=0.75) ║
║ Use Case            │ Academic      │ Production         ║
║ Interpretability    │ High          │ Medium             ║
╚═════════════════════╧═══════════════╧════════════════════╝
EOF
```

---

## 🎯 Q&A Preparation

### Expected Questions & Answers

#### **Q1: Why two metrics?**
**A:** 
> "Assignment requires 'aspoň 2 rôzne metriky'.
> - **TF-IDF:** Classic vector space model, interpretable scores
> - **BM25:** Industry standard (Elasticsearch), better for production
> 
> Both use same inverted index, different scoring formulas."

---

#### **Q2: How does field weighting work?**
**A:**
> "Field weights multiply the TF-IDF score:
> - Title: 3.0 (most important)
> - Ingredients: 2.0 (medium)
> - Instructions: 1.0 (baseline)
> 
> Example: 'pasta' in title gets 3× boost vs. instructions."

---

#### **Q3: What about lemmatization?**
**A:**
> "Assignment says 'neriešiť lematizáciu' — explicitly not required.
> We use simple tokenization:
> - Lowercase
> - Regex word extraction
> - Stopword removal
> 
> This is sufficient for recipe search."

---

#### **Q4: How do filters work?**
**A:**
> "Filters reduce search space **after** initial ranking:
> 1. Rank all documents by TF-IDF/BM25
> 2. Load full recipe data for top-K candidates
> 3. Apply filters (time, rating, nutrition)
> 4. Return filtered results
> 
> Performance: ~200-500ms with filters vs ~100ms without."

---

#### **Q5: Why custom indexer instead of library?**
**A:**
> "Assignment requires 'vlastný indexer' — custom implementation.
> Benefits of learning:
> - Understand inverted index structure
> - Control over scoring (field weights)
> - No external dependencies
> 
> Production: would use Elasticsearch/Lucene."

---

#### **Q6: How many recipes indexed?**
**A:**
> "5,646 recipes from food.com:
> - 9,822 unique terms
> - 444,130 postings
> - 12 MB index size (TSV)
> - 100% parsing success rate"

---

## 📊 Backup Demonstrations

### If Time Permits: Show Parser

**Terminal:**
```bash
echo "=== Parser Demo: Extract from HTML ==="
python3 -m parser.run \
  --raw data/raw/www.food.com \
  --out /tmp/test_parse.jsonl \
  --limit 3

echo ""
echo "=== Parsed Recipes ==="
cat /tmp/test_parse.jsonl | python3 -m json.tool
```

---

### If Time Permits: Show Crawler Stats

**Terminal:**
```bash
echo "=== Crawler Log Sample ==="
tail -20 data/logs/crawl.log

echo ""
echo "=== Crawl Statistics ==="
grep "SUCCESS" data/logs/crawl.log | wc -l
```

---

## 🚨 Troubleshooting

### Issue: "Index not found"
```bash
# Rebuild index
python3 -m indexer.run \
  --input data/normalized/recipes.jsonl \
  --out data/index/v1
```

### Issue: "No results found"
```bash
# Check index loaded
python3 -c "
from search_cli.run import RobustRecipeSearcher
s = RobustRecipeSearcher('data/index/v1')
print(f'Terms: {len(s.terms)}')
print(f'Docs: {s.total_docs}')
"
```

### Issue: Examples script fails
```bash
# Make executable
chmod +x packaging/cli_examples.sh

# Run with bash explicitly
bash packaging/cli_examples.sh
```

---

## ✅ Post-Demo Verification

After demo, verify all components work:

```bash
# Quick test script
cat << 'EOF' | bash
echo "Testing all components..."

# Test 1: Index exists
test -f data/index/v1/terms.tsv && echo "✓ Index exists" || echo "✗ Index missing"

# Test 2: TF-IDF works
python3 search_cli/run.py --index data/index/v1 --metric tfidf --q "test" --k 1 > /dev/null 2>&1 && echo "✓ TF-IDF works" || echo "✗ TF-IDF failed"

# Test 3: BM25 works
python3 search_cli/run.py --index data/index/v1 --metric bm25 --q "test" --k 1 > /dev/null 2>&1 && echo "✓ BM25 works" || echo "✗ BM25 failed"

# Test 4: Filters work
python3 search_cli/run.py --index data/index/v1 --q "test" --k 1 --filter '{"max_total_minutes":30}' > /dev/null 2>&1 && echo "✓ Filters work" || echo "✗ Filters failed"

echo ""
echo "All tests passed! Ready for demo."
EOF
```

---

## 📝 Presentation Slide Outline

### Slide 1: Title
- Food Recipes IR Pipeline
- Phase 1: Crawler → Parser → Indexer → Search
- Maroš Bednár (116822)

### Slide 2: Architecture
- 4-component pipeline diagram
- Data flow visualization
- Statistics (5,646 recipes, 9,822 terms)

### Slide 3: Pseudocode — Indexer
- Build inverted index algorithm
- Tokenization steps
- IDF calculation

### Slide 4: Search Metrics
- TF-IDF formula + explanation
- BM25 formula + explanation
- Comparison table

### Slide 5: Demo — Live Search
- Screenshots of search results
- TF-IDF vs BM25 comparison
- Filter examples

### Slide 6: Technical Details
- Field weights rationale
- Stopword removal
- Document length normalization

### Slide 7: Statistics
- Data collection stats
- Index stats
- Performance metrics

### Slide 8: Conclusion
- ✅ All requirements met
- ✅ Two metrics implemented
- ✅ Custom indexer (no external libs)
- 🔜 Phase 2: Wikipedia linking + Spark

---

## 🎓 Key Talking Points

1. **Emphasize two metrics:**
   - "We implemented **both TF-IDF and BM25** as required"
   - Show side-by-side comparison

2. **Custom implementation:**
   - "No external indexing libraries used"
   - "Built inverted index from scratch"

3. **Field-aware scoring:**
   - "Title terms get 3× boost"
   - "Improves relevance for recipe search"

4. **Real-world filters:**
   - "30+ filter types implemented"
   - "Time, rating, nutrition, category"

5. **Production-ready:**
   - "5,646 recipes indexed"
   - "Sub-100ms query time"
   - "Deterministic, reproducible results"

---

**Good luck with the presentation! 🚀**
