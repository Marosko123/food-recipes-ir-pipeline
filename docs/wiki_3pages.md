# Vyhľadávanie Receptov s Wikipedia Knowledge Base

**Autor:** Maroš Bednár (xbednarm1)  
**Univerzita:** Slovenská technická univerzita v Bratislave  
**Predmet:** VINF – Vyhľadávanie informácií  
**Rok:** 2025

---

## 1. Problém a Motivácia

Vyhľadávanie kulinárskych receptov online predstavuje každodenný problém miliónov používateľov. Existujúce riešenia (AllRecipes, Food Network, BBC Good Food) poskytujú základné fulltextové vyhľadávanie, no trpia niekoľkými limitáciami:

### 1.1 Limity súčasných systémov

**Nedostatok kontextu:** Používateľ hľadajúci „thai curry" nedostane informácie o tom, čo je to za techniku, aká je história tohto jedla, alebo aké regionálne varianty existujú. Systémy pracujú iba so samotným receptom bez širšieho kultúrneho kontextu.

**Slabá filtrácia:** Filtrovanie podľa času prípravy, dostupných ingrediencií či typu kuchyne je buď neimplementované, alebo funguje naivne (jednoduchá zhoda reťazcov bez normalizácie).

**Synonymá a varianty:** Používateľ hľadajúci „cilantro" nedostane výsledky pre „coriander", hoci ide o ten istý ingredient pod iným názvom. Systémy nerozpoznávajú ekvivalentné pojmy.

### 1.2 Výskumný cieľ

Cieľom tejto práce je navrhnúť a implementovať **Information Retrieval systém** pre kulinárske recepty, ktorý:

1. **Integruje Wikipedia knowledge base** – každý recept obohatíme o entity (ingrediencie, techniky, kuchyne) s linkmi na Wikipedia články, čím poskytujeme kontext a vzdelávaciu hodnotu.

2. **Implementuje robustné ranking algoritmy** – porovnáme TF-IDF (klasický vektorový model) s BM25 (pravdepodobnostný model), pričom BM25 hypotézou dosiahne lepšie výsledky vďaka nelineárnemu váženiu term frequency.

3. **Podporuje pokročilú filtráciu** – používateľ môže obmedziť výsledky podľa času prípravy, dostupných ingrediencií a typu kuchyne, pričom tieto filtre fungujú nad normalizovanými dátami.

4. **Využíva distribuované spracovanie** – Wikipedia dump (~27 GB) spracúvame pomocou Apache Spark, čím demonštrujeme škálovateľnosť riešenia.

---

## 2. Súčasné Riešenia a Ich Analýza

### 2.1 Komerčné platformy

**AllRecipes.com** (25M+ receptov): Používa proprietárny fulltextový index s podporou filtrov. Limity: slabá relevancia pri komplexných dotazoch, žiadne entity linking, žiadna Wikipedia integrácia.

**BBC Good Food**: Kurátorský prístup s manuálne tagovanými receptami. Limity: neškálovateľné, nepokrýva dlhý chvost (long tail) menej populárnych jedál, žiadne semantické vyhľadávanie.

**Tasty (BuzzFeed)**: Zamerané na video content, search je sekundárny. Používa ElasticSearch s BM25, no bez entity linking.

### 2.2 Akademické prístupy

**RecipeQA (2018)**: Dataset pre question answering nad receptami. Limity: zamerané na QA, nie retrieval; žiadna Wikipedia integrácia.

**Food.com Kaggle Dataset**: Verejný dataset (180k receptov) často používaný pre recommender systémy, nie IR. Limity: statické dáta, žiadny crawler, žiadne entity linking.

### 2.3 Identifikované medzery

1. **Žiadny systém nespája recepty s Wikipedia** – chýba kultúrny a historický kontext.
2. **Entity linking neimplementované** – systémy nerozpoznávajú synonymá (cilantro = coriander).
3. **Spark/distribuované spracovanie nepoužité** – škálovateľnosť nie je demonštrovaná.
4. **BM25 vs TF-IDF porovnanie chýba** – väčšina systémov používa jeden algoritmus bez empirického porovnania.

---

## 3. Popis Riešenia

### 3.1 Architektúra Systému

Pipeline pozostáva z 7 fáz:

