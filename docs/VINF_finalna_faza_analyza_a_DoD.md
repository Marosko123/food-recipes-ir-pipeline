
# VINF – Finálna fáza: čo spraviť a ako overiť (DoD checklist)

Autor: Maroš Bednár (xbednarm1)  
Projekt: **Recepty podľa jedla**  
Dátum: 25. 10. 2025  
Lokalita: Europe/Bratislava

---

## 1) Cieľ finálnej fázy (TL;DR)
Dodať **kompletnú IR pipeline** (crawler → parser/normalizácia → indexer + searcher → entity extrakcia + linking → Spark gazetteer → evaluácia) s reproducibilným behom cez `run.sh`, bez SQL databáz, s perzistenciou do súborov, s **≥ 500 MB dát** (vlastný crawl + enwiki subset/artefakty), unit testami a dokumentáciou (README + 3 strany na wiki + slidedeck).

---

## 2) Čo presne musí byť hotové (podľa špecifikácie zadania)
Nižšie sú **povinné výstupy** a požiadavky na kvalitu. Kde je to vhodné, uvádzam aj *odporúčané* vylepšenia.

### 2.1 Dáta
- **Crawl**: RAW HTML v `data/raw/{domain}/{doc_id}.html` (+ frontier, logy).  
- **Normalized**: `data/normalized/recipes.jsonl` (kľúče: `id, url, title, ingredients[], instructions[], times{prep,cook,total}, cuisine[], category[], tools[], yield, author, nutrition, ratings`).  
- **Index**: `index/v1/` (viď 2.3).  
- **Entities**: `entities/gazetteer_ingredients.tsv`, `entities/links.jsonl` (+ voliteľne `entities/gazetteer_cuisines.tsv`).  
- **Spark artefakty**: minimálne výstup gazetteera; voliteľne `entities/wiki_redirects.tsv`, `entities/wiki_stats.parquet`.  
- **Eval**: `eval/queries.tsv` (≥10 dotazov), `eval/qrels.tsv` (relevancie), výsledky metrík v TSV.

#### Požiadavky:
- **Objem dát ≥ 500 MB** (súčet vlastného crawlu + enwiki subset/artefakty).  
- **RAW dáta sa nikdy nemazú.**  
- Derivované výstupy sa môžu prepočítavať (deterministicky, s fixnými seedmi).

### 2.2 Crawler (food.com + interné linky na recepty)
- Rešpektuje `robots.txt`, má **throttle (QPS)**, **retries s exponenciálnym backoffom**, **deduplikáciu** (SHA1 URL), a **logovanie** do `data/crawl.log` (ideálne rotované).  
- CLI:  
  ```bash
  python -m crawler.run --seed https://www.food.com/recipe/chunky-chicken-nachos-138296 \
                        --limit 2000 --qps 0.5 --out data/raw
  ```
- Výstup: RAW HTML uložené podľa špecifikácie, frontier snapshot (ak je implementovaný), chybové logy.

### 2.3 Parser/normalizácia
- Primárne číta **JSON-LD Recipe (schema.org)**; fallback heuristiky pre ingrediencie/kroky.  
- Normalizuje časy z ISO-8601 → **minúty**.  
- Výstup do **JSONL** presne s definovanými kľúčmi.  
- CLI:  
  ```bash
  python -m parser.run --raw data/raw --out data/normalized/recipes.jsonl
  ```

### 2.4 Indexer + Searcher
- **Vlastný inverted index** s poľami `title`, `ingredients`, `instructions` (váhy polí).  
- **Dva rankery**: TF‑IDF (cosine) a BM25 (k≈1.2, b≈0.75).  
- Kombinované skóre naprieč poľami, **top‑k** výsledky, **snippety**.  
- Uloženie do TSV:  
  - `index/v1/terms.tsv` → `term \t df \t idf`  
  - `index/v1/postings.tsv` → `term \t field \t docId \t tf`  
  - `index/v1/docmeta.tsv` → `docId \t url \t title \t len_title \t len_ing \t len_instr`  
- CLI (index):  
  ```bash
  python -m indexer.run --input data/normalized/recipes.jsonl --out index/v1
  ```
- CLI (search):  
  ```bash
  python -m search_cli.run --index index/v1 --metric bm25 \
      --q "mexican chicken nachos" --k 10 \
      --filter '{"max_total_minutes":30,"cuisine":["Mexican"]}'
  ```

