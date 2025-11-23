# Špecifikácia projektu – Vyhľadávanie receptov z Food.com s obohatením z Wikipédie

## 1. Cieľ a kontext projektu

Cieľom projektu je vybudovať **kompletný systém na vyhľadávanie informácií** nad dátami z portálu **Food.com** (recepty) obohatenými o informácie z **Wikipédie**. Systém musí pokrývať celý typický IR pipeline:

1. **Crawler** – stiahnutie HTML stránok z Food.com (už je čiastočne hotové).
2. **Parser / extraktor entít** – spracovanie HTML do štruktúrovaných dát (recepty, ingrediencie, hodnotenia, kategórie…)
3. **Vlastný jednoduchý indexer a searcher** – implementovaný v Pythone (bez Lucene), s **minimálne 2 rôznymi metódami IDF/rankingu**.
4. **Práca s veľkými dátami (Spark)** – spracovanie Food.com dát a **Wikipédia dumpu** na distribuovanej architektúre.
5. **Join Food.com + Wikipedia** – spojenie receptov s relevantnými wiki stránkami (napr. suroviny, kuchyne, techniky varenia).
6. **Finálny index pomocou PyLucene** – profesionálnejší index a searcher, ktorý nahradí prvotný vlastný index.
7. **Vyhodnotenie úspešnosti** – aspoň na malej sade ručne označených dopytov: precision, recall (príp. precision@k).
8. **Dokumentácia, wiki, prezentácia, kód** – podľa požiadaviek predmetu.

Dokument slúži ako **pracovná špecifikácia pre implementačného agenta**, ktorý na jej základe:
- skontroluje existujúci kód,
- doplní chýbajúce časti,
- zjednotí formáty dát,
- pripraví všetky povinné artefakty na odovzdanie.

---

## 2. Dáta

### 2.1 Food.com

- Primárny dataset je z portálu **Food.com**.
- Už existuje približne **5600 stiahnutých HTML stránok** (každá reprezentuje buď recept, alebo inú podstránku).
- Cieľ: vytvoriť z týchto HTML **štruktúrovanú tabuľku receptov**.

Minimálne extrahované polia (entity):
- `recipe_id` – interné ID (napr. hash URL alebo číslo z URL),
- `url` – pôvodný odkaz,
- `title` – názov receptu,
- `ingredients` – zoznam ingrediencií (1 stĺpec, záznam oddelený napr. `|||` alebo JSON),
- `directions` – text postupu varenia (string; môže byť viac odsekov spojených `\n`),
- `rating` – číselné hodnotenie, ak existuje,
- `review_count` – počet recenzií, ak existuje,
- `categories` – kategórie / tagy receptu (napr. „Italian“, „Dessert“…),
- `cuisine` – typ kuchyne, ak je dostupný,
- `prep_time`, `cook_time`, `total_time` – ak sú k dispozícii,
- `servings` – počet porcií,
- `metadata` – ďalšie polia, ktoré sú ľahko extrahovateľné (napr. autor, dátum, nutričné hodnoty).

Výstupný formát Food.com dát:
- Použiť **TSV** (tab-separated values) alebo **JSON lines**.
- Príklad: `recipes_foodcom.tsv`
  - Prvý riadok – hlavička s názvami stĺpcov.
  - Každý ďalší riadok – jeden recept.

### 2.2 Wikipedia

- Použije sa **Wikipédia dump (EN)** – ideálne kompletný dump, minimálne však dáta potrebné na obohatenie receptov.
- Z Wikipédie treba extrahovať:
  - `page_id`,
  - `title`,
  - `redirects` (presmerovania),
  - `abstract` alebo prvý odsek,
  - `categories` (wiki kategórie),
  - `links_out` (odkazy na iné stránky),
  - prípadne ďalšie polia využiteľné pre semantické vyhľadávanie.

Výstupný formát Wiki dát:
- Ideálne **parquet** alebo **TSV** po spracovaní v Sparku:
  - napr. `wiki_pages.tsv` alebo `wiki_pages.parquet`.