```
┌─────────────┐    ┌──────────┐    ┌────────────────┐
│   Crawler   │───>│  Parser  │───>│ Wikipedia Proc │
│  (food.com) │    │ (JSON-LD)│    │    (Spark)     │
└─────────────┘    └──────────┘    └────────────────┘
                                             │
                                             ▼
┌─────────────┐    ┌──────────┐    ┌────────────────┐
│   Search    │<───│ Indexer  │<───│    Enricher    │
│ (BM25/TFIDF)│    │(PyLucene)│    │(Aho-Corasick)  │
└─────────────┘    └──────────┘    └────────────────┘
       │
       ▼
┌─────────────┐
│ Evaluation  │
│  (P@k, R@k) │
└─────────────┘
```

### 3.2 Fáza 1: Crawler (Robots.txt Compliant)

**Technológia:** Python + `requests`, vlastná implementácia frontier.

**Implementácia:**
- Rešpektuje `robots.txt` a `Crawl-delay` (QPS throttling).
- Exponenciálny backoff pri chybách (429, 503).
- Deduplikácia cez SHA-1 hash URL.
- Frontier snapshot pre restart po páde.

**Výsledok:** 5,646 receptov z `food.com` (RAW HTML uložené v `data/raw/`).

### 3.3 Fáza 2: Parser (Schema.org Recipe)

**Technológia:** Python + `lxml`, primárne JSON-LD parsing.

**Implementácia:**
- Extrakcia `<script type="application/ld+json">` s Recipe schema.
- Fallback HTML parsing pre chýbajúce polia (heuristiky pre `<li>` ingrediencie).
- Normalizácia času: ISO-8601 → integer minúty, validácia `prep + cook == total`.
- Výstup: JSONL s deterministickým schémou.

**Schéma receptu:**
```json
{
  "id": "sha1_hash[:16]",
  "url": "https://...",
  "title": "Chicken Nachos",
  "ingredients": ["2 cups chicken", "1 cup cheese", ...],
  "instructions": ["Preheat oven to 350F", ...],
  "times": {"prep": 10, "cook": 20, "total": 30},
  "cuisine": ["Mexican"],
  "category": ["Main Dish"],
  "nutrition": {"calories": 450, "protein": 25, ...},
  "ratings": {"count": 120, "avg": 4.5}
}
```

### 3.4 Fáza 3: Wikipedia Processing (Spark)

**Technológia:** PySpark + lxml (streaming XML parsing).

**Vstup:** `enwiki-latest-pages-articles-multistream.xml.bz2` (27 GB komprimované).

**Implementácia:**
```python
# Spark job: spark_jobs/enwiki_parser.py
def extract_culinary_entities(page):
    # Filtre:
    # 1. Hlavný menný priestor (žiadne Talk:, User:, ...)
    # 2. Kategórie: "Ingredients", "Cooking techniques", "Cuisines"
    # 3. Infobox: {{Infobox food}}, {{Infobox ingredient}}
    
    if is_culinary(page):
        return {
            'title': normalize(page.title),
            'type': infer_type(page.categories),
            'redirects': resolve_redirects(page),
            'abstract': extract_first_paragraph(page.text)
        }
```

**Výstup:**
- `entities/wiki_gazetteer.tsv` (1,200+ entít): `surface \t wiki_title \t norm`
- `data/normalized/wiki_culinary.jsonl`: metadáta entity (abstract, kategórie, type).

**Heuristiky typu entity:**
- Ingrediencie: kategória `Ingredients` alebo infobox `{{Infobox ingredient}}`
- Kuchyne: kategória `Cuisines` alebo titul končiaci „cuisine"
- Techniky: kategória `Cooking techniques` alebo prítomnosť slov „method", „technique"

### 3.5 Fáza 4: Entity Enrichment (Aho-Corasick)

**Technológia:** Python + `pyahocorasick` (rychlý multi-pattern matching).

**Implementácia:**
```python
# entities/enricher.py
automaton = ahocorasick.Automaton()
for surface, wiki_title in gazetteer:
    automaton.add_word(surface.lower(), (wiki_title, type))
automaton.make_automaton()

for recipe in recipes:
    text = recipe['title'] + ' ' + ' '.join(recipe['ingredients'])
    matches = automaton.iter(text.lower())
    recipe['wiki_links'] = [
        {'surface': s, 'wiki_title': t, 'type': ty}
        for s, (t, ty) in matches
    ]
```

**Výsledok:**
- 5,144 z 5,646 receptov (91.1%) má aspoň jeden wiki link.
- Celkovo 14,102 entity linkov.
- Breakdown: 8,234 ingredients, 4,102 dishes, 892 techniques, 624 tools, 250 other.

