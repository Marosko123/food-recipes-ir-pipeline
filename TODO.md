# TODO List — Food Recipes IR Pipeline

**Dátum vytvorenia:** 24. október 2025  
**Status projektu:** Wikipedia integrácia HOTOVÁ ✅ | PyLucene implementácia CHÝBA ❌

---

## 📊 QUICK SUMMARY

### ✅ ČO JE HOTOVÉ (5,646 receptov + 399 Wikipedia entít)

1. **Crawler** — RAW HTML z food.com (5,646 súborov v `data/raw/`)
2. **Parser** — `recipes_foodcom.jsonl` (12 MB, kompletná schéma)
3. **Wikipedia** — `wiki_culinary.jsonl` (399 entít, plné abstrakty, origin metadata)
4. **Enrichment** — `recipes_enriched.jsonl` (34 MB, 14,102 wiki links) **← FINÁLNY PRE INDEXÁCIU**
5. **Kvalita** — 91.9% dishes má origin metadata, 91.2% receptov obohatených

### ❌ ČO TREBA DOKONČIŤ (PyLucene)

1. **PyLucene Indexer** — `indexer/lucene_indexer.py` (BM25 + TF-IDF)
2. **PyLucene Searcher** — `search_cli/lucene_searcher.py` (filtre, highlighting)
3. **Evaluácia** — `eval/run.py` (P@k, MAP, nDCG)
4. **run.sh targety** — `index_lucene`, `search_lucene`, `eval`, `all`
5. **Dokumentácia** — Aktualizovať README, vytvoriť `wiki_3pages.md`

---

## 🎯 PRIORITY TASKS (v poradí)

### 1. ⚠️ KRITICKÉ — PyLucene Indexer

**Súbor:** `indexer/lucene_indexer.py`  
**Cieľ:** Vytvoriť Lucene index v `index/lucene/v2` z `recipes_enriched.jsonl`

#### Špecifikácia (§7 copilot-instructions.md):

```python
# Index Configuration
INDEX_PATH = "index/lucene/v2"
INPUT_FILE = "data/normalized/recipes_enriched.jsonl"

# Fields (s boostami):
- title_text         → TextField, boost 2.0, stored
- ingredients_text   → TextField, boost 1.5, stored
- instructions_text  → TextField, boost 1.0, stored
- wiki_abstracts     → TextField, boost 1.0, stored  # NOVÉ: zo wiki_links
- ingredients_kw     → StringField (repeated), pre exact match filter
- cuisine_kw         → StringField (repeated), pre cuisine filter
- total_minutes      → IntPoint + StoredField, pre time range filter
- url                → StoredField
- docId              → StoredField

# Analyzer:
StandardAnalyzer (anglické stopwords)

# Similarity:
- Default: BM25Similarity
- Voliteľné: ClassicSimilarity (TF-IDF) cez --similarity flag
```

#### Implementačné kroky:

1. **Imports:**
   ```python
   import lucene
   from org.apache.lucene.analysis.standard import StandardAnalyzer
   from org.apache.lucene.document import Document, Field, TextField, StringField, StoredField, IntPoint
   from org.apache.lucene.index import IndexWriter, IndexWriterConfig
   from org.apache.lucene.store import FSDirectory
   from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity
   from java.nio.file import Paths
   ```

2. **CLI argumenty:**
   ```bash
   --input data/normalized/recipes_enriched.jsonl
   --output index/lucene/v2
   --similarity bm25|tfidf  # default: bm25
   ```

3. **Indexovanie wiki_links:**
   ```python
   # Extrahuj abstrakty z wiki_links pre každý recept
   wiki_abstracts = []
   for link in recipe.get('wiki_links', []):
       if link.get('abstract'):
           wiki_abstracts.append(link['abstract'])
   
   # Pridaj do indexu
   doc.add(TextField("wiki_abstracts", " ".join(wiki_abstracts), Field.Store.YES))
   ```

4. **Error handling:**
   - Korektne zlyhať ak PyLucene nie je nainštalovaný
   - Logovať počet indexovaných dokumentov
   - Uložiť štatistiky do `data/logs/indexing.log`

#### Výstup:
- `index/lucene/v2/` — Lucene index directory
- `data/logs/indexing.log` — Log s počtom docs, časom, chybami

---

### 2. ⚠️ KRITICKÉ — PyLucene Searcher

**Súbor:** `search_cli/lucene_searcher.py`  
**Cieľ:** Multi-field search s filtrami a highlighting

#### Špecifikácia (§7 copilot-instructions.md):

