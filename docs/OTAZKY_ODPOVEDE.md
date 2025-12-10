# 📝 Otázky a Odpovede o Projekte

**Projekt:** Food Recipes IR Pipeline  
**Autor:** Maroš Bednár  
**Predmet:** VINF - Vyhľadávanie Informácií  
**Dátum:** December 2025

---

## 📋 Obsah

1. [Základné otázky o projekte](#základné-otázky-o-projekte)
2. [Crawling a dáta](#crawling-a-dáta)
3. [Spracovanie textu a parsing](#spracovanie-textu-a-parsing)
4. [Indexovanie](#indexovanie)
5. [Vyhľadávanie a ranking](#vyhľadávanie-a-ranking)
6. [Wikipedia integrácia](#wikipedia-integrácia)
7. [Spark a distribuované spracovanie](#spark-a-distribuované-spracovanie)
8. [Evaluácia](#evaluácia)
9. [Technické detaily](#technické-detaily)

---

## Základné otázky o projekte

### 1. Čo je cieľom projektu?
**Odpoveď:** Cieľom je vytvoriť kompletný Information Retrieval (IR) systém pre vyhľadávanie kulinárskych receptov z webu food.com, obohatených o znalosti z anglickej Wikipédie. Systém umožňuje fulltextové vyhľadávanie s podporou filtrov (čas prípravy, kuchyňa) a poskytuje historický a kultúrny kontext k receptom.

### 2. Aký je zdroj dát?
**Odpoveď:** Projekt používa dva hlavné zdroje dát:
- **food.com** - 5,646 receptov stiahnutých crawlerom
- **Wikipedia** - 9,693 kulinárskych článkov extrahovaných z English Wikipedia dump (20GB)

### 3. Koľko premenných sa extrahuje z každého receptu?
**Odpoveď:** Z food.com sa extrahuje **23 premenných**: id, url, title, description, ingredients, instructions, times (prep/cook/total), cuisine, category, difficulty, yield, serving_size, author, author_bio, author_location, nutrition (9 hodnôt), ratings, image, all_images, keywords, date_published.

### 4. Aká je architektúra systému?
**Odpoveď:** Pipeline pozostáva zo 6 fáz:
1. **Crawler** → stiahnutie HTML súborov z food.com
2. **Parser** → extrakcia štruktúrovaných dát (JSON-LD + Regex)
3. **Wikipedia Spark Parser** → extrakcia kulinárskych článkov
4. **Enricher** → prepojenie receptov s Wikipedia entitami
5. **Indexer** → vytvorenie invertovaného indexu (Simple TSV + Lucene)
6. **Searcher** → vyhľadávanie s BM25/TF-IDF

---

## Crawling a dáta

### 5. Akú stratégiu crawlingu používa projekt?
**Odpoveď:** Projekt používa **BFS (Breadth-First Search)** stratégiu implementovanú cez FIFO queue (deque). Táto stratégia zabezpečuje, že najprv navštívime stránky bližšie k seedu, čo typicky znamená dôležitejšie stránky.

```python
# crawler/frontier.py
self.queues = defaultdict(deque)  # FIFO = BFS
url, depth = queue.popleft()       # Vždy berieme z predku
```

### 6. Ako crawler rešpektuje robots.txt?
**Odpoveď:** Crawler používa Python `robotparser` na parsovanie robots.txt. Pred každým requestom skontroluje, či je URL povolená pre user-agent '*'. Implementácia zahŕňa cache pre robots.txt súbory, aby sa znížil počet requestov.

### 7. Koľko HTML súborov sa stiahlo?
**Odpoveď:** Stiahlo sa **5,646 HTML súborov** z domény www.food.com, čo predstavuje približne **2.2 GB** raw dát.

### 8. Ako sa rieši deduplikácia URL?
**Odpoveď:** Deduplikácia sa rieši pomocou `set()` normalizovaných URL. URL sa normalizuje odstránením trailing slash, query parametrov (okrem relevantných) a fragmentov.

---

## Spracovanie textu a parsing

### 9. Ako parser extrahuje dáta z HTML?
**Odpoveď:** Parser používa kombináciu dvoch prístupov:
1. **JSON-LD parsing** - Food.com používa Schema.org Recipe markup v JSON-LD formáte, čo umožňuje priamu extrakciu štruktúrovaných dát
2. **Regex fallback** - Pre prípad, že JSON-LD chýba, používame regulárne výrazy na extrakciu z HTML

### 10. Aký regex sa používa na extrakciu času prípravy?
**Odpoveď:** Časy sú v ISO 8601 duration formáte (napr. "PT1H30M" = 1 hodina 30 minút):
```python
hours = re.search(r'(\d+)H', duration)
mins = re.search(r'(\d+)M', duration)
total_minutes = (hours * 60 if hours else 0) + (mins if mins else 0)
```

### 11. Ako funguje tokenizácia?
**Odpoveď:** Tokenizácia prebieha v niekoľkých krokoch:
1. Odstránenie HTML tagov: `re.sub(r'<[^>]+>', ' ', text)`
2. Odstránenie HTML entít: `re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)`
3. Extrakcia slov: `re.findall(r'\b[a-zA-Z]+\b', text.lower())`
4. Filtrovanie stop slov a krátkych slov (< 2 znaky)

### 12. Aké stop slová sa odstraňujú?
**Odpoveď:** Odstraňuje sa približne 100 anglických stop slov vrátane: the, a, an, and, or, but, in, on, at, to, for, of, with, by, is, are, was, were, be, been, have, has, had, do, does, did, will, would, could, should, may, might, must, can, this, that, these, those, i, you, he, she, it, we, they...

---

## Indexovanie

### 13. Aké dva typy indexov projekt implementuje?
**Odpoveď:** Projekt implementuje dva typy indexov:
1. **Simple Index** - Čistá Python implementácia uložená v TSV súboroch, bez externých závislostí
2. **Lucene Index** - Profesionálny search engine cez PyLucene/Lupyne wrapper

### 14. Aká je štruktúra Simple indexu?
**Odpoveď:** Simple index pozostáva z troch TSV súborov:
- **terms.tsv** - slovník termov (term → df, idf)
- **postings.tsv** - posting listy (term → field, docId, tf)
- **docmeta.tsv** - metadáta dokumentov (docId → url, title, time, cuisine)
- **field_lengths.json** - dĺžky polí pre BM25

### 15. Koľko termov obsahuje Simple index?
**Odpoveď:** Simple index obsahuje **14,977 unikátnych termov** a **2,506,115 posting záznamov**. Celková veľkosť je približne **54.7 MB**.

### 16. Aké váhy majú jednotlivé polia pri indexovaní?
**Odpoveď:** Polia majú nasledovné váhy:
- **title**: 3.0 (najvyššia váha - titulok je najdôležitejší)
- **ingredients**: 2.0 (ingrediencie sú druhé najdôležitejšie)
- **instructions**: 1.0 (inštrukcie majú základnú váhu)
- **wiki**: 1.5 (Wikipedia entity majú strednú váhu)

---

## Vyhľadávanie a ranking

### 17. Aké ranking algoritmy projekt podporuje?
**Odpoveď:** Projekt podporuje dva ranking algoritmy:
- **BM25** (Okapi BM25) - pravdepodobnostný model s parametrami k1=1.2, b=0.75
- **TF-IDF** - klasický vektorový model s kosínusovou podobnosťou

### 18. Ako funguje BM25?
**Odpoveď:** BM25 vzorec:
```
BM25(t, d) = IDF(t) × (tf × (k1 + 1)) / (tf + k1 × (1 - b + b × |d|/avgdl))
```
Kde:
- **k1 = 1.2** - saturačný parameter pre TF (vyššie TF má klesajúci prínos)
- **b = 0.75** - normalizácia dĺžky dokumentu (dlhšie dokumenty sú penalizované)
- **|d|** - dĺžka dokumentu
- **avgdl** - priemerná dĺžka dokumentov v kolekcii

### 19. Aký je rozdiel medzi BM25 a TF-IDF?
**Odpoveď:** Hlavné rozdiely:
| Aspekt | TF-IDF | BM25 |
|--------|--------|------|
| TF saturácia | Lineárna (log) | Nelineárna (asymptotická) |
| Normalizácia dĺžky | Euklidovská | Probabilistická (b parameter) |
| Výkonnosť | Horšia na dlhých dokumentoch | Lepšia na heterogénnych kolekciách |

### 20. Aké filtre podporuje vyhľadávanie?
**Odpoveď:** Vyhľadávanie podporuje tieto filtre:
- **max_total_minutes** - maximálny čas prípravy (napr. do 30 minút)
- **cuisine** - typ kuchyne (napr. mexican, italian)
- **min_rating** - minimálne hodnotenie (napr. 4.0 hviezdičiek)
- **max_calories** - maximálny počet kalórií

---

## Wikipedia integrácia

### 21. Koľko Wikipedia článkov sa spracovalo?
**Odpoveď:** Z celkového Wikipedia dump (~6 miliónov stránok) sa extrahovalo **9,693 kulinárskych článkov**, čo predstavuje približne 0.16% konverzný pomer.

### 22. Ako sa filtrujú kulinárske články?
**Odpoveď:** Články sa filtrujú na základe:
1. **Infobox patterns**: `{{Infobox food}}`, `{{Infobox prepared food}}`, `{{Infobox ingredient}}`
2. **Kategórie**: články obsahujúce slová "cuisine", "dish", "food", "recipe", "cooking", "ingredient"
3. **Word-boundary matching**: presné zhody slov (nie substring) pre zníženie false positives

### 23. Aké typy entít sa extrahujú z Wikipédie?
**Odpoveď:** Extrahuje sa 6 typov entít:
| Typ | Počet | Podiel |
|-----|-------|--------|
| Jedlá (dish) | 5,285 | 62.5% |
| Ingrediencie | 2,606 | 30.8% |
| Techniky | 172 | 2.0% |
| Korenie/omáčky | 170 | 2.0% |
| Kuchyne | 151 | 1.8% |
| Nástroje | 75 | 0.9% |

### 24. Ako funguje Aho-Corasick entity matching?
**Odpoveď:** Aho-Corasick je algoritmus pre multi-pattern matching s O(n) zložitosťou:
1. **Budovanie automatu**: Vytvorí sa TRIE zo všetkých Wikipedia názvov (surface forms)
2. **Failure linky**: Pridajú sa linky pre efektívne backtracking (ako KMP)
3. **Prechod textu**: Text sa prejde raz a nájdu sa všetky zhody súčasne

### 25. Koľko Wiki linkov má priemerný recept?
**Odpoveď:** Priemerný recept má **24.75 Wiki linkov**. Pokrytie jednotlivých obohatení:
- wiki_links: 100%
- historical_context: 97.9%
- ingredient_origins: 96.5%
- dish_info: 70.1%

---

## Spark a distribuované spracovanie

### 26. Prečo sa používa Spark na spracovanie Wikipédie?
**Odpoveď:** Wikipedia XML dump má **20GB** (komprimovaný). Načítanie celého súboru do pamäte nie je možné na bežnom počítači. Spark umožňuje:
1. Streaming spracovanie bez načítania celého súboru
2. Paralelné spracovanie na viacerých jadrách
3. Efektívne spracovanie veľkých dát

### 27. Ako funguje streaming XML parser?
**Odpoveď:** Parser číta súbor riadok po riadku a bufferuje `<page>...</page>` bloky:
```python
for line in bz2.open(input_path, 'rt'):
    if '<page>' in line:
        buffer = [line]
        in_page = True
    elif in_page:
        buffer.append(line)
        if '</page>' in line:
            yield ''.join(buffer)
            in_page = False
```

### 28. Aká je rýchlosť spracovania?
**Odpoveď:** Na MacBook Pro M4 Pro je rýchlosť približne **2,500 stránok/sekundu**. Celé spracovanie 6 miliónov stránok trvá približne **40-50 minút**.

---

## Evaluácia

### 29. Aké metriky sa používajú na hodnotenie?
**Odpoveď:** Projekt používa štandardné IR metriky:
- **Precision@k** - podiel relevantných dokumentov v top-k výsledkoch
- **Recall@k** - podiel nájdených relevantných dokumentov z celkového počtu
- **F1-score** - harmonický priemer P a R
- **NDCG@k** - meria kvalitu zoradenia (normalized discounted cumulative gain)
- **MAP** - mean average precision

### 30. Aký je priemerný overlap medzi Simple a Lucene indexom?
**Odpoveď:** Priemerný overlap top-10 výsledkov je približne **70%**. Na niektorých dotazoch (napr. "chocolate cake") je overlap až **100%**, na iných (napr. "easy cookies") len **20%**.

### 31. Ktorý index je rýchlejší?
**Odpoveď:** **Simple index je rýchlejší** na jednoduché dotazy:
- Simple BM25: priemerne **2.36 ms**
- Lucene BM25: priemerne **19.61 ms** (kvôli JVM warmup)

Po JVM warmupe je Lucene porovnateľne rýchly.

---

## Technické detaily

### 32. Aké Python knižnice projekt používa?
**Odpoveď:** Hlavné knižnice:
- **requests** - HTTP requesty pre crawler
- **lxml** - HTML parsing
- **pyspark** - distribuované spracovanie
- **pylucene/lupyne** - Lucene wrapper
- **ahocorasick** - multi-pattern matching
- **numpy** - numerické výpočty

### 33. Ako sa spustí vyhľadávanie z príkazového riadku?
**Odpoveď:**
```bash
# Simple index (BM25)
python -m search_cli.run --index index/v1 --metric bm25 --q "chocolate cake" --k 10

# Lucene index (TF-IDF)
python -m search_cli.run --index index/v2_tfidf --metric tfidf --q "pasta carbonara" --k 5

# S filtrami
python -m search_cli.run --index index/v2 --metric bm25 --q "chicken" --k 10 --filter '{"max_total_minutes": 30}'
```

### 34. Aká je štruktúra výstupného JSONL súboru?
**Odpoveď:** Každý riadok obsahuje JSON objekt s receptom:
```json
{
  "id": "12345",
  "url": "https://www.food.com/recipe/...",
  "title": "Chocolate Cake",
  "ingredients": ["flour", "sugar", "cocoa"],
  "instructions": ["Preheat oven...", "Mix dry..."],
  "times": {"prep": 20, "cook": 45, "total": 65},
  "nutrition": {"calories": 350, "protein": 5, ...},
  "wiki_links": [
    {"surface": "chocolate", "wiki_title": "Chocolate", "type": "ingredient"},
    {"surface": "cake", "wiki_title": "Cake", "type": "dish"}
  ]
}
```

### 35. Ako funguje fuzzy vyhľadávanie?
**Odpoveď:** Lucene podporuje fuzzy vyhľadávanie pomocou FuzzyQuery s edit distance:
```python
from org.apache.lucene.search import FuzzyQuery
fuzzy_q = FuzzyQuery(term, maxEdits=2, prefixLength=2)
```
Toto nájde dokumenty aj pri preklepoch, napr. "chickn" → "chicken".

---

## Bonusové otázky

### 36. Prečo sa používa JSON-LD namiesto čistého HTML parsing?
**Odpoveď:** JSON-LD (Schema.org) má niekoľko výhod:
1. Štruktúrované dáta - netreba regex na extrakciu
2. Štandardizovaný formát - rovnaká štruktúra na rôznych weboch
3. Spoľahlivejšie - menej závislé na HTML štruktúre stránky

### 37. Ako sa rieši normalizácia ingrediencií?
**Odpoveď:** Wikipedia redirects slúžia ako synonymický slovník:
- "cilantro" → "Coriander"
- "eggplant" → "Eggplant" (US) = "Aubergine" (UK)
- "garlic clove" → "Garlic"

Aho-Corasick automat obsahuje všetky surface forms vrátane redirectov.

### 38. Aká je presnosť entity linking?
**Odpoveď:** Entity linking má vysokú presnosť vďaka:
1. **Word-boundary matching** - "Swedish" nenájde "dish"
2. **Case-insensitive** - "Garlic" = "garlic" = "GARLIC"
3. **Deduplication** - každá entita sa počíta len raz

### 39. Ako by sa dal systém vylepšiť?
**Odpoveď:** Možné vylepšenia:
1. **Semantic search** - použitie BERT embeddings namiesto keyword matching
2. **Query expansion** - rozšírenie dotazu o synonymá z WordNet
3. **Learning to Rank** - ML model pre personalizované zoradenie
4. **Faceted search** - navigácia podľa atribútov (kuchyňa, čas, kalórie)

### 40. Čo je najväčšia výzva projektu?
**Odpoveď:** Najväčšia výzva bolo **spracovanie 20GB Wikipedia dump** efektívne:
1. Streaming parser (nie načítanie celého súboru)
2. Správne page boundary detection (nerezať stránky uprostred)
3. Filtrovanie kulinárskych článkov s vysokou precision (málo false positives)

---

## 🎯 Zhrnutie pre skúšku

**Kľúčové čísla:**
- 5,646 receptov z food.com
- 9,693 Wikipedia článkov
- 23 premenných na recept
- 14,977 termov v indexe
- 2.5M posting záznamov
- 70% overlap Simple vs Lucene
- 24.75 Wiki linkov na recept

**Kľúčové technológie:**
- BFS crawling, robots.txt
- JSON-LD + Regex parsing
- Invertovaný index (TSV + Lucene)
- BM25 / TF-IDF ranking
- Aho-Corasick entity linking
- PySpark Wikipedia processing

---

*Vytvorené pre VINF projekt - December 2025*