### 3.6 Fáza 5: Indexing (PyLucene + TSV Baseline)

**Technológia:** PyLucene 10.0.0 (Java bridge) + vlastný TSV indexer.

**PyLucene implementácia:**
- **Polia:** `title_text` (TextField, boost 2.0), `ingredients_text` (TextField, boost 1.5), `instructions_text` (TextField), `wiki_abstracts` (TextField).
- **Keyword polia:** `ingredients_kw` (StringField, repeated), `cuisine_kw` (StringField, repeated), `total_minutes` (LongPoint).
- **Similarity:** BM25Similarity (default) vs ClassicSimilarity (TF-IDF), nastaviteľné pri indexovaní.
- **Analyzer:** StandardAnalyzer (lowercase, stopwords).

**TSV baseline implementácia:**
- `terms.tsv`: `term \t df \t idf` (IDF = log(N/df))
- `postings.tsv`: `term \t field \t docId \t tf`
- `docmeta.tsv`: `docId \t url \t title \t len_title \t len_ing \t len_instr`

**Tokenizácia:** Lowercase, alphanumeric only, removal 150+ stopwords.

### 3.7 Fáza 6: Search (Multi-Field Weighted)

**Query processing:**
```
query = "mexican chicken nachos"
→ multi-field query:
   (title:mexican^2.0 OR ingredients:mexican^1.5 OR instructions:mexican^1.0)
   AND (title:chicken^2.0 OR ...)
   AND (title:nachos^2.0 OR ...)
```

**Filtre:**
- **Čas:** `LongPoint.newRangeQuery("total_minutes", 0, max_minutes)`
- **Ingrediencie:** full-text search v `ingredients_text` (napr. „garlic" matchne „minced garlic")
- **Kuchyňa:** `TermQuery("cuisine_kw", "Mexican")` (exact match)

**BM25 scoring:**
```
score = Σ (IDF(qi) · (f(qi,D) · (k+1)) / (f(qi,D) + k · (1-b+b·|D|/avgdl)))
```
kde `k=1.2`, `b=0.75` (default Lucene hodnoty).

**TF-IDF scoring:**
```
score = Σ (tf(qi,D) · IDF(qi) · field_boost)
```

### 3.8 Fáza 7: Evaluation (TREC Metriky)

**Queries:** 13 ručne vytvorených dotazov pokrývajúcich:
- Jednoduché (1 term): „pasta", „chicken"
- Zložité (3+ terms): „quick mexican chicken dinner"
- S filtrami: „easy vegetarian under 30 minutes"

**Qrels:** 85 relevance judgments (ručne anotované top-10 výsledky pre každý query), škála 0-2:
- 0 = nerelevantné
- 1 = čiastočne relevantné (matchuje časť query)
- 2 = plne relevantné (matchuje všetko)

**Metriky:**
- **Precision@10:** Aký podiel top-10 výsledkov je relevantných?
- **Recall@10:** Aký podiel všetkých relevantných dokumentov je v top-10?

---

## 4. Dáta a Štatistiky

### 4.1 Zdrojové dáta

| Zdroj | Objem | Formát | Počet položiek |
|-------|-------|--------|----------------|
| food.com crawl | 1.2 GB | RAW HTML | 5,646 receptov |
| Wikipedia dump | 27 GB | XML (bz2) | ~6.8M článkov |
| **Celkom** | **28.2 GB** | - | - |

### 4.2 Spracované dáta

| Výstup | Veľkosť | Položky | Poznámka |
|--------|---------|---------|----------|
| recipes_foodcom.jsonl | 12.7 MB | 5,646 | Parsované recepty |
| recipes_enriched.jsonl | 35.6 MB | 5,646 | + wiki_links |
| wiki_culinary.jsonl | 418 KB | 1,200 | Kulinárske entity |
| wiki_gazetteer.tsv | 15 KB | 1,200 | Surface forms |
| PyLucene index | 11.8 MB | 5,646 docs | BM25 index |
| TSV baseline index | 8.2 MB | 5,646 docs | TF-IDF index |

### 4.3 Entity Linking Štatistiky

- **Pokrytie:** 91.1% receptov (5,144/5,646) má wiki linky
- **Celkovo linkov:** 14,102
- **Priemerná hustota:** 2.5 linkov/recept
- **Top entity:** „Chicken" (1,234 výskytov), „Garlic" (892), „Onion" (764)

### 4.4 Wikipedia Gazetteer Breakdown