```python
# CLI Interface:
python3 search_cli/lucene_searcher.py \
  --query "mexican chicken nachos" \
  --k 10 \
  --include-ingredients "onion,tomato" \
  --cuisine "Mexican,Italian" \
  --max-total-minutes 30 \
  --similarity bm25 \
  --highlight

# Multi-field Query (s boostami):
title_text^2.0 OR ingredients_text^1.5 OR instructions_text^1.0 OR wiki_abstracts^1.0

# Filters (BooleanQuery MUST):
- ingredients_kw: TermQuery pre každú required ingredient
- cuisine_kw: TermQuery pre každú allowed cuisine (OR)
- total_minutes: IntPoint.newRangeQuery(0, max_minutes)

# Highlighting:
UnifiedHighlighter na title_text, ingredients_text, instructions_text
```

#### Implementačné kroky:

1. **Query Builder:**
   ```python
   from org.apache.lucene.queryparser.classic import MultiFieldQueryParser
   from org.apache.lucene.search import BooleanQuery, BooleanClause, TermQuery, IntPoint
   
   # Multi-field s boostami
   fields = ["title_text", "ingredients_text", "instructions_text", "wiki_abstracts"]
   boosts = {
       "title_text": 2.0,
       "ingredients_text": 1.5,
       "instructions_text": 1.0,
       "wiki_abstracts": 1.0
   }
   ```

2. **Filtre:**
   ```python
   # Must-include ingredients
   if args.include_ingredients:
       for ing in args.include_ingredients.split(','):
           ing_query = TermQuery(Term("ingredients_kw", ing.strip().lower()))
           boolean_query.add(ing_query, BooleanClause.Occur.MUST)
   
   # Cuisine filter (OR)
   if args.cuisine:
       cuisine_query = BooleanQuery.Builder()
       for c in args.cuisine.split(','):
           cuisine_query.add(TermQuery(Term("cuisine_kw", c.strip())), BooleanClause.Occur.SHOULD)
   
   # Time range
   if args.max_total_minutes:
       time_query = IntPoint.newRangeQuery("total_minutes", 0, args.max_total_minutes)
       boolean_query.add(time_query, BooleanClause.Occur.MUST)
   ```

3. **Highlighting:**
   ```python
   from org.apache.lucene.search.highlight import UnifiedHighlighter
   
   highlighter = UnifiedHighlighter(searcher, analyzer)
   highlights = highlighter.highlight("title_text", query, topDocs)
   ```

4. **Output formát:**
   - Console: Pekný výpis s highlighting
   - TSV: `eval/runs/lucene_{similarity}_{timestamp}.tsv` (qid \t Q0 \t docid \t rank \t score \t run_id)

#### Výstup:
- Console output s highlighted snippetmi
- `eval/runs/lucene_bm25_20251024.tsv` — TREC formát pre evaluáciu

---

### 3. 🔸 DÔLEŽITÉ — Evaluácia

**Súbor:** `eval/run.py`  
**Cieľ:** Porovnať baseline (v1) vs PyLucene (v2) pre BM25 a TF-IDF

#### Špecifikácia (§9 copilot-instructions.md):

```python
# Spustiť queries.tsv nad indexmi:
1. baseline (index/v1, TSV)
2. lucene_bm25 (index/lucene/v2, BM25Similarity)
3. lucene_tfidf (index/lucene/v2, ClassicSimilarity)

# Metriky (pre každý query):
- P@1, P@5, P@10
- Recall@5, Recall@10
- MAP (Mean Average Precision)
- nDCG@10 (voliteľne)

# Výstup:
eval/metrics.tsv — tabulka s metrikami pre všetky runs
```

#### Implementačné kroky:

1. **Načítať qrels:**
   ```python
   # eval/qrels.tsv format: qid 0 docid relevance
   qrels = {}
   with open('eval/qrels.tsv') as f:
       for line in f:
           qid, _, docid, rel = line.strip().split('\t')
           qrels.setdefault(qid, {})[docid] = int(rel)
   ```

2. **Spustiť queries pre každý engine:**
   ```python
   engines = ['baseline', 'lucene_bm25', 'lucene_tfidf']
   for engine in engines:
       for qid, query_text in queries:
           results = search(engine, query_text, k=100)
           # Uložiť do eval/runs/{engine}_{timestamp}.tsv
   ```

3. **Vypočítať metriky:**
   ```python
   def calculate_metrics(run_file, qrels):
       metrics = {}
       for qid in queries:
           retrieved = load_run(run_file, qid)
           relevant = qrels[qid]
           
           metrics[qid] = {
               'P@1': precision_at_k(retrieved, relevant, 1),
               'P@5': precision_at_k(retrieved, relevant, 5),
               'P@10': precision_at_k(retrieved, relevant, 10),
               'Recall@10': recall_at_k(retrieved, relevant, 10),
               'MAP': average_precision(retrieved, relevant)
           }
       return metrics
   ```