### 2.3 Spojené dáta (Food.com + Wikipedia)

- Po joine vznikne dataset:
  - `recipe_id`, `url`, `title`, `ingredients`, `directions`, `rating`, ... (Food.com)
  - `wiki_concepts` – zoznam priradených wiki stránok (napr. ingrediencie, kuchyne),
  - `wiki_abstracts` – skrátené popisy z príslušných wiki stránok,
  - `wiki_categories` – zjednotená množina kategórií z Wikipédie.

Výstupný súbor napr. `recipes_joined.tsv` alebo `recipes_joined.parquet`.

Dôležité:
- Súčet spracovaných dát (Food.com + Wikipedia) musí byť **≥ 500 MB**, ideálne niekoľko GB.
- AI agent musí skontrolovať reálnu veľkosť na disku a doplniť tak, aby bola splnená podmienka kurzu.

---

## 3. Technológie – čo použiť a čo nie

### 3.1 Odporúčané technológie

**Programovací jazyk:**
- Primárne **Python 3.x**.

**Knižnice pre crawling a HTTP:**
- `requests` – hlavná knižnica na HTTP requesty,
- `selenium` – len ak je potrebné renderovanie JavaScriptu (pravdepodobne bude stačiť `requests`).

**Spracovanie textu:**
- `re` – regulárne výrazy na extrakciu dát z HTML a wiki dumpu,
- prípadne `html` modul (na unescape),
- jemne je možné použiť `BeautifulSoup` alebo podobný parser, ale **extrakcia kritických polí by mala byť riešená cez regexy** (podľa zadania sa kladie dôraz na regulárne výrazy).

**Distribuované spracovanie:**
- **Apache Spark** (PySpark) – povinný v druhej polovici semestra.
  - Použitie RDD alebo DataFrames (podľa potreby).

**Indexovanie a vyhľadávanie:**
- 1. fáza: vlastný jednoduchý index v Pythone (slovníky, súbory, atď.).
- 2. fáza: **PyLucene** – odporúčané pre finálny index.

### 3.2 Zakázané alebo neodporúčané technológie

- **SQL databázy – ZAKÁZANÉ** (MySQL, PostgreSQL, SQLite atď.).
  - Všetko ukladať do textových formátov: TSV, CSV, JSON (resp. JSON Lines), prípadne Parquet cez Spark.
- **Pandas – NEPOUŽÍVAŤ.**
- **NLTK – NEPOUŽÍVAŤ** (resp. len minimálne a len pre angličtinu; radšej vôbec nie, tu nie je potrebná).
- **XPath a extrakcia podľa presnej štruktúry HTML – NEPOUŽÍVAŤ.**
  - Výučbový dôraz je na regulárnych výrazoch a robustnom spracovaní textu.
- **RAR archívy – NEPOUŽÍVAŤ.**
  - Používať **ZIP**.

### 3.3 Odporúčané dátové formáty

- **TSV (tab-separated values)** – pre štruktúrované tabulárne dáta.
- **JSON / JSON Lines** – pre komplexnejšie štruktúry (zoznamy ingrediencií, objekty, atď.).
- **Parquet** – pre efektívne ukladanie veľkých dát v Sparku.

AI agent musí skontrolovať, že aktuálne implementované časti používanú iba povolené technológie, a ak nájde Pandas, SQL, NLTK alebo XPath, musí ich odstrániť/nahradiť.

---

## 4. Architektúra systému

### 4.1 Prehľad modulov

Systém bude rozdelený na nasledujúce logické moduly:

1. `crawler/` – sťahovanie HTML stránok Food.com.
2. `parser/` – extrakcia entít z HTML (Food.com) pomocou regexov.
3. `indexer_basic/` – jednoduchý, vlastný textový index (TF + 2 metódy IDF).
4. `searcher_basic/` – jednoduchý vyhľadávač nad vlastným indexom (CLI).
5. `spark_job/` – Spark úlohy na spracovanie veľkých dát (Food.com + Wikipedia, join).
6. `pylucene_index/` – generovanie Lucene indexu.
7. `pylucene_search/` – finálny vyhľadávač (CLI) nad Lucene indexom.
8. `evaluation/` – skripty na hodnotenie (precision, recall, štatistiky).
9. `utils/` – spoločné pomocné funkcie, logovanie, načítanie konfigurácie.

### 4.2 Crawler (Food.com)

Úloha:
- Stiahnuť a uložiť HTML stránky z Food.com.
- Zabezpečiť:
  - **User-Agent** hlavičku (simulácia normálneho prehliadača),
  - **timeout**,
  - **sleep** medzi requestami (politeness),
  - logovanie chýb (HTTP 4xx/5xx).

Výstup:
- Súborová štruktúra:
  - napr. `data/raw/foodcom/{recipe_id}.html`
- Zoznam URL a meta-dát (TSV/CSV/JSON) – napr. `data/urls_foodcom.tsv`.

### 4.3 Parser / extraktor entít

Úloha:
- Z každého HTML súboru extrahovať spomenuté polia (title, ingredients, directions, atď.) pomocou **regexov**.
- Implementovať viaceré regulárne výrazy a unit testy tak, aby boli robustné voči menším zmenám HTML.

Výstup:
- `data/processed/recipes_foodcom.tsv` – štruktúrovaný dataset receptov.

### 4.4 Vlastný indexer a searcher

Úloha:
- Implementovať **jednoduchý inverted index** v Pythone.

Index by mal obsahovať:
- slovník term → zoznam (document_id, term_frequency),
- pre každý dokument:
  - `doc_id`,
  - `title`,
  - `url`,
  - textové polia na indexovanie (napr. title + ingredients + directions),
  - pomocné metadáta (dĺžka dokumentu, rating…).

Ranking:
- Implementovať **minimálne 2 rôzne metódy výpočtu IDF/rankingu**, napr.:
  1. Klasický **TF-IDF**: `score = tf * log(N / df)`.
  2. Alternatívny variant: napr. `score = tf * log(1 + N / (1 + df))` alebo jednoduchá verzia **BM25-like**.

Searcher (CLI):
- Prijme textový dopyt, napr. `"chicken curry with coconut"`.
- Prevedie dopyt na tokeny.
- Vyhľadá relevantné dokumenty v indexe.
- Zoradí dokumenty podľa zvolenej metriky.
- Vypíše top-k výsledkov (napr. 10), vrátane:
  - `rank`, `score`, `title`, `url`, krátky výňatok textu.
- Musí podporovať přepínanie medzi aspoň dvomi metrikami.

### 4.5 Spark – spracovanie veľkých dát a join s Wikipédiou

Úloha:
- Prejsť z lokálneho spracovania na distribuované pomocou **Apache Spark**.
- Spracovať:
  - Food.com recepty (už vyextrahované),
  - Wikipedia dump.
- Implementovať **join** medzi Food.com a Wikipédiou.

Join (príklad):
- Pre každý recept z Food.com:
  - z ingrediencií a kategórií extrahovať možné názvy entity (napr. „garlic“, „Italian cuisine“, „pasta“),
  - mapovať tieto názvy na wiki stránky podľa `title` a `redirects`.

Výstup joinu:
- DataFrame / RDD s obohateným receptom + wiki informáciami.
- Uložiť do `recipes_joined.parquet` alebo `recipes_joined.tsv`.

### 4.6 PyLucene index a searcher

Úloha:
- Použiť **PyLucene** na vytvorenie plnohodnotného indexu.

Indexované polia (Lucene Fields):
- `recipe_id` – stored, not_analyzed,
- `title` – tokenized, stored,
- `ingredients` – tokenized, stored,
- `directions` – tokenized, stored,
- `wiki_concepts` – tokenized, stored,
- `rating`, `review_count` – numeric fields, stored,
- `cuisine`, `categories` – tokenized, stored.