> **Poznámka k PyLucene:** Ak učiteľ **vyžaduje PyLucene** pre finálny index/search, doruč:
> - separátny CLI mód (napr. `--engine pylucene`) s rovnakou syntaxou dotazov/filtra, 
> - perzistenciu indexu do adresára (Lucene FSDirectory), 
> - rovnaké váhy polí a podporu BM25.  
> Referenčná vlastná implementácia ostáva kvôli evaluácii a transparentnosti.

### 2.5 Entity extrakcia a linking
- **Matcher (Aho‑Corasick)** nad gazetteerom.  
- **Linker**: zapisuje nájdené entity do `entities/links.jsonl` s pozíciami (`docId, field, start, end, surface, wiki_title`).  
- CLI výstupom je deterministický JSONL (stabilné triedenie).

### 2.6 Spark job(y) nad enwiki (bez SQL)
- Skript: `spark_jobs/build_gazetteer.py`  
- Vstup: `data/enwiki/` (dump/abstracty).  
- Úloha: postaviť **gazetteer ingrediencií** (a voliteľne kuchýň): `surface \t wiki_title \t norm`, rozriešiť **redirecty**, filtrovať **hlavný menný priestor**, heuristiky kategórií/infoboxov, generovať povrchové formy (titul, redirecty, lead).  
- CLI:  
  ```bash
  spark-submit spark_jobs/build_gazetteer.py \
      --wiki data/enwiki \
      --out entities/gazetteer_ingredients.tsv \
      --cuisines-out entities/gazetteer_cuisines.tsv
  ```

### 2.7 Evaluácia (IR metriky)
- Implementuj **P@k**, **Recall@k** (MAP/nDCG voliteľné).  
- Vstup: `eval/queries.tsv`, `eval/qrels.tsv`.  
- Výstup: `eval/results_{metric}.tsv` + krátky komentár porovnania **TF‑IDF vs. BM25**.  
- CLI:  
  ```bash
  python -m eval.run --index index/v1 --metric tfidf \
         --queries eval/queries.tsv --qrels eval/qrels.tsv \
         --out eval/results_tfidf.tsv
  ```

### 2.8 Dokumentácia a packaging
- `docs/README.md` – inštalácia, run.sh, štruktúra dát, príklady.  
- `docs/wiki_3pages.md` – 3‑stranový dokument (Problém & motivácia, Súčasné riešenia, Popis riešenia, Dáta, Vyhodnotenie, Spustenie).  
- `docs/slides_outline.md` – osnovy slidov.  
- `packaging/run.sh` – ciele: `crawl | parse | index | search | gazetteer | eval | all`, `set -e`, usage.  
- **ZIP balík** (LF konce, deterministické poradie súborov), **bez RAR**.  
- **Wiki publikácia** do **13. 12. 2025** (min. 2 dni pred odovzdaním).

### 2.9 Testy a kvalita
- Unit testy: `tests/` pre crawler, parser, index/search, entities, spark, eval.  
- `python -m <module> -h` funguje pre všetky moduly.  
- Logy v `data/*.log`, prípadne rotácia.  
- Reproducibilita: fixné seedy, stabilné triedenie, identické výstupy pri opakovaní.

---

## 3) Ako to zvalidovať – krok za krokom (checklisty + očakávané stopy)

> Tip: Validáciu rob v **čistom pracovnom adresári** s prázdnymi `data/normalized`, `index/v1`, `entities`, `eval/results_*`.

### 3.1 Rýchly „smoke test“ (E2E)
```bash
bash packaging/run.sh all
```
**Pass kritériá:**
- Skript dobehne bez erroru (návratový kód 0).  
- Vytvoria sa priečinky a súbory:  
  - `data/normalized/recipes.jsonl` (≥ N riadkov; N > 0)  
  - `index/v1/{terms.tsv,postings.tsv,docmeta.tsv}` (všetky existujú, `terms.tsv` ≥ 500 termov)  
  - `entities/gazetteer_ingredients.tsv` (≥ 10k riadkov pri plnom wikip dump; na demo stačí menšie)  
  - `entities/links.jsonl` (obsahuje aspoň 1 nájdenú entitu)  
  - `eval/results_tfidf.tsv`, `eval/results_bm25.tsv` (ak spúšťaš obe)  

### 3.2 Crawler
- Skontroluj `data/crawl.log` – sú v ňom záznamy o QPS a retrypokusoch.  
- Over deduplikáciu: hash rovnakých URL sa neopakuje v frontier.  
- Námatkovo otvorme 3–5 HTML v `data/raw/food.com/...` – obsahuje `<script type="application/ld+json">`.

### 3.3 Parser
```bash
python -m parser.run --raw data/raw --out data/normalized/recipes.jsonl
```
**Pass:**
- JSONL validný (každý riadok parsovateľný).  
- `times.total` je integer (minúty) a `== prep + cook`, ak sú k dispozícii.  
- Aspoň 90 % receptov má neprázdne `ingredients[]` a `instructions[]` (pri demo vzorke primerane).