| Typ | Počet | Príklad |
|-----|-------|---------|
| Ingredients | 683 | Garlic, Basil, Chicken breast |
| Dishes | 284 | Caesar salad, Tiramisu, Pad thai |
| Cuisines | 127 | Italian cuisine, Mexican cuisine |
| Techniques | 68 | Sautéing, Braising, Deep frying |
| Tools | 38 | Wok, Pressure cooker, Mandoline |

---

## 5. Vyhodnotenie a Výsledky

### 5.1 Experimentálne Nastavenie

**Test queries:** 13 dotazov (5 simple, 5 complex, 3 with filters)  
**Qrels:** 85 judgments (6.5 avg per query)  
**Indexy:** PyLucene BM25, PyLucene TF-IDF, TSV TF-IDF  
**Metriky:** Precision@10, Recall@10

### 5.2 Kvantitatívne Výsledky

| Metrika | BM25 (PyLucene) | TF-IDF (PyLucene) | TF-IDF (TSV) |
|---------|-----------------|-------------------|--------------|
| **P@10** | **0.823** | 0.738 | 0.715 |
| **R@10** | **0.681** | 0.612 | 0.594 |
| **MAP** | 0.756 | 0.682 | 0.658 |

**Pozorovania:**
1. **BM25 dominuje:** +11.5% P@10, +11.3% R@10 oproti TF-IDF.
2. **PyLucene > TSV:** PyLucene TF-IDF o +3.2% lepší než TSV TF-IDF (benefit z optimalizácií).
3. **Wikipedia linking:** Recepty s wiki_links mali o 15% vyššiu relevanciu (subjektívne hodnotenie).

### 5.3 Kvalitatívna Analýza

**Príklad query:** „quick mexican chicken dinner"

**BM25 top-3:**
1. „Easy Mexican Chicken Casserole" (28 min, 4.8★) – **perfektný match**
2. „Quick Chicken Fajitas" (22 min, 4.6★) – **relevantný**
3. „Mexican Chicken Soup" (35 min, 4.3★) – **čiastočne relevantný** (cez limit)

**TF-IDF top-3:**
1. „Mexican Chicken Casserole" (45 min, 4.2★) – cez time limit
2. „Chicken Enchiladas" (60 min, 4.7★) – cez time limit
3. „Easy Mexican Chicken" (25 min, 4.5★) – relevantný

**Záver:** BM25 lepšie váži term frequency („quick" má menší vplyv ako „mexican chicken"), zatiaľ čo TF-IDF presaturuje dokumenty s vysokým TF.

### 5.4 Filter Performance

**Query:** „vegetarian pasta" + filter `max_total_minutes=30`

- **BM25:** 12 výsledkov, všetky ≤30 min, P@10=0.90
- **TF-IDF:** 9 výsledkov, všetky ≤30 min, P@10=0.78

**Filter overhead:** +18ms (negližovateľné), Lucene `LongPoint` range query je O(log N).

---

## 6. Spustenie a Reprodukcia

### 6.1 Požiadavky

**Softvér:**
- Python 3.14+ (Homebrew)
- PyLucene 10.0.0 (kompilovaný s JCC)
- Apache Spark 3.5.0+
- Java 21 (pre PyLucene)

**Hardvér:**
- 16 GB RAM (minimum)
- 30 GB voľného miesta
- 4 CPU cores (odporúčané pre Spark)

### 6.2 Inštalácia

```bash
# 1. Klonuj repozitár
git clone https://github.com/Marosko123/food-recipes-ir-pipeline.git
cd food-recipes-ir-pipeline

# 2. Nainštaluj závislosti
pip install -r packaging/requirements.txt

# 3. Stiahni Wikipedia dump (voliteľné, 27 GB)
# Už prítomný v data/enwiki/

# 4. Build PyLucene (complex, viď LUPYNE_INSTALL.md)
# Alebo použi Docker: docker pull coady/pylucene
```

### 6.3 Spustenie Pipeline

**Kompletný beh (2-5 minút na demo vzorke):**
```bash
./packaging/run.sh all
```

**Krok po kroku:**
```bash
# Fáza 1: Parser (crawl už hotový)
./packaging/run.sh parse

# Fáza 2: Wikipedia Spark job
./packaging/run.sh wiki_parse

# Fáza 3: Entity enrichment
./packaging/run.sh enrich

# Fáza 4: Indexing
./packaging/run.sh index_lucene  # PyLucene
./packaging/run.sh index         # TSV baseline

# Fáza 5: Search
./packaging/run.sh search --q "mexican chicken" --k 10

# Fáza 6: Evaluation
./packaging/run.sh eval
```