Searcher (CLI):
- Podporované dopyty:
  - **Boolean queries** – AND/OR medzi slovami,
  - **Phrase queries** – napr. "chicken soup",
  - voliteľne **Fuzzy queries** (napr. tolerantné na preklepy),
  - **Field-specific queries** – napr. vyhľadávať len v ingredienciách.

Porovnanie:
- Implementovať možnosť porovnania výsledkov medzi **vlastným indexom** a **Lucene indexom** na tých istých dopytoch (manuálne aj tabulkovo).

### 4.7 Vyhľadávacie rozhranie (CLI)

Minimálne požiadavky:
- Spustiteľný skript, napr. `python search_cli.py --engine basic` alebo `--engine lucene`.
- Interaktívny režim: používateľ zadá query, systém vráti výsledky.
- Podpora výberu rankingovej metódy (pri vlastnom indexeri).

---

## 5. Podrobná špecifikácia pre implementačného agenta

Nasledujúce podsekcie sú priamy TODO/Checklist pre AI agenta.

### 5.1 Modul A – Crawler

**Úloha:**
- Skontrolovať existujúci crawler a zabezpečiť, že spĺňa požiadavky predmetu.

**Vstupy:**
- Základný zoznam URL (seed), napr. homepage Food.com alebo konkrétne kategórie.

**Výstupy:**
- `data/raw/foodcom/{recipe_id}.html` – stiahnuté HTML.
- `data/urls_foodcom.tsv` – zoznam URL + status.

**Požiadavky:**
1. Používať `requests`, nie Pandas, nie SQL.
2. Nastaviť HTTP hlavičky:
   - `User-Agent`: string typu "Mozilla/5.0 ...".
3. Nastaviť `timeout` (napr. 10 sekúnd).
4. Nastaviť `sleep` medzi requestami (napr. 0.5–2 sekundy), aby sa nepreťažoval server.
5. Logovanie:
   - úspešné a neúspešné requesty (HTTP status, URL).
6. Žiadne použitie RAR, len ZIP.

**Kontrolné kroky:**
- [ ] Overiť, či existuje modul `crawler`.
- [ ] Overiť, že sa nevyužíva XPath.
- [ ] Overiť, že výstupy sú uložené v definovanej štruktúre.

### 5.2 Modul B – HTML parser & extraktor entít

**Úloha:**
- Extrahovať potrebné informácie z HTML stránok do TSV.

**Vstupy:**
- HTML súbory z `data/raw/foodcom/`.

**Výstupy:**
- `data/processed/recipes_foodcom.tsv`.

**Požiadavky:**
1. Používať **regulárne výrazy** (`re` modul) pre kľúčové časti extrakcie.
2. Nepoužívať XPath.
3. Ak je použitý parser (BeautifulSoup), regexy musia mať centrálnu úlohu pri extrakcii konkrétnych polí.
4. Pre každé pole (title, ingredients, directions, rating, categories, ...) mať jasne definované regexy.
5. Riešiť edge cases (chýbajúce polia, neúplné HTML, rôzne varianty štruktúry).

**Kontrolné kroky:**
- [ ] Skontrolovať, že existuje skript, ktorý iteruje cez všetky HTML a generuje TSV.
- [ ] Skontrolovať, že TSV má hlavičku a všetky požadované stĺpce.
- [ ] Skontrolovať, že kód ignoruje alebo loguje chybné súbory, ale nespadne.

### 5.3 Modul C – Unit testy na regexy (BONUS, odporúčané)

**Úloha:**
- Urobiť aspoň základné unit testy, ktoré overujú správnosť regexov pre extrakciu.

**Požiadavky:**
- Aspoň **20 HTML stránok**.
- Testy overia:
  - správnu extrakciu názvu,
  - extrakciu ingrediencií,
  - extrakciu directions,
  - extrakciu ratingu a review_count.