### 3.4 Indexer/Searcher
```bash
python -m indexer.run --input data/normalized/recipes.jsonl --out index/v1
python -m search_cli.run --index index/v1 --metric bm25 --q "chicken nachos" --k 5
```
**Pass:**
- Vylistuje top‑5 s titulom, URL a snippetom bez tracebacku.  
- `terms.tsv` obsahuje stĺpce `term, df, idf` a `idf > 0` pre bežné termy.  
- `postings.tsv` má kombinácie polí (`title|ingredients|instructions`).

**Ak je povolený PyLucene mód:**
```bash
python -m search_cli.run --engine pylucene --metric bm25 --q "chicken nachos" --k 5
```
- Výsledky sú porovnateľné (nie nutne identické) s vlastným indexom; filtrácia a váhy polí fungujú.

### 3.5 Entities (matcher + linker)
```bash
python -m entities.matcher --gaz entities/gazetteer_ingredients.tsv --text "Chopped tomatoes and chickpeas"
python -m entities.linker --input data/normalized/recipes.jsonl --gaz entities/gazetteer_ingredients.tsv --out entities/links.jsonl
```
**Pass:**
- `matcher` nájde napr. „chickpeas → Chickpea“ (ilustratívne).  
- `links.jsonl` má polia: `docId, field, start, end, surface, wiki_title`.

### 3.6 Spark gazetteer
```bash
spark-submit spark_jobs/build_gazetteer.py --wiki data/enwiki --out entities/gazetteer_ingredients.tsv
```
**Pass:**
- Súbor existuje, hlavička/kľúče sú v správnom poradí (`surface \t wiki_title \t norm`).  
- Námatkovo 10 riadkov – `wiki_title` bez prefixov menného priestoru a bez cyklických redirectov.

### 3.7 Evaluácia
```bash
python -m eval.run --index index/v1 --metric tfidf --queries eval/queries.tsv --qrels eval/qrels.tsv --out eval/results_tfidf.tsv
python -m eval.run --index index/v1 --metric bm25  --queries eval/queries.tsv --qrels eval/qrels.tsv --out eval/results_bm25.tsv
```
**Pass:**
- Výstupné TSV majú formát `qid \t docId \t rank \t score`.  
- Report (krátky komentár) tvrdí a číslami dokazuje, že **BM25 ≥ TF‑IDF** aspoň v P@10 alebo Recall@10 pre väčšinu dotazov (ak nie, je to vysvetlené).

### 3.8 Dokumentácia a packaging
- `python -m <module> -h` na všetkých moduloch vypíše nápovedu bez tracebacku.  
- `docs/README.md` obsahuje presné príkazy na spustenie (vrátane Spark).  
- `docs/wiki_3pages.md` vyplnené (bez AI stôp, s ľudským štýlom a slovenskými úvodzovkami „“).  
- `packaging/run.sh` má ciele a `set -e`; `bash packaging/run.sh search --q "..."` funguje.

---

## 4) Kritériá akceptácie (Definition of Done)
- **Dáta ≥ 500 MB** (over cez `du -sh data`).  
- **E2E pipeline** z `run.sh all` prejde bez chyby na čistej inštalácii.  
- **Spark job** odvodí gazetteer zo stiahnutej Wikipédie (bez SQL).  
- **Entities/links.jsonl** existuje a pokrýva aspoň ingrediencie a kuchyne.  
- **Index + search**: TF‑IDF aj BM25; PyLucene mód (ak vyžadované).  
- **Evaluácia**: výsledky pre ≥ 10 dotazov, P@k a Recall@k exportované, krátky komentár porovnania.  
- **Testy**: všetky `tests/*` prejdú (`pytest` alebo `python -m`).  
- **Dokumentácia**: README + 3‑stranový dokument + slidedeck osnova; wiki publikované do 13. 12. 2025.  
- **ZIP** balík pripravený (bez RAR), deterministický a spustiteľný do 2–5 min s demo vzorkou.

---

## 5) Technológie a knižnice

### 5.1 Povolené (jadro projektu)
- **Python** (jadro), **Shell skripty**, **PySpark** (distribučné spracovanie Wikipédie).  
- Knižnice: `re, argparse, json, gzip, hashlib, pathlib, logging, requests, lxml` alebo `beautifulsoup4`, `ahocorasick`, `tqdm`, `pyspark` (ak je potrebné).

