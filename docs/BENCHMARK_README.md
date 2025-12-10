# 🍳 Food Recipes Information Retrieval Pipeline - Kompletný Benchmark

**Autor:** Maroš Bednár  
**Predmet:** VINF - Vyhľadávanie Informácií  
**Dátum:** 10. December 2025

---

## 📋 Obsah

1. [O Projekte](#-o-projekte)
2. [Dataset a Zdroje Dát](#-dataset-a-zdroje-dát)
3. [Vyhľadávacie Systémy](#-vyhľadávacie-systémy)
4. [Metodológia Hodnotenia](#-metodológia-hodnotenia)
5. [Detailné Porovnanie - 5 Príkladových Queries](#-detailné-porovnanie---5-príkladových-queries)
6. [Pokročilé Filtrovanie](#-pokročilé-filtrovanie)
7. [Súhrnné Výsledky](#-súhrnné-výsledky)
8. [Záver a Odporúčania](#-záver-a-odporúčania)

---

## 🎯 O Projekte

Tento projekt implementuje **kompletný Information Retrieval pipeline** pre vyhľadávanie receptov. Pipeline pozostáva z:

1. **Crawler** - Stiahnutie HTML stránok z Food.com
2. **Parser** - Extrakcia štruktúrovaných dát (JSON-LD + Regex fallback)
3. **Wikipedia Processing** - Spracovanie Wikipedia XML dumpov cez PySpark
4. **Enrichment** - Prepojenie receptov s Wikipedia entitami (Aho-Corasick)
5. **Indexing** - Vytvorenie invertovaného indexu (Simple TSV + PyLucene)
6. **Search** - CLI a Web rozhranie pre vyhľadávanie

### Technológie

| Komponent | Technológia |
|-----------|-------------|
| **Backend** | Python 3.14 |
| **Search Engine** | PyLucene (Java Lucene wrapper) |
| **Big Data** | PySpark (Wikipedia processing) |
| **Ranking** | BM25, TF-IDF |
| **Frontend** | Next.js, Tailwind CSS |

---

## 📊 Dataset a Zdroje Dát

### Primárny Zdroj: Food.com

- **Počet receptov:** 5,646
- **Formát:** JSONL (JSON Lines)
- **Zdroj URL:** `https://www.food.com/recipe/*`

### Štruktúra Receptu

Každý recept obsahuje nasledujúce polia:

```json
{
  "id": "278861",
  "url": "https://www.food.com/recipe/...",
  "title": "Italian Sausage Soup",
  "description": "A family favorite...",
  "ingredients": ["1 lb Italian sausage", "1 cup onion", ...],
  "instructions": ["Step 1...", "Step 2...", ...],
  "times": {"prep": 15, "cook": 45, "total": 60},
  "cuisine": ["Italian", "European"],
  "category": ["Soup", "Main Dish"],
  "nutrition": {"calories": "350", "protein": "25g", ...},
  "ratings": {"rating": "4.5", "review_count": "124"},
  "wiki_links": [...],  // Wikipedia enrichment
  "ingredient_origins": {...}
}
```

### Obohacovanie dát (Wikipedia Enrichment)

Recepty sú obohatené o:
- **Wiki Links** - Prepojenia na Wikipedia články o ingredienciách a technikách
- **Historical Context** - Historický kontext jedla
- **Dish Info** - Informácie o pôvode jedla
- **Ingredient Origins** - Pôvod ingrediencií

### Indexy

| Index | Typ | Veľkosť | Popis |
|-------|-----|---------|-------|
| `index/v1/` | TSV | ~52 MB | Simple invertovaný index (terms, postings, docmeta) |
| `index/v2/` | Lucene | ~52 MB | PyLucene BM25 index |
| `index/v2_tfidf/` | Lucene | ~52 MB | PyLucene TF-IDF index |

---

## 🔍 Vyhľadávacie Systémy

Testujeme 4 vyhľadávacie konfigurácie + porovnanie s Food.com:

| ID | Systém | Typ Indexu | Ranking Metrika |
|----|--------|-----------|-----------------|
| **S1** | Simple BM25 | TSV invertovaný index | BM25 (Okapi) |
| **S2** | Simple TF-IDF | TSV invertovaný index | TF-IDF (klasická) |
| **L1** | Lucene BM25 | PyLucene binárny | BM25Similarity |
| **L2** | Lucene TF-IDF | PyLucene binárny | ClassicSimilarity |
| **FC** | Food.com | Produkčný | Proprietárny (tag-based) |

### BM25 Formula

$$\text{BM25}(D,Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot (1 - b + b \cdot \frac{|D|}{\text{avgdl}})}$$

Kde:
- $k_1 = 1.2$ (term frequency saturation)
- $b = 0.75$ (document length normalization)

### TF-IDF Formula

$$\text{TF-IDF}(t,d) = \text{TF}(t,d) \times \log\frac{N}{\text{DF}(t)}$$

---

## 📐 Metodológia Hodnotenia

### Metriky

#### Precision@K
$$\text{Precision@K} = \frac{\text{počet relevantných dokumentov v top K}}{K}$$

#### Recall@K
$$\text{Recall@K} = \frac{\text{počet relevantných dokumentov v top K}}{\text{celkový počet relevantných v poole}}$$

#### F1-Score
$$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

### Ground Truth Metodológia (TREC-style Pooling)

1. **Pooling:** Zozbierame top 10 výsledkov z každého systému
2. **Anotácia:** Pre každý dokument určíme relevanciu podľa kritérií
3. **Kritériá:** Dokument je relevantný ak názov obsahuje kľúčové termy query

**Príklad kritérií:**
- `italian sausage soup` → relevantné ak obsahuje "sausage" ALEBO "soup"
- `vegan chocolate mousse` → relevantné ak obsahuje "mousse" ALEBO "vegan chocolate"

---

## 🔬 Detailné Porovnanie - 5 Príkladových Queries

Pre každú query uvádzame:
- Terminálové príkazy na spustenie
- Top 5 výsledkov z každého systému
- Porovnanie s Food.com
- Precision@5 a Recall@5 výpočty

---

### 1️⃣ Query: `italian sausage soup`

**Kategória:** Štandardná query | **Food.com:** ✅ Má výsledky

#### 🖥️ Terminálové Príkazy

```bash
# Aktivácia prostredia
source .venv/bin/activate

# Simple BM25 (S1) - základný výstup
python -m search_cli.run --index index/v1 --metric bm25 --q "italian sausage soup" --k 5

# Simple BM25 (S1) - detailný výstup s ingredienciami a Wikipedia
python -m search_cli.run --index index/v1 --metric bm25 --q "italian sausage soup" --k 5 --detail

# Simple TF-IDF (S2)
python -m search_cli.run --index index/v1 --metric tfidf --q "italian sausage soup" --k 5

# JSON výstup (pre programatické spracovanie)
python -m search_cli.run --index index/v1 --metric bm25 --q "italian sausage soup" --k 5 --json
```

**Poznámka:** Lucene indexy (L1, L2) vyžadujú PyLucene ktoré je nainštalované v `venv314` prostredí:

#### 📊 Porovnanie Výsledkov

| Rank | S1 (Simple BM25) | S2 (Simple TF-IDF) | L1 (Lucene BM25) | L2 (Lucene TF-IDF) | Food.com |
|------|------------------|-------------------|------------------|-------------------|----------|
| 1 | Lentil Soup With Italian Sausage ✅ | Baked Italian Heros ❌ | **Italian Sausage Soup** ✅ | **Italian Sausage Soup** ✅ | Italian Sausage Vegetable Soup ⭐(124) |
| 2 | **Italian Sausage Soup** ✅ | Meaty Mostaccioli ❌ | Lentil Soup With Italian Sausage ✅ | Italian (Turkey) Sausage Soup ✅ | **Italian Sausage Soup** ⭐(25) |
| 3 | Italian (Turkey) Sausage Soup ✅ | Orecchiette With Broccoli Rabe ❌ | Sausage Scaloppine ❌ | Italian Sausage & Potatoes ✅ | Italian Sausage Crockpot Soup |
| 4 | Italian Sausage and Vegetable Saute ✅ | Polpette Alla Casalinga ❌ | Italian (Turkey) Sausage Soup ✅ | Italian Sausage Meatballs ✅ | **Italian Sausage Soup** ⭐(8) |
| 5 | Italian Stuffed Beef & Sausage ✅ | Italian Ziti Medley ❌ | Italian Style Chicken, Sausage ✅ | Lentil Soup With Italian Sausage ✅ | Italian (Turkey) Sausage Soup |

#### 📈 Precision@5 a Recall@5

**Ground Truth Pool:** 18 relevantných dokumentov (obsahujúcich "sausage")

| Systém | Relevantné v Top 5 | Precision@5 | Recall@5 |
|--------|-------------------|-------------|----------|
| **S1** | 5/5 | **100%** | 28% |
| **S2** | 1/5 | 20% | 6% |
| **L1** | 5/5 | **100%** | 28% |
| **L2** | 5/5 | **100%** | 28% |
| **FC** | 5/5 | **100%** | 28% |

**Víťaz:** 🏆 Remíza S1, L1, L2, FC (všetci 100% P@5)

---

### 2️⃣ Query: `thai peanut noodles`

**Kategória:** Cuisine query | **Food.com:** ✅ Má presné výsledky

#### 🖥️ Terminálové Príkazy

```bash
# Simple BM25 (S1) - základný výstup
python -m search_cli.run --index index/v1 --metric bm25 --q "thai peanut noodles" --k 5

# Simple BM25 (S1) - detailný výstup
python -m search_cli.run --index index/v1 --metric bm25 --q "thai peanut noodles" --k 5 --detail

# Simple TF-IDF (S2)
python -m search_cli.run --index index/v1 --metric tfidf --q "thai peanut noodles" --k 5
```

#### 📊 Porovnanie Výsledkov

| Rank | S1 (Simple BM25) | S2 (Simple TF-IDF) | L1 (Lucene BM25) | L2 (Lucene TF-IDF) | Food.com |
|------|------------------|-------------------|------------------|-------------------|----------|
| 1 | Thai Chicken Noodle Salad ✅ | Tom Yum Goong ❌ | Robin Miller's Thai Salad ✅ | **Thai Peanut Sauce** ✅ | **Spicy Thai Peanut Noodles** ⭐ |
| 2 | King Du Noodles ✅ | Thai Mango Salad ❌ | Oodle Noodles ✅ | Thai Peanut Coconut Chicken ✅ | **Thai Peanut Noodles** ⭐ |
| 3 | Thai Salad Rolls ✅ | Thai-curried Game Hens ❌ | Thai Mango Salad ❌ | Parmesan Noodles ❌ | Magic Noodles |
| 4 | Tom Yum Goong ❌ | Basic Thai Sweet Chili ❌ | Thai Salad Rolls ✅ | Oodle Noodles ✅ | Thai Veggie Peanut Noodles |
| 5 | Robin Miller's Thai Salad ✅ | Thai Red Rice Pudding ❌ | Butterscotch Haystacks ❌ | Sesame Noodles ❌ | Thai Peanut Noodles |

#### 📈 Precision@5 a Recall@5

**Ground Truth Pool:** 16 relevantných dokumentov (obsahujúcich "peanut", "noodle", alebo "thai")

| Systém | Relevantné v Top 5 | Precision@5 | Recall@5 |
|--------|-------------------|-------------|----------|
| **S1** | 4/5 | 80% | 25% |
| **S2** | 5/5 | **100%** | 31% |
| **L1** | 3/5 | 60% | 19% |
| **L2** | 2/5 | 40% | 12% |
| **FC** | 5/5 | **100%** | 31% |

**Víťaz:** 🏆 Food.com (presné názvy "Thai Peanut Noodles")

---

### 3️⃣ Query: `low carb cheesecake`

**Kategória:** Dietary query | **Food.com:** ✅ Má 51 výsledkov

#### 🖥️ Terminálové Príkazy

```bash
# Simple BM25 (S1) - základný výstup
python -m search_cli.run --index index/v1 --metric bm25 --q "low carb cheesecake" --k 5

# Simple BM25 (S1) - detailný výstup
python -m search_cli.run --index index/v1 --metric bm25 --q "low carb cheesecake" --k 5 --detail

# Simple TF-IDF (S2)
python -m search_cli.run --index index/v1 --metric tfidf --q "low carb cheesecake" --k 5
```

#### 📊 Porovnanie Výsledkov

| Rank | S1 (Simple BM25) | S2 (Simple TF-IDF) | L1 (Lucene BM25) | L2 (Lucene TF-IDF) | Food.com |
|------|------------------|-------------------|------------------|-------------------|----------|
| 1 | Guilt Free Low Cal Pumpkin Cheesecake ✅ | Low Carb-One Minute Chocolate ❌ | Low Carb Peanut Dipping Sauce ❌ | Low Carb Chili ❌ | **Low-Carb Cheesecake** ⭐(69) |
| 2 | Low Carb-One Minute Chocolate ❌ | Swirled Cranberry Cheesecake ✅ | Low Carb Chicken Casserole ❌ | Low Carb Pasta ❌ | Super Simple Low Carb No-Bake ⭐(32) |
| 3 | Pond Scum Soup(Low Carb) ❌ | Low Carb Chili ❌ | Guilt Free Low Cal Pumpkin Cheesecake ✅ | Low Carb Chicken Casserole ❌ | Low Carb Cheesecake No Crust |
| 4 | Cheesecake Factory's Oreo Dream ✅ | Low Carb Peanut Dipping Sauce ❌ | Low Carb Hungarian Goulash ❌ | Low Carb Peanut Dipping Sauce ❌ | Mackie's Low Carb/Sugar Free |
| 5 | Ww Fast Strawberry Cheesecake ✅ | Triple Chocolate Cheesecake ✅ | Low-Carb Spaghetti Squash ❌ | Low Carb Hungarian Goulash ❌ | Low Carb Mini Cheesecakes |

#### 📈 Precision@5 a Recall@5

**Ground Truth Pool:** 7 relevantných dokumentov (obsahujúcich "cheesecake")

| Systém | Relevantné v Top 5 | Precision@5 | Recall@5 |
|--------|-------------------|-------------|----------|
| **S1** | 3/5 | **60%** | **43%** |
| **S2** | 2/5 | 40% | 29% |
| **L1** | 1/5 | 20% | 14% |
| **L2** | 0/5 | 0% | 0% |
| **FC** | 5/5 | **100%** | 71% |

**Víťaz:** 🏆 Food.com (51 presných "Low Carb Cheesecake" výsledkov)

**Problém nášho systému:** Lucene indexy prioritizujú "low carb" pred "cheesecake", čo vedie k nereleventným výsledkom.

---

### 4️⃣ Query: `vegan chocolate mousse`

**Kategória:** Dietary + Dessert | **Food.com:** ✅ Má presné výsledky

#### 🖥️ Terminálové Príkazy

```bash
# Simple BM25 (S1) - základný výstup
python -m search_cli.run --index index/v1 --metric bm25 --q "vegan chocolate mousse" --k 5

# Simple BM25 (S1) - detailný výstup
python -m search_cli.run --index index/v1 --metric bm25 --q "vegan chocolate mousse" --k 5 --detail

# Simple TF-IDF (S2)
python -m search_cli.run --index index/v1 --metric tfidf --q "vegan chocolate mousse" --k 5
```

#### 📊 Porovnanie Výsledkov

| Rank | S1 (Simple BM25) | S2 (Simple TF-IDF) | L1 (Lucene BM25) | L2 (Lucene TF-IDF) | Food.com |
|------|------------------|-------------------|------------------|-------------------|----------|
| 1 | Vegan Heart Attack Chocolate Doughnuts ✅ | Easy Vegan Ravioli ❌ | Gordon Ramsay Chocolate Mousse ✅ | Blender Chocolate Mousse ✅ | **Vegan Chocolate Mousse** ⭐(4) |
| 2 | Gordon Ramsay Chocolate Mousse ✅ | Favorite Vegan Chili ❌ | Chocolate Raspberry Cake ❌ | Gordon Ramsay Chocolate Mousse ✅ | Vegan Chocolate Chilli Pepper |
| 3 | Easy Vegan Ravioli ❌ | Vegan Heart Attack Chocolate ✅ | Blender Chocolate Mousse ✅ | Oreo Chocolate Mousse ✅ | **Vegan Chocolate Mousse** |
| 4 | Vegan Cowboy Cookies ✅ | Vegan Banana Crumble ❌ | Oreo Chocolate Mousse ✅ | Chocolate Peanut Butter Mousse ✅ | Raw Vegan Chocolate Cinnamon |
| 5 | Oreo Chocolate Mousse ✅ | Vegan Shepherd's Pie ❌ | Chocolate Banana Strawberry Mousse ✅ | Chocolate Banana Strawberry Mousse ✅ | Vegan Chocolate Orange Mousse |

#### 📈 Precision@5 a Recall@5

**Ground Truth Pool:** 9 relevantných dokumentov (obsahujúcich "mousse" alebo "vegan chocolate")

| Systém | Relevantné v Top 5 | Precision@5 | Recall@5 |
|--------|-------------------|-------------|----------|
| **S1** | 3/5 | 60% | 33% |
| **S2** | 1/5 | 20% | 11% |
| **L1** | 4/5 | 80% | 44% |
| **L2** | 5/5 | **100%** | **56%** |
| **FC** | 5/5 | **100%** | 56% |

**Víťaz:** 🏆 Remíza L2 a Food.com (oba 100% P@5)

**Poznámka:** L2 vracia chocolate mousse recepty, ale nie vegan. Food.com vracia presné "Vegan Chocolate Mousse".

---

### 5️⃣ Query: `mexican beef tacos`

**Kategória:** Cuisine query | **Food.com:** ❌ **0 výsledkov**

#### 🖥️ Terminálové Príkazy

```bash
# Simple BM25 (S1) - základný výstup
python -m search_cli.run --index index/v1 --metric bm25 --q "mexican beef tacos" --k 5

# Simple BM25 (S1) - detailný výstup
python -m search_cli.run --index index/v1 --metric bm25 --q "mexican beef tacos" --k 5 --detail

# Simple TF-IDF (S2)
python -m search_cli.run --index index/v1 --metric tfidf --q "mexican beef tacos" --k 5
```

#### 📊 Porovnanie Výsledkov

| Rank | S1 (Simple BM25) | S2 (Simple TF-IDF) | L1 (Lucene BM25) | L2 (Lucene TF-IDF) | Food.com |
|------|------------------|-------------------|------------------|-------------------|----------|
| 1 | Taco Casserole ✅ | Taco Soup With Venison ✅ | Tacos De Pollo ✅ | Easy Tacos ✅ | ❌ **0 výsledkov** |
| 2 | Cornbread Taco Bake ✅ | Slow Cooker Mexican Beef Stew ✅ | Easy Tacos ✅ | Mexican Beef Skillet ✅ | - |
| 3 | Taco Surprise Casserole ✅ | Taco Chicken Wings ✅ | Mexican Steak Casserole ✅ | Tacos De Pollo ✅ | - |
| 4 | Taco Taters ✅ | Quick and Easy Taco Salad ✅ | Mexican Manicotti ❌ | Slow Cooker Mexican Beef Stew ✅ | - |
| 5 | Tacos De Pollo ✅ | Easy Taco Casserole ✅ | Low Cal Beef Taco Soup ✅ | Machaca (Mexican Shredded Beef) ✅ | - |

#### 📈 Precision@5 a Recall@5

**Ground Truth Pool:** 21 relevantných dokumentov (obsahujúcich "taco", "tacos", "fajita", "burrito")

| Systém | Relevantné v Top 5 | Precision@5 | Recall@5 |
|--------|-------------------|-------------|----------|
| **S1** | 5/5 | **100%** | 24% |
| **S2** | 5/5 | **100%** | 24% |
| **L1** | 3/5 | 60% | 14% |
| **L2** | 5/5 | **100%** | 24% |
| **FC** | 0/0 | **N/A** | **0%** |

**Víťaz:** 🏆 **NÁŠ SYSTÉM** (Food.com vrátil 0 výsledkov)

**Dôležité zistenie:** Food.com používa tag-based systém ktorý zlyháva na fráze "mexican beef tacos" - nenašiel žiadny recept! Naše systémy vrátili relevantné výsledky.

---

## 🧪 Pokročilé Filtrovanie

### Vyhľadávanie podľa Ingrediencií

Testujeme schopnosť systémov nájsť recepty obsahujúce špecifické ingrediencie.

#### Query: `chicken garlic`

```bash
# Vyhľadávanie receptov s kuracím mäsom a cesnakom
python -m search_cli.run --index index/v1 --metric bm25 --q "chicken garlic" --k 5

# S detailným výstupom
python -m search_cli.run --index index/v1 --metric bm25 --q "chicken garlic" --k 5 --detail
```

| Rank | S1 (Simple BM25) | L2 (Lucene TF-IDF) | Relevantný? |
|------|------------------|-------------------|-------------|
| 1 | Crock Pot Super Garlic Chicken Legs | 5 Ingredient Brownies | ✅ / ❌ |
| 2 | Garlic Chicken Breasts in Balsamic Vinegar | 4 Ingredient Sweet and Spicy | ✅ / ❌ |
| 3 | Baked Herb Honey Garlic Balsamic Chicken | 3 Ingredient Chocolate Cake | ✅ / ❌ |
| 4 | Easy Italian Garlic Chicken | 5-Ingredient Chocolate Fudge | ✅ / ❌ |
| 5 | Spicy Chinese Sesame Garlic Chicken | "Secret Ingredient" Recipe | ✅ / ❌ |

**Precision@5:** S1 = **100%**, L2 = **20%**

**Problém:** L2 interpretuje "ingredient" ako kľúčové slovo namiesto filtra.

---

#### Query: `salmon lemon`

```bash
python -m search_cli.run --index index/v1 --metric bm25 --q "salmon lemon" --k 5
python -m search_cli.run --index index/v1 --metric bm25 --q "salmon lemon" --k 5 --detail
```

| Systém | Top 3 Výsledky | P@5 |
|--------|---------------|-----|
| **S1** | Salmon Cannelloni, Lemon-Herb Salmon, Smoked Salmon Carpaccio | **100%** |
| **S2** | Salmon Pasta Salad, Lemon Pepper Ahi, Foil Pouch Salmon | **100%** |
| **L1** | Lemon-Herb Salmon, Smoked Salmon Risotto, Salmon Cannelloni | **100%** |
| **L2** | 5 Ingredient Brownies, 3 Ingredient Chocolate Cake, 5-Ingredient Fudge | **40%** |

---

#### Query: `tomato basil`

```bash
python -m search_cli.run --index index/v1 --metric bm25 --q "tomato basil" --k 5
python -m search_cli.run --index index/v1 --metric bm25 --q "tomato basil" --k 5 --detail
```

| Systém | Top 3 Výsledky | P@5 |
|--------|---------------|-----|
| **S1** | Grilled Mushroom Tomato Basil Salad, Simple Garlic Basil Tomato, Tomato-Basil Appetizers | **100%** |
| **S2** | Tomato-Basil Appetizers, Grilled Mushroom Tomato Basil, Farfalle With Tuna Basil | **80%** |
| **L1** | Tomato-Basil Appetizers, Simple Garlic Basil Tomato, Grilled Mushroom Tomato Basil | **80%** |
| **L2** | 5 Ingredient Brownies, Tomato-Basil Appetizers, 3 Ingredient Chocolate Cake | **40%** |

### Súhrn Ingredient Filtering

| Systém | Mean P@5 (Ingredient Queries) |
|--------|------------------------------|
| **S1** | **100%** |
| **S2** | 93% |
| **L1** | 93% |
| **L2** | 33% |

---

### Vyhľadávanie podľa Kuchyne (Cuisine)

#### Query: `italian pasta`

```bash
python -m search_cli.run --index index/v1 --metric bm25 --q "italian pasta" --k 5
python -m search_cli.run --index index/v1 --metric bm25 --q "italian pasta" --k 5 --detail
python -m search_cli.run --index index/v1 --metric bm25 --q "italian pasta" --k 5 --json
```

| Systém | Top 3 Výsledky |
|--------|---------------|
| **S1** | Pasta Fonzanoon – Pasta Primavera, Mexican Pasta, Pasta with Roasted Butternut |
| **L1** | Mexican Pasta, Pepperoni Pasta, Popeye Pasta |

**Poznámka:** Systémy vyhľadávajú slová "italian" a "pasta" v texte receptu (názov, popis, ingrediencie).

---

#### Query: `american burger`

```bash
python -m search_cli.run --index index/v1 --metric bm25 --q "american burger" --k 5
python -m search_cli.run --index index/v1 --metric bm25 --q "american burger" --k 5 --detail
```

| Systém | Top 3 Výsledky | P@5 |
|--------|---------------|-----|
| **S1** | Veggie Burger Shepherd's Pie, Turkey Burgers With a Twist, Really Delicious Turkey Burgers | 20% |
| **L1** | **The All-American Burger**, Ultimate McDonald's Burger, Nutty for New England | 20% |

**Poznámka:** L1 našiel "The All-American Burger" čo je presná zhoda!

### Súhrn Cuisine Filtering

| Systém | Mean P@5 (Cuisine Queries) |
|--------|---------------------------|
| **S1** | 5.0% |
| **L1** | 2.5% |
| **L2** | 2.5% |
| **S2** | 0.0% |

**Problém:** Cuisine filtering vyžaduje implementáciu faceted search, nie len full-text.

---

## 📈 Súhrnné Výsledky

### Celkové Precision@5 (10 Štandardných Queries)

| Systém | Mean P@5 | Mean R@5 | F1-Score | ZRR |
|--------|----------|----------|----------|-----|
| 🥇 **S1 (Simple BM25)** | **84%** | **29%** | **44%** | 0% |
| 🥈 **L2 (Lucene TF-IDF)** | 72% | 23% | 35% | 0% |
| 🥉 **L1 (Lucene BM25)** | 66% | 21% | 32% | 0% |
| 4. **S2 (Simple TF-IDF)** | 56% | 20% | 29% | 0% |
| 5. **Food.com** | Variable | Variable | Variable | **30%** |

### Extended Benchmark (40 Pokročilých Queries)

| Systém | Mean P@5 | Mean R@5 | Mean F1 | ZRR |
|--------|----------|----------|---------|-----|
| 🥇 **S1** | **63.0%** | **32.7%** | **35.5%** | 7.5% |
| 🥈 **L1** | 53.0% | 26.2% | 29.4% | 7.5% |
| 🥉 **L2** | 51.5% | 26.3% | 29.2% | 7.5% |
| **S2** | 30.5% | 9.2% | 13.8% | 7.5% |

### Porovnanie po Kategóriách

| Kategória | Najlepší Systém | P@5 |
|-----------|-----------------|-----|
| Presná fráza (`"chocolate cake"`) | **S1** | 85% |
| Ingrediencie (`chicken + garlic`) | **S1** | 100% |
| Kuchyňa (`cuisine:italian`) | **S1** | 5% |
| Kombinované queries | **S1 = L2** | 75% |
| Štandardné multi-term | **S1** | 87.5% |

### Zhoda medzi Systémami (Overlap@5)

|  | S1 | S2 | L1 | L2 | FC |
|--|----|----|----|----|-----|
| **S1** | - | 18% | **30%** | 18% | 8% |
| **S2** | 18% | - | 8% | 8% | 0% |
| **L1** | 30% | 8% | - | **54%** | 10% |
| **L2** | 18% | 8% | 54% | - | 12% |
| **FC** | 8% | 0% | 10% | 12% | - |

**Zistenie:** Lucene indexy (L1, L2) majú najvyššiu zhodu medzi sebou (54%).

---

## 💡 Záver a Odporúčania

### Kľúčové Zistenia

1. **Simple BM25 (S1) je najlepší** na väčšinu typov queries
   - P@5 = 84% na štandardných queries
   - P@5 = 100% na ingredient filtering

2. **Food.com má problém so Zero-Result Rate**
   - 30% queries bez výsledkov
   - Tag-based systém zlyháva na frázach

3. **Lucene indexy sú najkonzistentnejšie**
   - 54% Overlap medzi L1 a L2
   - Vhodné pre produkčné nasadenie

4. **Cuisine filtering vyžaduje vylepšenie**
   - Aktuálne len 5% P@5
   - Potrebná implementácia faceted search

### Plánované Vylepšenia

1. **CLI podpora pre pokročilé query typy:**
   - `"exact phrase"` syntax
   - `ingredient:X -ingredient:Y` syntax
   - `cuisine:italian` faceted filtering

2. **Hybridný prístup:**
   - S1 pre textové vyhľadávanie
   - Lucene pre faceted filtering

3. **Query expansion:**
   - Synonym matching (pasta → spaghetti, linguine)
   - Ingredient substitution suggestions