**Kontrolné kroky:**
- [ ] Skontrolovať, či existuje priečinok `tests/` alebo podobný.
- [ ] Spúšťanie testov jedným príkazom (napr. `pytest` alebo `python -m unittest`).

### 5.4 Modul D – Vlastný indexer

**Úloha:**
- Implementovať jednoduchý inverted index nad Food.com receptami.

**Vstupy:**
- `recipes_foodcom.tsv` alebo `recipes_joined.tsv` (v neskoršej verzii).

**Výstupy:**
- súbory s indexom, napr.:
  - `index_basic/lexicon.json` – mapovanie term → term_id,
  - `index_basic/postings.bin` alebo `.json` – zoznam postingov,
  - `index_basic/documents.tsv` – meta-dáta dokumentov.

**Požiadavky:**
1. Tokenizácia textu – jednoduchá (split podľa whitespace + odstránenie interpunkcie).
2. Normalizácia – napr. lowercasing.
3. Výpočet TF (term frequency) pre každý dokument a term.
4. Implementácia **2 metód IDF/rankingu**.

**Kontrolné kroky:**
- [ ] Indexer spustiteľný jedným skriptom (napr. `python build_basic_index.py`).
- [ ] Po spustení vygeneruje všetky potrebné indexové súbory.

### 5.5 Modul E – Vlastný searcher

**Úloha:**
- Vyhľadávať nad vlastným indexom.

**Požiadavky:**
1. CLI skript, napr. `python search_basic.py`.
2. Parameter pre voľbu rankingovej metódy (napr. `--metric tfidf` vs. `--metric alt1`).
3. Vstup: textový dopyt,
4. Výstup:
   - top-k dokumentov: `rank`, `score`, `title`, `url`, výňatok.

**Kontrolné kroky:**
- [ ] Overiť, že skript funguje na malej sade dát.
- [ ] Vytvoriť aspoň 5 ukážkových dopytov (pre konzultácie a odovzdanie).

### 5.6 Modul F – Štatistika a metadáta

**Úloha:**
- Vytvoriť tabulku štatistík o datasetoch:
  - počet dokumentov,
  - celková veľkosť na disku,
  - počet tokenov (ideálne cez `tiktoken` alebo iný tokenizer),
  - podiel relevantných dokumentov.

**Výstup:**
- `stats_foodcom.tsv` – základné štatistiky.
- (BONUS) `stats_tokens.tsv`.

### 5.7 Modul G – Spark job (Food.com + Wikipedia)

**Úloha:**
- Implementovať Spark job, ktorý:
  - načíta Food.com dáta,
  - načíta Wikipedia dump (alebo už predspracované wiki TSV),
  - extrahuje potrebné polia z wiki (regexy),
  - vykoná join podľa definovaných pravidiel.

**Požiadavky:**
1. Použiť PySpark (
   `from pyspark.sql import SparkSession`).
2. Definovať jasný join kľúč (napr. názvy ingrediencií, kategórií, názvy receptov vs. tittles v wiki).
3. Zabezpečiť, že:
   - join je vysvetlený v dokumentácii,
   - spočítaný je počet unikátnych pripojených wiki stránok.

**Kontrolné kroky:**
- [ ] Overiť, že Spark job sa dá spustiť lokálne.
- [ ] Pripraviť konfiguráciu pre spustenie na UISAV klastri.

### 5.8 Modul H – PyLucene index

**Úloha:**
- Na základe obohatených dát vytvoriť Lucene index.

**Požiadavky:**
1. Definovať schému indexu (polia – viď časť 4.6).
2. Implementovať builder skript, napr. `python build_lucene_index.py`.
3. Index uložiť do adresára `index_lucene/`.

**Kontrolné kroky:**
- [ ] Overiť, že index sa dá vytvoriť bez chýb.
- [ ] Overiť veľkosť indexu a počet dokumentov.

### 5.9 Modul I – PyLucene search CLI

**Úloha:**
- Implementovať CLI vyhľadávač nad Lucene indexom.