4. **Výstup:**
   ```tsv
   engine       qid  P@1   P@5   P@10  Recall@10  MAP
   baseline     q1   1.0   0.8   0.7   0.65       0.82
   lucene_bm25  q1   1.0   1.0   0.9   0.85       0.91
   lucene_tfidf q1   1.0   0.8   0.8   0.75       0.85
   ```

#### Výstup:
- `eval/metrics.tsv` — Porovnanie všetkých engineov
- `docs/wiki_3pages.md` — Komentár k výsledkom (BM25 vs TF-IDF)

---

### 4. 🔸 DÔLEŽITÉ — packaging/run.sh targety

**Súbor:** `packaging/run.sh`  
**Cieľ:** Pridať chýbajúce targety podľa §8

#### Špecifikácia:

```bash
# HOTOVÉ:
crawl        — Crawler (RAW HTML)
parse        — Parser Food.com → recipes_foodcom.jsonl
wiki_parse   — Wikipedia parsing → wiki_culinary.jsonl + wiki_gazetteer.tsv
enrich       — Recipe enrichment → recipes_enriched.jsonl
wiki_clean   — Zmaže wiki artefakty (SAFE DELETE)

# CHÝBA:
index_lucene    — PyLucene indexing z recipes_enriched.jsonl
search_lucene   — PyLucene search s filtrami
eval            — Evaluácia (BM25 vs TF-IDF vs baseline)
all             — parse → wiki_parse → enrich → index_lucene → eval
```

#### Implementačné kroky:

```bash
# 1. index_lucene target
index_lucene() {
    echo "🔨 Building PyLucene index from recipes_enriched.jsonl..."
    python3 indexer/lucene_indexer.py \
        --input data/normalized/recipes_enriched.jsonl \
        --output index/lucene/v2 \
        --similarity bm25
    echo "✅ Index built: index/lucene/v2"
}

# 2. search_lucene target
search_lucene() {
    # Príklady queries
    python3 search_cli/lucene_searcher.py \
        --query "${1:-mexican chicken}" \
        --k "${2:-10}" \
        --similarity bm25 \
        --highlight
}

# 3. eval target
eval() {
    echo "📊 Running evaluation..."
    python3 eval/run.py \
        --queries eval/queries.tsv \
        --qrels eval/qrels.tsv \
        --output eval/metrics.tsv
    echo "✅ Metrics saved: eval/metrics.tsv"
}

# 4. all target (E2E pipeline)
all() {
    parse
    wiki_parse
    enrich
    index_lucene
    eval
}
```

#### Výstup:
- Funkčné targety: `./packaging/run.sh index_lucene`, `search_lucene`, `eval`, `all`

---

### 5. 🔹 NÍZKA PRIORITA — Dokumentácia

**Súbory:** `docs/README.md`, `docs/wiki_3pages.md`

#### 5.1 Aktualizovať README.md

```markdown
# Nové sekcie:

## 5. Indexing (PyLucene)
./packaging/run.sh index_lucene

## 6. Search (PyLucene)
./packaging/run.sh search_lucene --query "mexican chicken" --k 10 --cuisine Mexican --max-total-minutes 30

## 7. Evaluation
./packaging/run.sh eval
```

#### 5.2 Vytvoriť wiki_3pages.md

```markdown
# Wikipedia Integration — Evaluation Report

## 1. Wikipedia Entity Extraction
- 399 culinary entities (310 dishes, 62 ingredients, 22 cuisines, ...)
- 91.9% dishes have origin metadata
- Full abstracts (avg 1,419 chars)

## 2. Recipe Enrichment
- 5,646 recipes → 5,147 enriched (91.2%)
- 14,102 wiki links with abstracts + origin metadata

## 3. Search Performance (BM25 vs TF-IDF)
[Po evaluácii: tabulka s P@k, MAP, nDCG]

## 4. Examples
[Screenshots/výpisy highlighted queries]
```

---

## 📦 DÁTOVÉ SÚBORY (Status)

| Súbor | Veľkosť | Status | Použitie |
|-------|---------|--------|----------|
| `data/raw/www.food.com/*.html` | 5,646 súborov | ✅ Source | Crawler output |
| `data/normalized/recipes_foodcom.jsonl` | 12 MB | ✅ Source | Food.com parse |
| `data/normalized/wiki_culinary.jsonl` | 409 KB | ✅ Knowledge | Wikipedia entities |
| `entities/wiki_gazetteer.tsv` | - | ✅ Mapping | Aho-Corasick |
| **`data/normalized/recipes_enriched.jsonl`** | **34 MB** | **✅ FINAL** | **← INDEXOVAŤ** |
| `index/v1/` | - | ✅ Baseline | TSV index (pre porovnanie) |
| `index/lucene/v2/` | - | ❌ Chýba | PyLucene index |
| `eval/queries.tsv` | - | ✅ Ready | Evaluation queries |
| `eval/qrels.tsv` | - | ✅ Ready | Relevance judgments |
| `eval/metrics.tsv` | - | ❌ Chýba | Evaluation output |