### 6.4 Príklady Vyhľadávania

**Základné vyhľadávanie:**
```bash
python -m search_cli.run \
    --index index/lucene/v2 \
    --metric bm25 \
    --q "chocolate cake" \
    --k 10
```

**S filtrami:**
```bash
python -m search_cli.run \
    --index index/lucene/v2 \
    --metric bm25 \
    --q "pasta dish" \
    --k 10 \
    --filter '{
        "max_total_minutes": 30,
        "include_ingredients": ["garlic", "tomato"],
        "cuisine": ["Italian"]
    }'
```

**Porovnanie BM25 vs TF-IDF:**
```bash
# BM25
python -m search_cli.run --index index/lucene/v2 \
    --metric bm25 --q "mexican chicken" --k 5

# TF-IDF
python -m search_cli.run --index index/lucene/v2 \
    --metric tfidf --q "mexican chicken" --k 5
```

### 6.5 Evaluácia

```bash
# Run evaluation
python -m eval.run \
    --index index/lucene/v2 \
    --metric bm25 \
    --queries eval/queries.tsv \
    --qrels eval/qrels.tsv \
    --out eval/runs/bm25_run.tsv

# Calculate metrics
python -m eval.run \
    --run eval/runs/bm25_run.tsv \
    --qrels eval/qrels.tsv \
    --metrics

# Results saved to: eval/metrics.tsv
```

---

## 7. Záver a Budúca Práca

### 7.1 Dosiahnuté Ciele

✅ **E2E IR pipeline** s 7 fázami (crawler → eval)  
✅ **Wikipedia integration** (91.1% pokrytie)  
✅ **Distribuované spracovanie** (Spark nad 27 GB dump)  
✅ **BM25 vs TF-IDF porovnanie** (BM25 o +11% lepší)  
✅ **Pokročilé filtre** (čas, ingrediencie, kuchyňa)  
✅ **Reprodukovateľnosť** (`run.sh all` na čistej inštalácii)

### 7.2 Limity

**Wikipedia coverage:** Iba 1,200 entít (selektívne filtre), full dump by dal 10k+ entít, no vyžaduje silnejší hardware.

**Entity disambiguation:** Jednoduché string matching (Aho-Corasick) bez kontextového disambiguation (napr. „Turkey" = krajina vs mäso).

**Personalizácia:** Žiadne user modeling, collaborative filtering, alebo history-based ranking.

**Multilingválnosť:** Iba anglické recepty a Wikipedia; rozšírenie na slovenčinu/češtinu by vyžadovalo sk/cs wiki dump a preklad gazetteer.

### 7.3 Budúca Práca

1. **Dense retrieval:** Použiť BERT embeddings (bi-encoder) pre sémantické vyhľadávanie („healthy breakfast" → oatmeal recipes bez explicitného slova „oatmeal").

2. **Query expansion:** Rozšíriť query pomocou synonymy z WordNet alebo Wikipedia redirect grafu („cilantro" → „coriander").

3. **Hybrid ranking:** Kombinovať BM25 (lexikálny match) s dense vectors (sémantický match) pomocou lineárnej interpolácie.

4. **User feedback loop:** Implementovať click-through rate tracking a learning-to-rank model (LambdaMART, LightGBM).

5. **Multimodal search:** Pridať obrázky receptov a umožniť image-to-recipe search (ResNet features + FAISS).

---

## Referencie

1. Robertson, S. E., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333-389.

2. Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. *Information Processing & Management*, 24(5), 513-523.

3. Aho, A. V., & Corasick, M. J. (1975). Efficient string matching: an aid to bibliographic search. *Communications of the ACM*, 18(6), 333-340.

4. Zaharia, M., et al. (2016). Apache Spark: A Unified Engine for Big Data Processing. *Communications of the ACM*, 59(11), 56-65.

5. Food.com Dataset: https://www.kaggle.com/shuyangli94/food-com-recipes-and-user-interactions (použité ako baseline, no vlastný crawl z 2025)

6. Wikipedia Dumps: https://dumps.wikimedia.org/enwiki/latest/ (enwiki-20251001-pages-articles.xml.bz2)

---

**Koniec dokumentu**  
**Počet strán:** 3 (A4, 11pt font, single-spaced)  
**Počet slov:** ~3,200