**Požiadavky:**
1. Podpora rôznych typov dopytov:
   - Boolean (AND/OR),
   - Phrase,
   - aspoň jeden typ field-specific query.
2. Vstup: query + voliteľne typ dopytu.
3. Výstup: top-k výsledkov s meta-informáciami.

**Porovnanie:**
- Pripraviť skript alebo notebook, ktorý porovná výsledky:
  - `basic_index` vs. `lucene_index` na tých istých 3 (alebo viac) dopytoch.

### 5.10 Modul J – Evaluácia

**Úloha:**
- Zhodnotiť úspešnosť vyhľadávania.

**Požiadavky:**
1. Definovať malú sadu dopytov (napr. 5–10),
2. Pre každý dopyt manuálne označiť relevantné dokumenty,
3. Vypočítať:
   - precision,
   - recall,
   - prípadne precision@k.

**Výstupy:**
- Tabuľka (TSV/PDF) s výsledkami,
- slovný komentár v dokumentácii.

---

## 6. Dokumentácia a odovzdanie

### 6.1 Textový dokument (min. 3 strany)

Dokument musí obsahovať:

1. **Popis projektu a motivácia (cca 15 riadkov)**
   - Prečo vyhľadávanie receptov,
   - prečo Food.com + Wikipedia,
   - aký problém rieši používateľ (napr. rýchle nájdenie receptov podľa ingrediencií, kuchyne…).

2. **Prehľad existujúcich riešení (0,5 strany)**
   - Aké existujúce vyhľadávače receptov existujú (Food.com, Allrecipes, Google Recipes…),
   - aké IR techniky používajú (fulltext, filtrovanie, odporúčanie).

3. **Popis riešenia, použitý softvér a frameworky (cca 1 strana)**
   - Architektúra (crawler, parser, indexer, Spark, Lucene),
   - konkrétne knižnice (requests, re, PySpark, PyLucene…),
   - popis problémov pri implementácii.

4. **Popis dát (Food.com, Wikipedia)**
   - Štruktúra datasetov,
   - príklady záznamov (ako zip na wiki),
   - štatistiky dát.

5. **Vyhodnotenie (0,5–1 strana)**
   - Precision/recall výsledky,
   - slovný komentár – čo fungovalo dobre, čo nie, kde sú obmedzenia.

6. **Spustenie, inštalácia, použitie softvéru (0,5–1 strana)**
   - Ako nainštalovať závislosti,
   - ako spustiť crawler, parser, indexer, Spark job, Lucene index, searcher,
   - minimálne príklady príkazov.

### 6.2 Wiki stránka

Na personálnej wiki stránke musí byť:
- TL;DR opis projektu,
- odkazy na:
  - dataset Food.com,
  - dataset Wikipedia,
  - zip s kódom,
  - dokumentáciu (PDF / wiki text),
  - prezentáciu (slajdy v PDF),
- ukážky extraktovaných dát (minimálne 5 príkladov),
- ukážky regexov.

### 6.3 ZIP s kódom

- Komprimovaný pomocou **ZIP**, nie RAR.
- Rozumná štruktúra priečinkov:
  - `crawler/`, `parser/`, `indexer_basic/`, `spark_job/`, `pylucene_index/`, `evaluation/`, `docs/`, `data/` (alebo cesty nakonfigurované v config súbore).
- Readme s inštrukciami.

### 6.4 Prezentácia

Slajdy by mali obsahovať:
1. Problém a motivácia,
2. Dáta a ich vlastnosti,
3. Architektúra riešenia,
4. Ukážky výstupov (screenshoty CLI, príklady dopytov),
5. Vyhodnotenie,
6. Zhrnutie.

---

## 7. Konzultácie a čo musí byť pripravené

### 7.1 Konzultácia 1 – Výber a potvrdenie projektu + dáta

Termín: **do 2.10.2025**

