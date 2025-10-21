# Recepty podľa jedla – Súhrn odovzdávok (Projekt 1 vs. Projekt 2)

Tento dokument presne sumarizuje, čo musí byť hotové v **1. projekte** (1. polovica semestra) a čo v **2. projekte** (2. polovica). Obsahuje termíny, povinné artefakty, cesty súborov, demo kroky a pravidlá (čo áno/nie).

---

## 1) Prvý projekt (1. polovica semestra) — **do 31.10.2025**

### A. Čo má byť **na wiki** (publikované)
- **TL;DR + motivácia** (max 1 strana).
- **Zdroj dát (web):** `https://www.food.com/recipe?ref=nav` + **polia**: `ingredients`, `instructions`, `description`, `ratings{value,count}`, `difficulty`, `times{total,prep,cook}`, `keywords/tags`, `yield`, `author`, `cuisine/category/tools`, `nutrition`.
- **Zdroj dát (Wikipedia EN dumps):** `https://dumps.wikimedia.org/enwiki/latest/` + krátka **ukážka (100 riadkov)** z *all-titles-in-ns0.gz* na wiki.
- **Min. 5 párov Q&A** (typické dopyty a očakávané odpovede systému).
- **Architektúra & flow + pseudokód** (crawler → parser → index → search).
- **Demo & štatistiky** (stav crawlu, veľkosť dát, ukážky JSONL, ukážky vyhľadávania).

### B. Kód a artefakty (repo / ZIP)
- **Crawler** (robots.txt, QPS≈0.5, retries/backoff, deduplikácia URL):
  - RAW HTML → `data/raw/food.com/<doc_id>.html`
  - Log → `data/crawl.log` (timestamp, URL, status, bytes, duration)
- **Parser/normalizácia**:
  - JSON‑LD Recipe (preferované) + fallback heuristiky/REGEX.
  - Časy ISO‑8601 → **minúty** (int).
  - Výstup → `data/normalized/recipes.jsonl` (1 recept = 1 riadok).
- **Indexer (vlastný inverted index)**:
  - Polia + váhy: `title=3.0`, `ingredients=2.0`, `instructions=1.0`.
  - Artefakty:
    - `index/v1/terms.tsv`  – `term \t df \t idf_log(N/df) \t idf_bm25`
    - `index/v1/postings.tsv` – `term \t field \t docId \t tf`
    - `index/v1/docmeta.tsv`  – `docId \t url \t title \t len_title \t len_ing \t len_instr`
- **CLI vyhľadávač**:
  - Prepínače: `--metric tfidf|bm25`, `--q "..."`, `--k 10`
  - **Filtre**: `--filter '{"max_total_minutes":30,"cuisine":["Mexican"]}'`
  - Snippety (zvýraznenie termov).
- **(Odporúčané) Mini‑lookup na wiki tituly** (z *all‑titles‑in‑ns0.gz* + voliteľne DBpedia redirects) – jednoduché streamovanie, bez pandas/SQL.
- **packaging/run.sh** (s `set -e` a cieľmi):
  - `crawl | parse | index | search | eval | all` (a `-h` pre každý modul).

### C. Dáta a štatistiky (čo ukážeš)
- Počet stiahnutých HTML (napr. ~5600+), veľkosť na disku: `du -sh data/raw`.
- Počet riadkov v `data/normalized/recipes.jsonl`.
- Ukážky: 1–2 recepty (JSONL), 100‑riadkový sample *titles* z Wikipédie.
- Porovnanie TF‑IDF vs. BM25 aspoň na pár dotazoch (plná evaluácia v 2. projekte).

### D. Demo (2–5 min)
1. `bash packaging/run.sh index` (alebo ukáž existujúci index).
2. `bash packaging/run.sh search -- "mexican chicken nachos" --metric bm25 --k 5`.
3. Otvor `data/normalized/recipes.jsonl` (1–2 záznamy; skontroluj `times.total` v minútach).
4. `du -sh data/raw` + počty HTML.
5. Na wiki ukáž: TL;DR, Architektúra & pseudokód, Demo & štatistiky, Q&A.

### E. Pravidlá (povolené / zakázané / pozor)
- **Povolené:** Python, Shell; knižnice: `re, argparse, json, gzip, hashlib, pathlib, logging, requests, lxml/bs4, ahocorasick, tqdm`.
- **Zakázané:** SQL databázy, **pandas**, **NLTK**, **RAR** (používaj ZIP).
- **Pozor:** Nekrehké selektory (radšej JSON‑LD + robustné fallbacky), **RAW sa nikdy nemaž**, časy drž **v minútach** jednotne.

