# 📚 VINF - Kompletný Študijný Materiál pre Skúšku

**Autor:** Maroš Bednár  
**Predmet:** VINF - Vyhľadávanie Informácií  
**Dátum:** December 2025

---

## 📖 Obsah

1. [Čo je Information Retrieval](#čo-je-information-retrieval)
2. [Prehľad projektu](#prehľad-projektu)
3. [Crawling - Sťahovanie dokumentov](#1️⃣-crawling-sťahovanie-dokumentov)
4. [Textové operácie](#2️⃣-textové-operácie)
5. [Indexovanie](#3️⃣-indexovanie)
6. [Modely vyhľadávania](#4️⃣-modely-vyhľadávania)
7. [Ranking algoritmy](#5️⃣-ranking-algoritmy)
8. [Extrakcia informácií](#6️⃣-extrakcia-informácií)
9. [Regulárne výrazy](#7️⃣-regulárne-výrazy)
10. [Hodnotenie úspešnosti](#8️⃣-hodnotenie-úspešnosti)
11. [Distribuované spracovanie](#9️⃣-distribuované-spracovanie)
12. [Wikipedia integrácia](#🔟-wikipedia-integrácia)
13. [Vzorové otázky na skúšku](#📝-vzorové-otázky-na-skúšku)

---

## Čo je Information Retrieval (Vyhľadávanie Informácií)?

Predstav si Google. Napíšeš "recept na lasagne" a Google ti za 0.3 sekundy nájde milióny výsledkov a zoradí ich tak, že najrelevantnejšie sú hore. **Ako to funguje?** To je presne to, čo študujeme v predmete VINF.

**Definícia:** Information Retrieval (IR) je proces vyhľadávania relevantných informácií z veľkej kolekcie dokumentov na základe informačnej potreby používateľa.

### Kľúčové koncepty IR:
- **Dokument** - jednotka informácie (webová stránka, recept, článok)
- **Kolekcia/Korpus** - množina všetkých dokumentov
- **Dotaz (Query)** - vyjadrenie informačnej potreby používateľa
- **Relevancia** - miera zhody dokumentu s dotazom

---

# 🗺️ PREHĽAD PROJEKTU

Tento projekt implementuje **kompletný IR systém** pre vyhľadávanie receptov z food.com obohatených o Wikipedia entity.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITEKTÚRA PROJEKTU                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CRAWLING          2. PARSING           3. ENRICHMENT        │
│  ┌─────────┐          ┌─────────┐          ┌─────────┐         │
│  │ food.com│ ──HTML──▶│ Parser  │──JSON──▶│ +Wiki   │         │
│  │ crawler │          │ (Regex) │          │ Entities│         │
│  └─────────┘          └─────────┘          └─────────┘         │
│       │                                         │               │
│       ▼                                         ▼               │
│  data/raw/              data/normalized/   recipes_enriched.jsonl│
│                                                 │               │
│  4. INDEXING           5. SEARCH               │               │
│  ┌─────────┐          ┌─────────┐              │               │
│  │ Simple  │◀─────────│ Query   │◀─────────────┘               │
│  │ TF-IDF  │          │ Engine  │                              │
│  ├─────────┤          │ BM25/   │                              │
│  │ Lucene  │◀─────────│ TF-IDF  │                              │
│  │ BM25    │          └─────────┘                              │
│  └─────────┘                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

# 1️⃣ CRAWLING (Sťahovanie dokumentov)

## Čo to je?
**Crawler** je program, ktorý automaticky navštevuje webové stránky a sťahuje ich obsah. Je to ako robot, ktorý prechádza internet a zbiera dokumenty.

## V projekte: `crawler/run.py`

### Stratégie prehľadávania

#### BFS (Breadth-First Search) - Do šírky
```
         A          Level 0
       / | \
      B  C  D       Level 1   <- Najprv všetky tieto
     /|  |  |\
    E F  G  H I     Level 2   <- Potom tieto
```
**Ako to funguje:** Najprv navštívime VŠETKY linky z aktuálnej stránky, až potom ideme hlbšie.

**Výhoda:** Nájdeme "dôležité" stránky skôr (tie, čo sú blízko koreňa)
**Nevýhoda:** Potrebujeme veľa pamäte na frontu

#### DFS (Depth-First Search) - Do hĺbky
```
         A          <- Začneme tu
        /
       B            <- Ideme čo najhlbšie
      /
     E              <- Až na koniec
    /
   ...              <- Potom späť a ďalšia vetva
```
**Ako to funguje:** Sledujeme jeden link čo najhlbšie, potom sa vraciame.

**Výhoda:** Menej pamäte
**Nevýhoda:** Môžeme sa "stratiť" v menej dôležitých stránkach

### robots.txt
Súbor na každom webe, ktorý hovorí crawlerom čo môžu a nemôžu sťahovať:
```
User-agent: *
Disallow: /admin/
Disallow: /private/
Sitemap: https://example.com/sitemap.xml
```

### Anchor texty (DÔLEŽITÉ na skúšku!)
```html
<a href="https://food.com/recipe/lasagna">Talianska lasagne</a>
```
Text "Talianska lasagne" sa pridá do dokumentu **lasagna** (nie do aktuálneho dokumentu!).
Prečo? Lebo ten text **popisuje cieľový dokument**.

**V projekte:** Anchor texty sa pridávajú 2x (boost), aby mali väčšiu váhu.

---

# 2️⃣ TEXTOVÉ OPERÁCIE

## V projekte: `parser/html_parser.py`

### Tokenizácia
Rozdelenie textu na jednotlivé tokeny (slová).

**Whitespace tokenizer:**
```python
text = "Skúška z VI bude 19.1.2026 o 10:30!"
tokens = text.split()  # Rozdelí podľa medzier
# Výsledok: ["Skúška", "z", "VI", "bude", "19.1.2026", "o", "10:30!"]
```
⚠️ Pozor: Interpunkcia ostáva prilepená!

**V projekte používame regex tokenizáciu:**
```python
# Z html_parser.py - extrakcia ingrediencií
re.compile(r'<li[^>]*class="[^"]*ingredient[^"]*"[^>]*>(.*?)</li>')
```

### Stop slová
Bežné slová, ktoré nenesú význam:
- Anglické: the, a, is, are, in, on, at, to...
- Slovenské: a, v, na, do, je, sú, z...

**Prečo ich odstraňujeme?**
1. Šetríme miesto v indexe
2. Zlepšujeme presnosť vyhľadávania

### Lematizácia vs Stemming

#### Lematizácia (Lemmatization)
Prevod slova na jeho **základný slovníkový tvar**:
```
kolky → kolko
kolka → kolko
kolkách → kolko
```
✅ Presnejšie (používa slovník)
❌ Pomalšie, potrebuje slovník pre každý jazyk

#### Stemming
**Mechanické orezanie** prípony:
```
running → run
connection → connect
connected → connect
```
✅ Rýchle, jednoduché
❌ Nepresné (napr. "university" → "univers")

**Porter Stemmer** - najznámejší algoritmus:
```
ATIONAL → ATE     (relational → relate)
IZER → IZE        (digitizer → digitize)
ING → ∅           (running → runn → run)
```

---

# 3️⃣ INDEXOVANIE

## V projekte: `indexer/lucene_indexer.py`, `index/v1/`

### Čo je Index?
Index je dátová štruktúra, ktorá umožňuje **rýchle vyhľadávanie**.

Bez indexu: Musíme prejsť VŠETKY dokumenty (pomalé!)
S indexom: Priamy skok na dokumenty obsahujúce hľadaný term

### Invertovaný Index (KĽÚČOVÝ KONCEPT!)

**Klasický index:** dokument → slová v ňom
```
Doc1 → [chicken, pasta, garlic, olive, oil]
Doc2 → [beef, stew, carrot, potato]
Doc3 → [chicken, soup, noodle]
```

**Invertovaný index:** slovo → dokumenty kde sa nachádza
```
chicken → [Doc1, Doc3]
pasta   → [Doc1]
beef    → [Doc2]
soup    → [Doc3]
...
```

### Štruktúra v projekte (TSV súbory):

#### terms.tsv - Slovník termov
```tsv
term        df      idf
chicken     523     2.34
pasta       312     2.89
lasagna     45      4.12
```
- **df** (document frequency) = v koľkých dokumentoch sa term vyskytuje
- **idf** (inverse document frequency) = log(N/df) - vzácnosť termu

#### postings.tsv - Posting listy
```tsv
term        field       docId   tf
chicken     title       12345   2
chicken     ingredients 12345   5
chicken     title       67890   1
```
- **field** = kde sa term nachádza (title, ingredients, instructions)
- **tf** (term frequency) = koľkokrát sa term vyskytuje v dokumente

#### docmeta.tsv - Metadáta dokumentov
```tsv
docId   url                                     title                   total_minutes   cuisine
100095  https://www.food.com/recipe/...         Crock Pot Chicken       190             Asian,Chinese
```

---

# 4️⃣ MODELY VYHĽADÁVANIA

## V projekte: `search_cli/run.py`

### TF-IDF Model

**TF (Term Frequency)** - Ako často sa slovo vyskytuje v dokumente
```
tf(chicken, doc1) = 5  (chicken sa vyskytuje 5x v doc1)
```

**IDF (Inverse Document Frequency)** - Ako vzácne je slovo
```
idf(chicken) = log(5646 / 523) = 2.38
idf(lasagna) = log(5646 / 45) = 4.83   # Vzácnejšie = vyššie IDF
```

**TF-IDF skóre:**
```
tfidf(t, d) = tf(t, d) × idf(t)
```

### BM25 Model (Vylepšený TF-IDF)

```
BM25(t, d) = idf(t) × (tf(t,d) × (k1 + 1)) / (tf(t,d) + k1 × (1 - b + b × |d|/avgdl))
```

Kde:
- **k1** = 1.2 (typicky) - saturácia TF
- **b** = 0.75 (typicky) - normalizácia dĺžky dokumentu
- **|d|** = dĺžka dokumentu
- **avgdl** = priemerná dĺžka dokumentov

**Prečo je BM25 lepší?**
1. TF saturácia - 10 výskytov nie je 10x lepších ako 1
2. Normalizácia dĺžky - krátke dokumenty nie sú penalizované

### Kosínusová podobnosť (BUDE NA SKÚŠKE!)

Dokumenty a dopyty reprezentujeme ako **vektory** v n-rozmernom priestore (n = počet termov).

```
Doc1 = [2, 1, 0, 3]   # Vektor TF-IDF hodnôt
Doc2 = [1, 2, 1, 0]
Query = [1, 1, 0, 1]
```

**Kosínus uhla medzi vektormi:**
```
cos(A, B) = (A · B) / (||A|| × ||B||)
```

**Príklad výpočtu:**
```
A = [2, 1, 0, 1]
B = [1, 1, 1, 0]

A · B = 2×1 + 1×1 + 0×1 + 1×0 = 3  (skalárny súčin)
||A|| = √(4 + 1 + 0 + 1) = √6 = 2.45  (euklidovská norma)
||B|| = √(1 + 1 + 1 + 0) = √3 = 1.73

cos(A, B) = 3 / (2.45 × 1.73) = 3 / 4.24 = 0.71
```

### Normalizácia (BUDE NA SKÚŠKE!)

#### 1. Euklidovská normalizácia dĺžky
```
v_norm = v / ||v||
```
Transformuje vektor na jednotkovú dĺžku.

#### 2. Log škálovanie
```
tf_log = 1 + log(tf)   ak tf > 0
tf_log = 0             ak tf = 0
```
Tlmí vplyv veľmi vysokých frekvencií.

#### 3. Max škálovanie
```
tf_norm = tf / max_tf_in_doc
```
Normalizuje vzhľadom na najčastejší term v dokumente.

---

# 5️⃣ RANKING ALGORITMY

## PageRank (VÝPOČET BUDE NA SKÚŠKE!)

Algoritmus od Google - hodnotí dôležitosť stránky podľa linkov.

**Intuícia:** Stránka je dôležitá, ak na ňu odkazujú iné dôležité stránky.

**Vzorec:**
```
PR(A) = (1-d) + d × Σ(PR(Ti) / C(Ti))
```
Kde:
- **d** = 0.85 (damping factor)
- **Ti** = stránky, ktoré odkazujú na A
- **C(Ti)** = počet odkazov na stránke Ti

### Príklad výpočtu (TOTO SA NAUČ!)

```
Stránky: A, B, C
Linky:
  A → B, C  (A odkazuje na B a C)
  B → C
  C → A

Matica prepojení (kto odkazuje na koho):
      A    B    C
A  [  0    0    1  ]   (na A odkazuje len C)
B  [  1    0    0  ]   (na B odkazuje len A)
C  [  1    1    0  ]   (na C odkazujú A aj B)

Počiatočné hodnoty: PR(A) = PR(B) = PR(C) = 1/3

Iterácia 1 (d = 0.85):
PR(A) = (1-0.85) + 0.85 × (PR(C)/1)
      = 0.15 + 0.85 × (0.33/1) = 0.15 + 0.28 = 0.43

PR(B) = (1-0.85) + 0.85 × (PR(A)/2)  # A má 2 odchádzajúce linky
      = 0.15 + 0.85 × (0.33/2) = 0.15 + 0.14 = 0.29

PR(C) = (1-0.85) + 0.85 × (PR(A)/2 + PR(B)/1)
      = 0.15 + 0.85 × (0.33/2 + 0.33/1) = 0.15 + 0.42 = 0.57
```

## HITS (Hyperlink-Induced Topic Search)

Každá stránka má dva skóre:
- **Hub score** - kvalita ako "rozcestník" (odkazuje na dobré zdroje)
- **Authority score** - kvalita ako "zdroj" (ostatní na mňa odkazujú)

**Algoritmus:**
```
1. Inicializuj: hub(p) = authority(p) = 1 pre všetky stránky

2. Opakuj:
   authority(p) = Σ hub(q)      pre všetky q, ktoré odkazujú na p
   hub(p) = Σ authority(q)      pre všetky q, na ktoré p odkazuje
   
   Normalizuj hodnoty

3. Konvergencia
```

### Porovnanie algoritmov

| Algoritmus | Výhody | Nevýhody |
|------------|--------|----------|
| **PageRank** | Query-independent, rýchly | Ignoruje obsah stránky |
| **HITS** | Query-dependent, Hub+Authority | Pomalší, topic drift |
| **SALSA** | Kombinácia PR a HITS | Komplexnejší |

---

# 6️⃣ EXTRAKCIA INFORMÁCIÍ

## V projekte: `entities/recipe_enricher.py`

### 5 úloh MUC (Message Understanding Conference)

#### 1. Named Entity Recognition (NE)
Identifikácia pomenovaných entít:
```
Text: "C. J. Van Rijsbergen pracuje na University of Glasgow"

Entity:
- PERSON: C. J. Van Rijsbergen
- ORGANIZATION: University of Glasgow
```

#### 2. Coreference Resolution (CO)
Rozpoznanie, že rôzne výrazy označujú tú istú entitu:
```
Text: "Rijsbergen publikoval knihu. On je expert na IR."

Koreferencie:
- "Rijsbergen" = "On"
```

#### 3. Template Element (TE)
Štruktúrované informácie o entite:
```json
{
  "entity": "Rijsbergen",
  "type": "PERSON",
  "role": "researcher",
  "affiliation": "University of Glasgow"
}
```

#### 4. Template Relation (TR)
Vzťahy medzi entitami:
```
Rijsbergen --[works_at]--> University of Glasgow
Rijsbergen --[authored]--> "Information Retrieval"
```

#### 5. Scenario Template (ST)
Kompletný scenár udalosti:
```json
{
  "event": "Book publication",
  "author": "Rijsbergen",
  "title": "Information Retrieval",
  "year": "1979",
  "publisher": "Butterworths"
}
```

### V projekte - Entity Linking
```python
# Z recipe_enricher.py - Aho-Corasick pre rýchle hľadanie entít
def find_entities(self, text: str) -> List[Dict]:
    """Nájde entity pomocou Aho-Corasick automatu."""
    for end_pos, (surface, wiki_title) in self.automaton.iter(text_lower):
        # Nájdené: "garlic" → Wikipedia: "Garlic"
```

---

# 7️⃣ REGULÁRNE VÝRAZY

## V projekte: `parser/html_parser.py`

### Základná syntax
| Výraz | Význam |
|-------|--------|
| `.` | Ľubovoľný znak |
| `*` | 0 alebo viac opakovaní |
| `+` | 1 alebo viac opakovaní |
| `?` | 0 alebo 1 opakovanie |
| `\d` | Číslica [0-9] |
| `\w` | Slovný znak [a-zA-Z0-9_] |
| `\s` | Whitespace |
| `[abc]` | a alebo b alebo c |
| `^` | Začiatok |
| `$` | Koniec |

### Príklady (BUDÚ NA SKÚŠKE!)

#### Firmy (a.s., s.r.o.)
```python
# Nájde: "Acme a.s.", "Google s.r.o."
r'[A-Z][a-zA-Z]*\s+(a\.s\.|s\.r\.o\.)'
```

#### Dátum
```python
# Nájde: "19.1.2026", "3.12.2025"
r'\d{1,2}\.\d{1,2}\.\d{4}'
```

#### Čas
```python
# Nájde: "10:30", "9:05"
r'\d{1,2}:\d{2}'
```

#### Telefónne číslo
```python
# Nájde: "+421 123 456 789"
r'\+\d{2,3}\s*\d{3}[\s-]?\d{3}[\s-]?\d{3,4}'
```

#### Sumy peňazí
```python
# Nájde: "100 €", "1,500.00 EUR"
r'\d+([,\.]\d+)?\s*(€|EUR|Sk|USD)'
```

#### Email
```python
r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
```

### Inteligentné rozpoznávače
```python
# "dnes" → aktuálny dátum
# "zajtra" → aktuálny dátum + 1 deň
# "o týždeň" → aktuálny dátum + 7 dní
```

---

# 8️⃣ HODNOTENIE ÚSPEŠNOSTI

## V projekte: `eval/run.py`

### Precision (Presnosť)
**Koľko z vrátených dokumentov je relevantných?**
```
Precision = TP / (TP + FP)
          = (počet relevantných vo výsledkoch) / (celkový počet výsledkov)
```

### Recall (Úplnosť)
**Koľko relevantných dokumentov sme našli?**
```
Recall = TP / (TP + FN)
       = (počet relevantných vo výsledkoch) / (celkový počet relevantných)
```

### F1-Score
**Harmonický priemer Precision a Recall**
```
F1 = 2 × (P × R) / (P + R)
```

### Príklad výpočtu (TOTO SA NAUČ!)

```
Všetky relevantné dokumenty: {1, 2, 3, 4, 5}
Systém vrátil: {1, 2, 6, 7, 8}

TP (True Positive) = {1, 2} = 2     (vrátené A relevantné)
FP (False Positive) = {6, 7, 8} = 3 (vrátené ALE nerelevantné)
FN (False Negative) = {3, 4, 5} = 3 (relevantné ALE nevrátené)

Precision = 2 / (2+3) = 2/5 = 0.40 = 40%
Recall = 2 / (2+3) = 2/5 = 0.40 = 40%
F1 = 2 × (0.4 × 0.4) / (0.4 + 0.4) = 0.32 / 0.8 = 0.40 = 40%
```

### S lematizáciou vs bez

```
Dopyt: "running shoes"

BEZ lematizácie:
- Nájde: doc1 (obsahuje "running shoes")
- Nenájde: doc2 (obsahuje "run shoe")

S lematizáciou:
- "running" → "run"
- "shoes" → "shoe"
- Nájde: doc1 aj doc2!

Výsledok: Recall sa zvýši!
```

---

# 9️⃣ DISTRIBUOVANÉ SPRACOVANIE

## V projekte: `spark_jobs/enwiki_spark_parser.py`

### MapReduce Paradigma

**Map:** Transformuj vstup na (kľúč, hodnota) páry
**Reduce:** Agreguj hodnoty so rovnakým kľúčom

### Word Count (BUDE NA SKÚŠKE!)

```
Vstup: "foo bar foo qux bar foo"

=== MAPPER ===
Pre každé slovo emit(slovo, 1):
  emit(foo, 1)
  emit(bar, 1)
  emit(foo, 1)
  emit(qux, 1)
  emit(bar, 1)
  emit(foo, 1)

=== SHUFFLE & SORT ===
Zoskupí podľa kľúča:
  foo: [1, 1, 1]
  bar: [1, 1]
  qux: [1]

=== REDUCER ===
Pre každý kľúč sčítaj hodnoty:
  emit(foo, 3)
  emit(bar, 2)
  emit(qux, 1)
```

**Pseudokód:**
```python
# MAPPER
def mapper(line):
    words = line.split()
    for word in words:
        emit(word, 1)

# REDUCER
def reducer(word, values):
    total = sum(values)
    emit(word, total)
```

### V projekte (Spark)
```python
# Z enwiki_spark_parser.py
spark = SparkSession.builder \
    .appName("WikiCulinaryParser") \
    .getOrCreate()

# Paralelné spracovanie Wikipedia dump
rdd = spark.sparkContext.textFile(input_path)
results = rdd.flatMap(parse_page).filter(is_food_article)
```

---

# 🔟 SIETE A SÉMANTIKA

### Small-World Networks (Siete malého sveta)

**Vlastnosti:**
1. **Krátke cesty** - Medzi ľubovoľnými dvoma uzlami existuje krátka cesta
2. **Vysoký clustering** - Susedia majú tendenciu byť tiež prepojení
3. **Degree distribution** - Málo uzlov s veľa spojeniami (hubs)

**Príklad:** 6 stupňov oddelenia (každý človek je prepojený s každým cez max 6 ľudí)

### Sémantické vyhľadávanie

**Klasické vyhľadávanie:** Hľadá presné slová
```
Query: "car" → Nájde dokumenty obsahujúce "car"
Nenájde: "automobile", "vehicle"
```

**Sémantické vyhľadávanie:** Rozumie významu
```
Query: "car" → Nájde: "car", "automobile", "vehicle", "auto"
```

**Ako to funguje:**
1. **Ontológie** - štruktúrované znalosti (Car IS-A Vehicle)
2. **Word embeddings** - vektory slov (Word2Vec, BERT)
3. **Knowledge graphs** - grafy entít a vzťahov

---

# ✅ CHECKLIST - Čo je v projekte

| Téma | Implementované | Súbor | Poznámka |
|------|----------------|-------|----------|
| Crawling | ✅ | `crawler/run.py` | BFS stratégia, robots.txt |
| Tokenizácia | ✅ | `parser/html_parser.py` | Regex-based |
| Invertovaný index | ✅ | `index/v1/` | TSV formát |
| TF-IDF | ✅ | `search_cli/run.py` | Implementované |
| BM25 | ✅ | `search_cli/run.py` | Implementované |
| Lucene | ✅ | `indexer/lucene_indexer.py` | PyLucene |
| Entity extraction | ✅ | `entities/recipe_enricher.py` | Aho-Corasick |
| Regex | ✅ | `parser/html_parser.py` | Časy, ingrediencie |
| Evaluation | ✅ | `eval/run.py` | P@k, R@k, MAP, NDCG |
| MapReduce | ✅ | `spark_jobs/enwiki_spark_parser.py` | PySpark |

---

# 📝 VZOROVÉ OTÁZKY NA SKÚŠKU

## 1. Tokenizácia
**Otázka:** Použite whitespace tokenizer na text "Skúška z VI bude 19.1.2026!"
**Odpoveď:** ["Skúška", "z", "VI", "bude", "19.1.2026!"]

## 2. Kosínusová podobnosť
**Otázka:** Vypočítajte kosínus medzi A=[1,2,0] a B=[2,1,1]
**Odpoveď:**
```
A·B = 1×2 + 2×1 + 0×1 = 4
||A|| = √(1+4+0) = √5 = 2.24
||B|| = √(4+1+1) = √6 = 2.45
cos = 4 / (2.24 × 2.45) = 4 / 5.49 = 0.73
```

## 3. PageRank
**Otázka:** A→B, B→C, C→A. Jedna iterácia s d=0.85, PR₀=1/3
**Odpoveď:** (viď sekcia PageRank vyššie)

## 4. Precision/Recall
**Otázka:** Relevantné={1,2,3}, Vrátené={1,3,4,5}
**Odpoveď:**
```
TP=2, FP=2, FN=1
P = 2/4 = 0.5
R = 2/3 = 0.67
F1 = 2×0.5×0.67/(0.5+0.67) = 0.57
```

## 5. Regex
**Otázka:** Napíšte regex pre slovenské firmy (a.s., s.r.o.)
**Odpoveď:** `[A-Z][a-zA-Z]+\s+(a\.s\.|s\.r\.o\.)`

## 6. MapReduce
**Otázka:** Napíšte pseudokód pre word count
**Odpoveď:** (viď sekcia MapReduce vyššie)

---

# 🏆 PRIORITY UČENIA

1. ⭐⭐⭐ **PageRank výpočet** - URČITE BUDE
2. ⭐⭐⭐ **Kosínusová podobnosť** - URČITE BUDE  
3. ⭐⭐⭐ **Precision/Recall/F1** - URČITE BUDE
4. ⭐⭐⭐ **MapReduce pseudokód** - URČITE BUDE
5. ⭐⭐⭐ **Regex príklady** - URČITE BUDE
6. ⭐⭐ **HITS algoritmus** - PRAVDEPODOBNE
7. ⭐⭐ **Invertovaný index** - PRAVDEPODOBNE
8. ⭐⭐ **NE, CO, TE, TR, ST** - PRAVDEPODOBNE
9. ⭐ **BM25 vs TF-IDF** - MOŽNO
10. ⭐ **Small-world siete** - MOŽNO

---

# 🎯 ČO UKÁZAŤ UČITEĽOVI V REPORTE

## Čo v projekte MÁME a učiteľ ocení:

### 1. Crawling ✅
```python
# crawler/frontier.py - FIFO queue = BFS stratégia!
class Frontier:
    def __init__(self):
        self.queues = defaultdict(deque)  # FIFO = BFS
```
**Ukázať:** Používame BFS (breadth-first), respektujeme robots.txt

### 2. Invertovaný index ✅
```
index/v1/
├── terms.tsv      # term → df, idf
├── postings.tsv   # term → field, docId, tf
├── docmeta.tsv    # doc → metadata
```
**Ukázať:** Tri súbory tvoria kompletný invertovaný index

### 3. TF-IDF + BM25 ✅
```python
# search_cli/run.py
self.k1 = 1.2   # BM25 parameter
self.b = 0.75   # BM25 parameter
```
**Ukázať:** Implementované OBA modely, porovnanie v benchmarkoch

### 4. Entity Extraction ✅
```python
# entities/recipe_enricher.py
# Aho-Corasick automaton pre rýchle hľadanie entít
self.automaton = ahocorasick.Automaton()
```
**Ukázať:** Named Entity Recognition pomocou Wikipedia gazetteeru

### 5. Regex ✅
```python
# parser/html_parser.py
# Časy varenia
r'PT(\d+H)?(\d+M)?'
# Ingrediencie
r'<li[^>]*class="[^"]*ingredient[^"]*"[^>]*>(.*?)</li>'
```
**Ukázať:** Regex na extrakciu štruktúrovaných dát

### 6. Evaluation ✅
```python
# eval/run.py
def precision_at_k(retrieved, relevant, k): ...
def recall_at_k(retrieved, relevant, k): ...
def ndcg_at_k(retrieved, relevance, k): ...
```
**Ukázať:** Kompletné IR metriky

### 7. MapReduce (Spark) ✅
```python
# spark_jobs/enwiki_spark_parser.py
rdd = spark.sparkContext.textFile(input_path)
results = rdd.flatMap(parse_page).filter(is_food_article)
```
**Ukázať:** Distribuované spracovanie Wikipedia dump

### 8. Lucene ✅
```python
# indexer/lucene_indexer.py
from org.apache.lucene.search.similarities import BM25Similarity
```
**Ukázať:** Profesionálny search engine

## Čo v projekte CHÝBA (a čo doplniť do reportu):

### ❌ Anchor text boosting
- Máme crawling, ale anchor texty explicitne neboostujeme
- **Fix pre report:** Spomenúť, že Wikipedia enrichment plní podobnú úlohu

### ❌ Lematizácia/Stemming
- Používame Lucene StandardAnalyzer (má základný stemming)
- **Fix pre report:** Pridať príklad ako by lematizácia zmenila výsledky

### ❌ PageRank/HITS
- Nemáme implementované (nepotrebné pre recipe search)
- **Fix pre report:** Vysvetliť prečo - nie je to link-based domain

### ❌ Kosínusová podobnosť explicitne
- Používame BM25/TF-IDF skóring
- **Fix pre report:** Ukázať že BM25 je evolúcia kosínusovej podobnosti

## Odporúčaná štruktúra finálneho reportu:

```
1. Úvod
   - Cieľ projektu
   - Dataset (food.com + Wikipedia)

2. Crawling
   - BFS stratégia (frontier.py)
   - robots.txt compliance
   - Uložené dáta

3. Spracovanie textu
   - Tokenizácia (regex)
   - Extrakcia štruktúrovaných dát

4. Indexovanie
   - Invertovaný index (terms, postings, docmeta)
   - Lucene index

5. Vyhľadávanie
   - TF-IDF model
   - BM25 model
   - Porovnanie výkonnosti

6. Entity Extraction
   - Wikipedia enrichment
   - Aho-Corasick matching

7. Evaluácia
   - Precision, Recall
   - Benchmark výsledky

8. Distribuované spracovanie
   - PySpark Wikipedia parser

9. Záver
```

---

# 🔬 DETAILNÉ PRÍKLADY KÓDU Z PROJEKTU

## A. Crawler - Reálna implementácia

### A.1 Frontier (FIFO Queue = BFS)
```python
# crawler/frontier.py
class Frontier:
    """URL frontier s BFS stratégiou."""
    
    def __init__(self):
        self.queues = defaultdict(deque)  # FIFO = BFS!
        self.seen = set()  # Deduplikácia URL
        
    def add(self, url: str, depth: int = 0):
        """Pridaj URL do fronty."""
        normalized = self._normalize(url)
        if normalized not in self.seen:
            self.seen.add(normalized)
            host = urlparse(normalized).netloc
            self.queues[host].append((normalized, depth))
    
    def get_next(self) -> Tuple[str, int]:
        """Vráť ďalšiu URL (FIFO = BFS)."""
        for host, queue in self.queues.items():
            if queue:
                return queue.popleft()  # FIFO!
        return None, 0
```

### A.2 Robots.txt Parser
```python
# crawler/robots.py
class RobotsParser:
    """Parser pre robots.txt."""
    
    def is_allowed(self, url: str) -> bool:
        """Skontroluj či môžeme crawlovať URL."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        # Načítaj robots.txt (s cache)
        if robots_url not in self.cache:
            resp = requests.get(robots_url, timeout=5)
            self.cache[robots_url] = robotparser.RobotFileParser()
            self.cache[robots_url].parse(resp.text.split('\n'))
        
        return self.cache[robots_url].can_fetch('*', url)
```

## B. Parser - Extrakcia 23 premenných

### B.1 JSON-LD Parsing (Schema.org Recipe)
```python
# parser/html_parser.py
def extract_recipe_data(html: str) -> Dict[str, Any]:
    """Extrahuj dáta z HTML pomocou JSON-LD."""
    
    # Nájdi JSON-LD blok
    pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        try:
            data = json.loads(match)
            if data.get('@type') == 'Recipe':
                return {
                    'title': data.get('name', ''),
                    'description': data.get('description', ''),
                    'ingredients': data.get('recipeIngredient', []),
                    'instructions': extract_instructions(data),
                    'times': extract_times(data),
                    'nutrition': data.get('nutrition', {}),
                    'author': data.get('author', {}).get('name', ''),
                    'image': data.get('image', [{}])[0].get('url', ''),
                    # ... ďalších 15 premenných
                }
        except json.JSONDecodeError:
            continue
    return {}

def extract_times(data: Dict) -> Dict[str, int]:
    """Parsuj ISO 8601 duration (PT30M = 30 minút)."""
    result = {}
    
    for key in ['prepTime', 'cookTime', 'totalTime']:
        duration = data.get(key, '')
        if duration:
            # PT1H30M → 90 minút
            hours = re.search(r'(\d+)H', duration)
            mins = re.search(r'(\d+)M', duration)
            
            total = 0
            if hours: total += int(hours.group(1)) * 60
            if mins: total += int(mins.group(1))
            
            result[key.replace('Time', '')] = total
    
    return result
```

### B.2 Regex pre ingrediencie
```python
# parser/ingredient_extractor.py
def parse_ingredient(text: str) -> Dict:
    """Parsuj ingredienciu na množstvo, jednotku, názov."""
    
    # Vzor: "2 cups flour" alebo "1/2 teaspoon salt"
    pattern = r'''
        ^
        ([\d/½¼¾⅓⅔]+)?     # Množstvo (optional)
        \s*
        (cups?|tbsp|tsp|oz|lb|g|kg|ml|l)?  # Jednotka (optional)
        \s*
        (.+)               # Názov ingrediencie
        $
    '''
    
    match = re.match(pattern, text, re.VERBOSE | re.IGNORECASE)
    if match:
        return {
            'amount': parse_fraction(match.group(1)),
            'unit': match.group(2) or '',
            'name': match.group(3).strip()
        }
    return {'amount': None, 'unit': '', 'name': text}
```

## C. Simple Index - Čistá Python implementácia

### C.1 Budovanie indexu
```python
# indexer/simple_indexer.py
class SimpleIndexer:
    """Invertovaný index bez externých závislostí."""
    
    def __init__(self):
        self.terms = {}          # term → (df, idf)
        self.postings = defaultdict(list)  # term → [(field, docId, tf)]
        self.doc_metadata = {}   # docId → metadata
        
        # Váhy polí
        self.field_weights = {
            'title': 3.0,        # Titulok má najvyššiu váhu
            'ingredients': 2.0,  # Ingrediencie stredná
            'instructions': 1.0  # Inštrukcie najnižšia
        }
    
    def build(self, recipes: List[Dict]):
        """Vybuduj index z receptov."""
        
        # 1. Tokenizuj a počítaj termy
        term_doc_counts = defaultdict(set)
        
        for recipe in recipes:
            doc_id = str(recipe['id'])
            
            for field in ['title', 'ingredients', 'instructions']:
                text = self._get_field_text(recipe, field)
                tokens = self._tokenize(text)
                term_counts = Counter(tokens)
                
                for term, tf in term_counts.items():
                    term_doc_counts[term].add(doc_id)
                    self.postings[term].append((field, doc_id, tf))
        
        # 2. Vypočítaj IDF
        N = len(recipes)
        for term, doc_set in term_doc_counts.items():
            df = len(doc_set)
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1)  # BM25 IDF
            self.terms[term] = (df, idf)
```

### C.2 BM25 Vyhľadávanie
```python
# indexer/simple_indexer.py
class SimpleSearcher:
    """Vyhľadávač pre Simple index."""
    
    # BM25 parametre
    K1 = 1.2  # Saturácia TF
    B = 0.75  # Normalizácia dĺžky
    
    def search_bm25(self, query: str, k: int = 10) -> List[Dict]:
        """Vyhľadaj pomocou BM25."""
        
        query_terms = self._tokenize(query)
        doc_scores = defaultdict(float)
        
        for term in query_terms:
            if term not in self.postings:
                continue
            
            df, idf = self.terms[term]
            
            for field, doc_id, tf in self.postings[term]:
                # Získaj dĺžku dokumentu
                doc_len = self.field_lengths[field][doc_id]
                avg_len = self.avg_doc_lengths[field]
                
                # BM25 vzorec
                numerator = tf * (self.K1 + 1)
                denominator = tf + self.K1 * (1 - self.B + self.B * doc_len / avg_len)
                
                weight = self.field_weights.get(field, 1.0)
                score = idf * (numerator / denominator) * weight
                
                doc_scores[doc_id] += score
        
        # Zoraď a vráť top-k
        sorted_docs = sorted(doc_scores.items(), 
                           key=lambda x: x[1], reverse=True)[:k]
        
        return [{'docId': d, 'score': s} for d, s in sorted_docs]
```

## D. Lucene/PyLucene Index

### D.1 Indexovanie do Lucene
```python
# indexer/lucene_indexer.py
from lupyne import engine
from org.apache.lucene.analysis.standard import StandardAnalyzer

class LuceneIndexer:
    """PyLucene indexer pomocou Lupyne wrappera."""
    
    def __init__(self, index_dir: str):
        self.indexer = engine.Indexer(index_dir, StandardAnalyzer())
        
        # Definuj polia
        self.indexer.set('docId', stored=True)
        self.indexer.set('title_text', stored=True, tokenized=True)
        self.indexer.set('ingredients_text', stored=True, tokenized=True)
        self.indexer.set('instructions_text', stored=True, tokenized=True)
        self.indexer.set('total_minutes', stored=True, docValues=True)
    
    def index_recipe(self, recipe: Dict):
        """Indexuj jeden recept."""
        doc = {
            'docId': str(recipe['id']),
            'title_text': recipe.get('title', ''),
            'ingredients_text': ' '.join(recipe.get('ingredients', [])),
            'instructions_text': ' '.join(recipe.get('instructions', [])),
            'total_minutes': recipe.get('times', {}).get('total', 0)
        }
        self.indexer.add(doc)
```

### D.2 BM25 vs TF-IDF v Lucene
```python
# search_cli/lupyne_searcher.py
from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity

class LupyneSearcher:
    """Vyhľadávač s podporou BM25 a TF-IDF."""
    
    def search_bm25(self, query: str, k: int = 10):
        """Vyhľadaj pomocou BM25."""
        self.searcher.setSimilarity(BM25Similarity())
        return self._search(query, k)
    
    def search_tfidf(self, query: str, k: int = 10):
        """Vyhľadaj pomocou klasického TF-IDF."""
        self.searcher.setSimilarity(ClassicSimilarity())
        return self._search(query, k)
    
    def _search(self, query: str, k: int):
        """Vykonaj vyhľadávanie s váhovaním polí."""
        # Multi-field query s boostami
        query_parts = []
        for term in query.split():
            escaped = QueryParser.escape(term)
            query_parts.append(f"title_text:{escaped}^2.0")     # Boost titulku
            query_parts.append(f"ingredients_text:{escaped}^1.5")
            query_parts.append(f"instructions_text:{escaped}^1.0")
        
        query_str = " OR ".join(query_parts)
        parsed_query = self.searcher.parse(query_str)
        
        return self.searcher.search(parsed_query, count=k)
```

## E. Wikipedia Spark Parser

### E.1 Streaming XML Parser
```python
# spark_jobs/enwiki_spark_parser.py
def stream_pages(input_path: str):
    """Streamuj Wikipedia XML stránky bez načítania celého súboru."""
    
    import bz2
    
    buffer = []
    in_page = False
    
    # Streaming čítanie komprimovaného súboru
    with bz2.open(input_path, 'rt', encoding='utf-8') as f:
        for line in f:
            if '<page>' in line:
                in_page = True
                buffer = [line[line.index('<page>'):]]
            elif in_page:
                buffer.append(line)
                if '</page>' in line:
                    # Kompletná stránka
                    page_xml = ''.join(buffer)
                    yield page_xml
                    in_page = False
                    buffer = []
```

### E.2 Filtrovanie kulinárskych článkov
```python
# spark_jobs/enwiki_spark_parser.py
class WikiXMLParser:
    """Parser pre Wikipedia XML."""
    
    # Infobox vzory pre jedlo
    INFOBOX_PATTERNS = [
        re.compile(r'{{\s*Infobox\s+food', re.I),
        re.compile(r'{{\s*Infobox\s+prepared\s+food', re.I),
        re.compile(r'{{\s*Infobox\s+ingredient', re.I),
    ]
    
    # Kulinárske kategórie
    FOOD_SIGNALS = [
        'cuisine', 'dish', 'food', 'recipe', 'cooking',
        'ingredient', 'beverage', 'dessert', 'bread'
    ]
    
    @staticmethod
    def is_food_article(text: str, categories: List[str]) -> bool:
        """Urči či je článok o jedle."""
        
        # Kontrola infoboxu
        has_food_infobox = any(
            p.search(text) for p in WikiXMLParser.INFOBOX_PATTERNS
        )
        if has_food_infobox:
            return True
        
        # Kontrola kategórií
        cat_text = ' '.join(categories).lower()
        food_signals = sum(
            1 for s in WikiXMLParser.FOOD_SIGNALS if s in cat_text
        )
        return food_signals >= 2
```

### E.3 Extrakcia metadát z Wiki
```python
# spark_jobs/enwiki_spark_parser.py
@staticmethod
def extract_history(text: str) -> str:
    """Extrahuj History sekciu."""
    pattern = r'==+\s*History\s*==+(.*?)(?:==+|\Z)'
    match = re.search(pattern, text, re.DOTALL | re.I)
    if match:
        history = match.group(1)
        # Vyčisti wiki markup
        history = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', history)
        history = re.sub(r'<ref[^>]*>.*?</ref>', '', history, flags=re.DOTALL)
        return history[:1000]  # Max 1000 znakov
    return ''

@staticmethod
def extract_origin(text: str) -> str:
    """Extrahuj krajinu pôvodu z Infoboxu."""
    pattern = r'\|\s*origin[^=]*=\s*([^\n|]+)'
    match = re.search(pattern, text, re.I)
    if match:
        origin = match.group(1).strip()
        # Vyčisti wiki linky
        origin = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', origin)
        return origin
    return ''
```

## F. Entity Enrichment (Aho-Corasick)

### F.1 Budovanie automatu
```python
# entities/recipe_enricher.py
import ahocorasick

class RecipeEnricher:
    """Obohatenie receptov o Wikipedia entity."""
    
    def __init__(self, gazetteer_path: str):
        self.automaton = ahocorasick.Automaton()
        self.wiki_data = {}
        
        # Načítaj gazetteer
        with open(gazetteer_path, 'r') as f:
            next(f)  # Skip header
            for line in f:
                surface, wiki_title, entity_type = line.strip().split('\t')
                # Pridaj do automatu (case-insensitive)
                self.automaton.add_word(surface.lower(), (surface, wiki_title, entity_type))
        
        self.automaton.make_automaton()  # Finalizuj
    
    def enrich(self, recipe: Dict) -> Dict:
        """Obohaťte recept o Wikipedia entity."""
        
        # Kombinuj text na prehľadávanie
        text = f"{recipe['title']} {' '.join(recipe['ingredients'])} {' '.join(recipe['instructions'])}"
        text_lower = text.lower()
        
        # Nájdi entity pomocou Aho-Corasick (O(n) zložitosť!)
        wiki_links = []
        seen = set()
        
        for end_pos, (surface, wiki_title, entity_type) in self.automaton.iter(text_lower):
            if wiki_title not in seen:
                seen.add(wiki_title)
                wiki_links.append({
                    'surface': surface,
                    'wiki_title': wiki_title,
                    'type': entity_type,
                    'wiki_url': f"https://en.wikipedia.org/wiki/{wiki_title.replace(' ', '_')}"
                })
        
        recipe['wiki_links'] = wiki_links
        return recipe
```

### F.2 Aho-Corasick - Ako funguje
```
Aho-Corasick je algoritmus pre multi-pattern matching.

Príklad: Hľadáme ["garlic", "onion", "oil"] v texte "garlic and onion"

1. Budovanie TRIE:
       (root)
       /  |  \
      g   o   o
      |   |   |
      a   n   i
      |   |   |
      r   i   l
      |   |
      l   o
      |   |
      i   n
      |
      c

2. Failure linky (ako KMP):
   Ak neuspejeme, skočíme na najdlhší suffix

3. Prechod textu (O(n)):
   "garlic and onion"
    ^---- nájdené "garlic"
               ^---- nájdené "onion"

Zložitosť: O(n + m + z)
- n = dĺžka textu
- m = súčet dĺžok vzorov  
- z = počet nájdených zhôd
```

## G. Evaluation Metriky

### G.1 Precision, Recall, F1
```python
# eval/run.py
def precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """Precision@k - Koľko z top-k je relevantných."""
    retrieved_k = retrieved[:k]
    relevant_in_k = sum(1 for doc in retrieved_k if doc in relevant)
    return relevant_in_k / k if k > 0 else 0.0

def recall_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """Recall@k - Koľko relevantných sme našli v top-k."""
    retrieved_k = set(retrieved[:k])
    found = len(retrieved_k & relevant)
    return found / len(relevant) if relevant else 0.0

def f1_score(precision: float, recall: float) -> float:
    """F1 = harmonický priemer P a R."""
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
```

### G.2 NDCG (Normalized Discounted Cumulative Gain)
```python
# eval/run.py
def ndcg_at_k(retrieved: List[str], relevance: Dict[str, int], k: int) -> float:
    """NDCG@k - Meria kvalitu zoradenia."""
    
    def dcg(scores: List[int]) -> float:
        """Discounted Cumulative Gain."""
        return sum(
            (2**rel - 1) / math.log2(i + 2)  # +2 lebo log2(1) = 0
            for i, rel in enumerate(scores)
        )
    
    # Skutočné skóre v poradí výsledkov
    actual_scores = [relevance.get(doc, 0) for doc in retrieved[:k]]
    
    # Ideálne skóre (zoradené od najlepšieho)
    ideal_scores = sorted(relevance.values(), reverse=True)[:k]
    
    dcg_actual = dcg(actual_scores)
    dcg_ideal = dcg(ideal_scores)
    
    return dcg_actual / dcg_ideal if dcg_ideal > 0 else 0.0
```

---

# 📊 ŠTATISTIKY PROJEKTU

## Dátové súbory

| Súbor | Počet záznamov | Veľkosť |
|-------|----------------|---------|
| HTML súbory (raw) | 5,646 | 2.2 GB |
| recipes_foodcom.jsonl | 5,646 | 12 MB |
| wiki_culinary.jsonl | 9,693 | 11 MB |
| recipes_enriched.jsonl | 5,646 | 78 MB |

## Extrahované premenné

### Z food.com (23 premenných):
1. id, url, title, description
2. ingredients (list), instructions (list)
3. times (prep, cook, total)
4. cuisine, category, difficulty
5. yield, serving_size
6. author, author_bio, author_location
7. nutrition (9 hodnôt: calories, fat, protein, carbs, ...)
8. ratings (average, count)
9. image, all_images, keywords, date_published

### Z Wikipedia (15 premenných):
1. wiki_id, wiki_title, abstract
2. type (dish, ingredient, technique, tool)
3. origin_country, origin_region, year_origin
4. history, categories, infobox
5. redirects, alternate_names, variations, main_ingredient

### Obohatenie (+4 premenné):
1. wiki_links (priemerne 24.75 linkov/recept)
2. historical_context (97.9% pokrytie)
3. dish_info (70.1% pokrytie)
4. ingredient_origins (96.5% pokrytie)

## Index štatistiky

### Simple Index (TSV):
- Počet termov: 14,977
- Počet postingov: 2,506,115
- Veľkosť: 54.7 MB

### Lucene Index:
- Dokumenty: 5,646
- Veľkosť (BM25): 49.5 MB
- Veľkosť (TF-IDF): 49.5 MB

---

*Vytvorené pre VINF projekt - December 2025*
*Aktualizované s reálnym kódom z projektu*