Musí byť pripravené:
- TL;DR opis projektu + motivácia.
- Odkaz na Food.com (čo presne scrapujete – recepty, kategórie…).
- Odkaz na wiki (aké články sú zaujímavé – napr. ingrediencie, kuchyne).
- Minimálne 5 párov **otázka → očakávaná odpoveď** pre systém.

### 7.2 Konzultácia 2a – Návrh riešenia

Termín: **17.10.2025**

Pripraviť:
- Zoznam frameworkov a knižníc (Python, Spark, PyLucene…).
- Diagram architektúry crawlera (ako sa plazia URL, ako sa ukladajú dáta).
- Ukážka HTTP hlavičiek, timeout, sleep.
- Implementovaný základ crawlera + niekoľko stiahnutých stránok.

### 7.3 Konzultácia 2b – Prvá časť projektu (31.10.2025)

Musí byť:
- Dokončený crawler.
- Stiahnuté všetky potrebné dáta + štatistika (počet, veľkosť na disku).
- Dokončený extraktor (regexy) + ukážky na wiki.
- Vlastný indexer + minimálne 2 IDF metódy.
- (BONUS) Unit testy na regexy.
- (BONUS) Štatistika tokenov.

Odovzdanie 1. časti – report s kapitolami:
- opis projektu,
- odkazy na scrapované stránky + ukážky dát,
- 5 párov otázka/odpoveď,
- použité frameworky,
- architektúra crawlera (diagram),
- tabuľka metadát,
- odôvodnenie hlavičiek a sleepov,
- ukážka kódu na extrakciu URL,
- ukážka kódu na extrakciu entít,
- opis indexera a indexu,
- opis IDF metód,
- porovnanie správania metód IDF na 3 queries,
- tabuľka so štatistikou dokumentov,
- ZIP s kódom.

### 7.4 Konzultácia 3 – Spracovanie veľkých dát (Spark)

Termín: **do 14.11.2025**

Musí byť:
- Rozšírený kód na spracovanie veľkých dát (Food.com + Wikipedia) v Sparku.
- Extrakcia wiki dát pomocou regexov.
- Implementovaný join.
- Vyčíslené:
  - koľko wiki stránok bolo joinutých,
  - aké atribúty z wiki sú použité.

### 7.5 Konzultácia 4 – Takmer hotové riešenie

Termín: **do 28.11.2025**

Musí byť:
- Hotový Spark kód (join funguje).
- Návrh a implementácia indexu v PyLucene.
- Odôvodnenie polí indexu.
- Prepojenie novo vytvoreného indexu do aplikácie.
- Porovnanie dopytov: starý index vs. nový Lucene index.
- Popis typov dopytov (Boolean, Range, Phrase, Fuzzy…).
- Odkaz na GitHub s aktuálnym kódom.

### 7.6 Konzultácia 5 – Hotový softvér

Termín: **do 5.12.2025**

Musí byť:
- Kompletný softvér – spustiteľný, otestovaný na celých dátach.
- Pripravená dokumentácia a prezentácia.
- Vyhodnotené metriky (precision/recall).

Hard deadline odovzdania: **do 15.12.2025**.

---

## 8. Zhrnutie pre AI agenta

1. **Prejdi existujúci kód** a porovnaj ho s touto špecifikáciou.
2. **Zakáž / odstráň** použitie Pandas, SQL databáz, XPath, NLTK.
3. Uisti sa, že:
   - crawler generuje konzistentnú štruktúru raw dát,
   - parser vytvára `recipes_foodcom.tsv` s požadovanými stĺpcami,
   - existuje funkčný vlastný indexer + searcher,
   - existuje Spark job na spracovanie Food.com + Wikipedia,
   - join je implementovaný a zdokumentovaný,
   - PyLucene index a searcher sú funkčné,
   - existuje evaluačný skript s výpočtom precision a recall.
4. Priprav všetky výstupné súbory, štatistiky, ukážkové queries a dokumentáciu tak, aby zodpovedali požiadavkám konzultácií a finálneho odovzdania.