---

## 🚀 EXECUTION PLAN (Ako postupovať)

### Fáza 1: PyLucene Setup (1-2 hodiny)
1. Overiť PyLucene inštaláciu: `python3 -c "import lucene; lucene.initVM()"`
2. Ak chýba → README s inštrukciami (Java JDK 11+, ant build)
3. Otestovať basic indexing + search na malej vzorke (10 receptov)

### Fáza 2: Implementácia Indexera (2-3 hodiny)
1. Vytvoriť `indexer/lucene_indexer.py` podľa špecifikácie
2. Implementovať BM25/TF-IDF prepínač
3. Indexovať wiki_abstracts z wiki_links
4. Otestovať na recipes_enriched.jsonl (5,646 receptov)
5. Pridať `index_lucene` target do run.sh

### Fáza 3: Implementácia Searchera (2-3 hodiny)
1. Vytvoriť `search_cli/lucene_searcher.py` podľa špecifikácie
2. Implementovať multi-field query s boostami
3. Implementovať filtre (ingredients, cuisine, time)
4. Implementovať UnifiedHighlighter
5. Output do TREC formátu (eval/runs/*.tsv)
6. Pridať `search_lucene` target do run.sh

### Fáza 4: Evaluácia (1-2 hodiny)
1. Aktualizovať `eval/run.py` pre PyLucene runs
2. Spustiť queries.tsv pre baseline, BM25, TF-IDF
3. Vypočítať P@k, MAP, nDCG
4. Uložiť do eval/metrics.tsv
5. Pridať `eval` target do run.sh

### Fáza 5: Dokumentácia (1 hodina)
1. Aktualizovať README.md
2. Vytvoriť wiki_3pages.md s výsledkami
3. Pridať príklady použitia

**Celkový čas:** 7-11 hodín

---

## ⚠️ KRITICKÉ POZNÁMKY

### PyLucene Dependencies
```bash
# Vyžaduje:
- Java JDK 11+ (OpenJDK alebo Oracle)
- Apache Ant
- GCC/Clang (pre build)
- Python 3.8+

# Inštalácia (macOS):
brew install openjdk@11 ant
pip install lucene  # alebo manuálny build z source
```

### SAFE DELETE Politika
**NEDOTÝKAŤ SA:**
- `data/raw/**` (crawler dáta)
- `data/normalized/recipes_foodcom.jsonl` (pôvodný parse)
- `index/v1/**` (baseline TSV index)

**MÔŽEŠ ZMAZAŤ:**
- `index/lucene/v2/**` (pri rebuildoch)
- `eval/runs/**` (staré run files)
- `data/logs/**` (staré logy)

### Debugging Tips
```bash
# Test PyLucene import
python3 -c "import lucene; print(lucene.VERSION)"

# Test small index (10 docs)
head -n 10 data/normalized/recipes_enriched.jsonl > /tmp/test.jsonl
python3 indexer/lucene_indexer.py --input /tmp/test.jsonl --output /tmp/test_index

# Check index stats
python3 -c "import lucene; lucene.initVM(); from org.apache.lucene.index import DirectoryReader; from org.apache.lucene.store import FSDirectory; from java.nio.file import Paths; reader = DirectoryReader.open(FSDirectory.open(Paths.get('index/lucene/v2'))); print(f'Docs: {reader.numDocs()}')"
```

---

## 📊 PROGRESS TRACKING

### Completed (60% projektu)
- [x] Crawler (5,646 HTML)
- [x] Parser (recipes_foodcom.jsonl)
- [x] Wikipedia parsing (wiki_culinary.jsonl)
- [x] Recipe enrichment (recipes_enriched.jsonl)
- [x] Entity quality verification (91.9% origin coverage)
- [x] SAFE DELETE cleanup (SQL kód odstránený)
- [x] Full abstracts (avg 1,419 chars)

### In Progress (0% projektu)
- [ ] *nothing*

### TODO (40% projektu)
- [ ] PyLucene indexer (15%)
- [ ] PyLucene searcher (15%)
- [ ] Evaluácia (5%)
- [ ] run.sh targety (3%)
- [ ] Dokumentácia (2%)

---

## 🎯 NEXT ACTION

**Spusti:**
```bash
# 1. Over PyLucene
python3 -c "import lucene; lucene.initVM(); print('✅ PyLucene OK')"

# 2. Začni s indexerom
# Vytvor: indexer/lucene_indexer.py podľa sekcie "1. PyLucene Indexer" vyššie
```

**Ak PyLucene chýba:**
```bash
# macOS
brew install openjdk@11 ant
# Potom manuálny build pylucene z https://lucene.apache.org/pylucene/
```

---

**KONIEC TODO LISTU**