### F. Termíny (1. projekt)
- **03.10.2025 – Konzultácia 1:** Wiki TL;DR + linky (Food.com, ENwiki dumps) + 5× Q&A.
- **17.10.2025 – Konzultácia 2:** Wiki architektúra & pseudokód; **PoC crawler** + pár stránok.
- **31.10.2025 – Odovzdanie 1. časti:** Crawler hotový + štatistiky; **extraktor** (JSON‑LD + fallback) + ukážky; **indexer + CLI searcher** (TF‑IDF & BM25). *(BONUS: unit testy extrakcií ~20 stránok).*

---

## 2) Druhý projekt (2. polovica semestra) — **14.11.2025 → 15.12.2025**

### A. Wikipedia obohatenie + Spark
- **ENwiki dumps:** *all‑titles‑in‑ns0.gz* (a ideálne *redirects*; príp. DBpedia redirects/short‑abstracts).
- **Spark gazetteer job (PySpark):**
  - Vstup: titles (+ redirects).
  - Výstup TSV/Parquet: `entities/gazetteer_wiki.tsv` – polia: `surface`, `wiki_title`, `norm` (lowercase, `_`→` `, trim).
- **Entity matching & linking:**
  - Aho‑Corasick nad gazetteerom.
  - Zápis: `entities/links.jsonl` – `docId`, `field`, `start`, `end`, `surface`, `wiki_title`.
- *(Voliteľné)* **Short abstracts** (DBpedia) → Parquet `(title, abstract)` na offline „pôvod/históriu“ jedla.

### B. Škálovanie a behy na väčších dátach
- **≥ 500 MB – 1+ GB** spracovaných dát (Food.com + Wikipedia artefakty).
- Pipeline na väčšom vstupe/na celku: crawl → parse → index → search + entities/linking.
- **GitHub** repozitár (podľa pokynov cvičiaceho) s funkčným kódom.

### C. Evaluácia a odovzdanie
- **Evaluácia** (≥10 dotazov): **P@k** a **Recall@k** (porovnanie **TF‑IDF vs. BM25**) + krátky komentár.
- **Slidy** + **ZIP** so softvérom (demo dáta) pridané na wiki.
- **README**: inštalácia/spustenie, ukážkové príkazy.
- **Wiki (max 1 strana)**: čo / ako / overenie (precision/recall) / spustenie. **Zverejniť do 13.12.2025** (min. 2 dni pred).

### D. Demo (2–5 min, finále)
1. `run.sh index` + `run.sh search "..." --metric bm25` (top‑k + filtre).
2. Ukáž **entity linking**: recept → nájdené wiki tituly (+ voliteľne krátky abstract).
3. Otvor **tabuľku metrík** (P@k/Recall@k) a zhrň rozdiel TF‑IDF vs. BM25.
4. Ukaž, kde je **ZIP + README + slidy** na wiki.

### E. Pravidlá (povinné / zakázané / pozor)
- **Povinné:** Spark job(y), entity linking, väčší objem dát, evaluácia metrík.
- **Zakázané:** SQL DB, pandas, NLTK, RAR; **RAW sa nikdy nemaž**.
- **Pozor:** licencia a atribúcia (Wikipedia/DBpedia – CC BY‑SA); **reproducibilita** (`run.sh`), stabilné triedenie, deterministické výsledky.

### F. Termíny (2. projekt)
- **14.11.2025 – Konzultácia 3:** rozšírený kód na väčších dátach (môže už Spark), smerom k gazetteeru.
- **28.11.2025 – Konzultácia 4:** takmer hotové (Spark **musí byť**), testy na celých dátach (Food.com + Wikipedia).
- **05.12.2025 – Konzultácia 5:** hotový softvér + metriky + slidy + ZIP, demo 2–5 min.
- **13.12.2025 – Zverejnenie na wiki:** dokument + slidy (min. 2 dni pred).
- **15.12.2025 – Hard deadline:** finálne odovzdanie.

---

## 3) Rýchly kontrolný zoznam (na odškrtávanie)

### 1. projekt (do 31.10.2025)
- [ ] Wiki: TL;DR + linky + Q&A  
- [ ] Wiki: Architektúra & pseudokód  
- [ ] Crawler hotový + štatistiky  
- [ ] Parser (JSON‑LD + fallback) → `data/normalized/recipes.jsonl`  
- [ ] Indexer + CLI vyhľadávač (TF‑IDF & BM25)  
- [ ] Demo (2–5 min) + ZIP

### 2. projekt (14.11. → 15.12.2025)
- [ ] Spark gazetteer (titles + redirects) → TSV/Parquet  
- [ ] Aho‑Corasick matching → `entities/links.jsonl`  
- [ ] Väčšie dáta spracované (≥500 MB–GB)  
- [ ] Evaluácia P@k/Recall@k (≥10 dotazov)  
- [ ] Slidy + ZIP + README na wiki  
- [ ] Zverejnené do 13.12. a finálne odovzdané 15.12.

---

**Pozn.:** Čokoľvek, čo **nie je na wiki**, sa považuje za **neexistujúce**. Drž všetko stručné a spustiteľné do **2–5 min** (ZIP + `run.sh`).  