### 5.2 Odporúčané / povolené rozšírenia
- **PyLucene** pre finálne vyhľadávanie (ak učiteľ požaduje), pri zachovaní referenčnej vlastnej implementácie.  
- `zipfile` pre balenie (nie RAR).  
- Jednoduché util knižnice zo štandardnej knižnice Pythonu.

### 5.3 **Zakázané – určite nepoužívať**
- **SQL databázy** (MySQL, PostgreSQL, SQLite, atď.) – **žiadne** trvalé uloženie do DB.  
- **pandas**, **nltk**.  
- **RAR** archívy (iba **ZIP**).  
- Externé **SaaS vyhľadávače** (Algolia, Typesense cloud, atď.) ako primárny engine.  
- Plnotextové servery typu **Elasticsearch/Solr** ako náhrada implementácie; výnimka: **PyLucene**, ak je **výslovne povolený** učiteľom.  
- Ťažké ML/LLM frameworky na retrieval (napr. husté vektory, FAISS) – úloha je klasická IR TF‑IDF/BM25.  
- Krehké XPath viazané na presnú štruktúru HTML (používaj JSON‑LD a robustné heuristiky).

---

## 6) Najčastejšie chyby a ako im predísť
- **Mazanie RAW dát** – nikdy ich nemaž, regeneruj len derivované vrstvy.  
- **Nedeterministické zoradenie** – zafixuj seedy a stabilné triedenie (tie‑break podľa `docId`).  
- **Zlý parsing času** – vždy konvertuj ISO‑8601 na minúty; kontrola `prep + cook == total`.  
- **Nepriehľadná evaluácia** – archivuj `eval/results_*.tsv` a uveď presný príkaz, ktorým si metriky získal.  
- **Chýbajúce -h** – každý modul musí mať `-h`.  
- **Veľký Spark run bez filtra** – filtruj na hlavný menný priestor + kategórie; pred plným behom testuj na vzorke.

---

## 7) Rýchla „pre‑release“ kontrola (checklist)
- [ ] `du -sh data` ≥ 500 MB  
- [ ] `bash packaging/run.sh all` prebehne bez chyby  
- [ ] `entities/gazetteer_ingredients.tsv` existuje, má rozumný objem  
- [ ] `entities/links.jsonl` existuje, obsahuje nájdené entity  
- [ ] `python -m search_cli.run --metric bm25 --q "chicken" --k 5` vracia výsledky so snippetmi  
- [ ] `python -m eval.run ...` vygeneruje P@10/Recall@10 TSV  
- [ ] `pytest` alebo `python -m` testy prejdú  
- [ ] README, 3‑strany na wiki, slidedeck osnova sú hotové  
- [ ] ZIP balík pripravený (bez RAR), run.sh funkčný

---

## 8) Referenčné príkazy (kopírovať & spustiť)
```bash
# Crawl
python -m crawler.run --seed https://www.food.com/recipe/chunky-chicken-nachos-138296 --limit 2000 --qps 0.5 --out data/raw

# Parse
python -m parser.run --raw data/raw --out data/normalized/recipes.jsonl

# Index
python -m indexer.run --input data/normalized/recipes.jsonl --out index/v1

# Search
python -m search_cli.run --index index/v1 --metric bm25 --q "mexican chicken nachos" --k 10 --filter '{"max_total_minutes":30,"cuisine":["Mexican"]}'

# Spark gazetteer
spark-submit spark_jobs/build_gazetteer.py --wiki data/enwiki --out entities/gazetteer_ingredients.tsv --cuisines-out entities/gazetteer_cuisines.tsv

# Entities
python -m entities.linker --input data/normalized/recipes.jsonl --gaz entities/gazetteer_ingredients.tsv --out entities/links.jsonl

# Eval
python -m eval.run --index index/v1 --metric tfidf --queries eval/queries.tsv --qrels eval/qrels.tsv --out eval/results_tfidf.tsv
python -m eval.run --index index/v1 --metric bm25  --queries eval/queries.tsv --qrels eval/qrels.tsv --out eval/results_bm25.tsv
```

---

## 9) Poznámky k termínom (2025)
- 31. 10.: E2E na vzorke, základná evaluácia, CLI filtre.
- 14. 11.: ≥ 500 MB dát, Spark gazetteer, linking v2.
- 28. 11.: Spark hotový, širšia evaluácia, draft 3‑stranového dokumentu.
- 05. 12.: hotový softvér, slidedeck draft, ZIP + run.sh, finálne metriky.
- **13. 12.: zverejniť dokument a slidedeck na wiki (min. 2 dni pred).**
- 15. 12.: odovzdanie (hard deadline).

---

### Koniec dokumentu
