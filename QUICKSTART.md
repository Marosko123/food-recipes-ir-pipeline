# 🚀 Quick Start Guide

**Food Recipes Information Retrieval Pipeline**  
Autor: Maroš Bednár (AIS 116822)

---

## 📋 Predpoklady

```bash
# Python 3.x + pip
python3 --version

# Nainštaluj závislosti
pip3 install -r packaging/requirements.txt
```

---

## ⚡ Rýchly štart (5 minút)

### 1️⃣ Stiahni recepty (100 kusov pre demo)

```bash
./packaging/run.sh crawl 100
```

**Výstup:** `data/raw/www.food.com/*.html` (raw HTML súbory)

---

### 2️⃣ Parsuj HTML → JSON

```bash
./packaging/run.sh parse
```

**Výstup:** `data/normalized/recipes.jsonl` (štruktúrované dáta)

---

### 3️⃣ Vytvor index

```bash
./packaging/run.sh index
```

**Výstup:** `data/index/v1/` (terms.tsv, postings.tsv, docmeta.tsv)

---

### 4️⃣ Vyhľadávaj

```bash
# Základné vyhľadávanie (BM25)
./packaging/run.sh search "chicken pasta"

# Ďalšie príklady
./packaging/run.sh search "chocolate dessert"
./packaging/run.sh search "italian pasta"
./packaging/run.sh search "healthy salad"
```

---

### 5️⃣ Demo pre učiteľa (10 Q&A scenárov)

```bash
bash packaging/cli_examples.sh
```

**Ukáže 10 realistických scenárov:**
- Rýchle kuracie jedlo do 30 min
- Talianske cestoviny do 45 min
- Zdravý šalát s vysokým proteínom
- Čokoládový dezert pre oslavu
- Mexická kuchyňa (rýchlo)
- Ľahká polievka (nízke kalórie)
- Rýchle raňajky do 15 min
- Vegetariánske cestoviny
- Večera s vysokým proteínom
- Porovnanie TF-IDF vs BM25

---

## 🔍 Pokročilé vyhľadávanie

### S filtrami (čas, hodnotenie, kalórie)

```bash
# Rýchle kuracie jedlo (≤30 min, hodnotenie ≥4.0)
python3 search_cli/run.py \
    --index data/index/v1 \
    --metric bm25 \
    --q "chicken" \
    --k 5 \
    --filter '{"max_total_minutes": 30, "min_rating": 4.0}'

# Zdravý šalát (≤400 cal, ≥15g proteín)
python3 search_cli/run.py \
    --index data/index/v1 \
    --metric bm25 \
    --q "salad" \
    --k 5 \
    --filter '{"max_calories": 400, "min_protein": 15}'
```

### Porovnanie TF-IDF vs BM25

```bash
# TF-IDF (normalized scores 0-1)
python3 search_cli/run.py \
    --index data/index/v1 \
    --metric tfidf \
    --q "pasta carbonara" \
    --k 5

# BM25 (Okapi BM25, unbounded scores)
python3 search_cli/run.py \
    --index data/index/v1 \
    --metric bm25 \
    --q "pasta carbonara" \
    --k 5
```

---

## 🛠️ Centrálny entrypoint

Všetky príkazy sú dostupné cez `./packaging/run.sh`:

```bash
# Ukáž help
./packaging/run.sh help

# Spusti celý pipeline (crawl→parse→index)
./packaging/run.sh all 100

# Vyčisti všetko a začni odznova
./packaging/run.sh clean
./packaging/run.sh crawl 100
./packaging/run.sh parse
./packaging/run.sh index
```

---

## 📚 Dostupné filtre

| Filter | Typ | Príklad |
|--------|-----|---------|
| `max_total_minutes` | int | `30` (jedlá do 30 min) |
| `max_prep_minutes` | int | `15` (príprava do 15 min) |
| `max_cook_minutes` | int | `20` (varenie do 20 min) |
| `min_rating` | float | `4.0` (hodnotenie ≥4.0★) |
| `min_rating_count` | int | `10` (min. 10 hodnotení) |
| `max_calories` | int | `400` (≤400 cal) |
| `min_protein` | int | `15` (≥15g proteín) |
| `max_fat` | int | `20` (≤20g tuk) |
| `required_ingredients` | list | `["chicken", "pasta"]` |
| `excluded_ingredients` | list | `["nuts", "shellfish"]` |
| `cuisines` | list | `["Italian", "Mexican"]` |
| `categories` | list | `["Dessert", "Main Dish"]` |

**Kombinuj filtre podľa potreby!**

---

## 📖 Dokumentácia

### Pre učiteľa (odovzdávka Phase 1):
- **`README_First_Submission.md`** - Kompletný prehľad Phase 1
  - Systémová architektúra
  - Pseudokód (indexer + search)
  - TF-IDF a BM25 vysvetlenie
  - Demo scenáre
  - Štatistiky (5,646 receptov, 9,822 termov, 444,130 postingov)

- **`docs/DEMO_GUIDE.md`** - Krok-za-krokom prezentačný návod (20 min)

### Pre developera:
- **`docs/CLI_GUIDE.md`** - Kompletná referencia CLI (5000+ riadkov)
- **`search_cli/README.md`** - Rýchly prehľad CLI

### Príklady:
- **`packaging/cli_examples.sh`** - 10 Q&A demo scenárov (spustiteľné)

---

## ❓ Časté problémy

### "Index not found"
```bash
./packaging/run.sh index
```

### "Normalized data not found"
```bash
./packaging/run.sh parse
```

### "Raw data not found"
```bash
./packaging/run.sh crawl 100
```

### Chýbajúce závislosti
```bash
pip3 install -r packaging/requirements.txt
```

### Vyčistiť všetko a začať odznova
```bash
./packaging/run.sh clean
./packaging/run.sh all 100
```

---

## 🎯 Súhrn pre Phase 1 odovzdávku

```bash
# 1. Kompletný pipeline
./packaging/run.sh all 100

# 2. Ukázka vyhľadávania
./packaging/run.sh search "chicken pasta"

# 3. Demo pre učiteľa (10 Q&A scenárov)
bash packaging/cli_examples.sh

# 4. Prečítaj dokumentáciu
cat README_First_Submission.md
cat docs/DEMO_GUIDE.md
```

**✅ Všetko je pripravené na odovzdávku!**

---

## 📞 Kontakt

**Autor:** Maroš Bednár  
**AIS ID:** 116822  
**Email:** bednarmaros341@gmail.com  
**Kurz:** VINF (Information Retrieval)  
**Deadline:** 31. október 2025
