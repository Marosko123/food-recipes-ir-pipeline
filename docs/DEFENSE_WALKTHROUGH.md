# 🎬 Scenár Obhajoby: "Príbeh Receptov" (Walkthrough)

Tento dokument je tvoj **scenár**. Nečítaj ho doslovne, ale drž sa tejto osnovy. Je to postavené ako príbeh toku dát – od špinavého HTML až po inteligentné vyhľadávanie.

---

## 🏁 Úvod (1 minúta)

**🗣 Čo povedať:**
"Dobrý deň. Mojím cieľom bolo vytvoriť nielen obyčajný vyhľadávač, ale systém, ktorý **rozumie kulinárskemu kontextu**.
Väčšina vyhľadávačov hľadá len text. Môj systém obohacuje recepty o znalosti z Wikipédie. Keď hľadáte 'Taco', systém vie, že je to mexické jedlo a ponúkne vám k tomu kontext.
Celé to beží na pipeline: **Crawler → Parser → Spark (Wiki) → Enrichment → PyLucene Index**."

**💻 Čo ukázať:**
Otvorený terminál v roote projektu.
```bash
ls -F
# Ukáž, že projekt má jasnú štruktúru (data, index, parser, spark_jobs...)
```

---

## 1. Kapitola: Získanie dát (Crawler)

**🗣 Čo povedať:**
"Prvým krokom bolo získať dáta. Napísal som vlastný crawler pre **Food.com**.
Musel byť 'slušný' (polite) – dodržiavať `robots.txt` a nepreťažiť server. Stiahol som vyše **5 600 receptov**.
Dáta ukladám ako surové HTML, aby som sa k nim mohol kedykoľvek vrátiť."

**💻 Čo ukázať:**
Ukáž jedno surové HTML, aby videl ten "bordel", s ktorým začínaš.
```bash
head -n 20 data/raw/www.food.com/100095.html
```
*(Komentár: "Vidíte, je to surový kód, plný JavaScriptu a CSS balastu.")*

---

## 2. Kapitola: Čistenie a Extrakcia (Parser)

**🗣 Čo povedať:**
"Z toho HTML potrebujem dostať štruktúrované dáta: názov, ingrediencie, čas.
Použil som **hybridný prístup**:
1.  Najprv skúsim nájsť **JSON-LD** (moderný štandard pre metadáta).
2.  Ak to zlyhá, mám pripravené **Regulárne výrazy (Regex)** ako zálohu.
Výsledkom je čistý JSONL súbor."

**💻 Čo ukázať:**
Ukáž jeden vyparsovaný riadok (použi `jq` ak máš, alebo len `head`).
```bash
head -n 1 data/normalized/recipes_foodcom.jsonl
```
*(Komentár: "Tu už máme čisté dáta: title, ingredients, instructions...")*

---

## 3. Kapitola: Mozog systému (Wikipedia & Spark)

**🗣 Čo povedať:**
"Teraz prichádza tá zaujímavá časť. Chcel som, aby systém vedel, čo je to 'Cumin' alebo 'Sauté'.
Stiahol som dump Wikipédie (niekoľko GB XML) a spracoval ho pomocou **Apache Spark**.
Spark prešiel milióny článkov a vyfiltroval len tie kulinárske – ingrediencie, techniky, nástroje.
Vytvoril som takzvaný **Gazetteer** – slovník entít."

**💻 Čo ukázať:**
Ukáž ten slovník entít.
```bash
head -n 5 entities/wiki_gazetteer_v2.tsv
```
*(Komentár: "Vidíme, že 'Acorn squash' je identifikovaný ako ingrediencia a máme k nemu normalizovaný tvar.")*

---

## 4. Kapitola: Spájanie svetov (Enrichment)

**🗣 Čo povedať:**
"Mám recepty a mám entity. Ako ich spojiť?
Použil som algoritmus **Aho-Corasick**. Je to efektívny algoritmus na vyhľadávanie viacerých vzorov naraz.
Prešiel som texty receptov a našiel v nich zmienky o wiki entitách.
Výsledkom je 'obohatený' (enriched) recept, ktorý obsahuje nielen text, ale aj odkazy na Wikipédiu a abstrakty."

**💻 Čo ukázať:**
Nájdi recept, ktorý má `wiki_links` a ukáž to.
```bash
grep "wiki_links" data/normalized/recipes_enriched_v2.jsonl | head -n 1 | cut -c 1-200
# (Ten cut je tam len aby to nezahltilo obrazovku, stačí ukázať začiatok)
```

---

## 5. Kapitola: Vyhľadávanie (PyLucene Index)

**🗣 Čo povedať:**
"Všetky tieto dáta som naindexoval pomocou **PyLucene**.
Je to Python wrapper pre Java Lucene. Používam **Invertovaný Index** a ranking model **BM25**.
Indexujem nielen text, ale aj tie extrahované entity, čo mi umožňuje presné filtrovanie."

**💻 Čo ukázať (LIVE DEMO):**
Teraz to spusti naživo. To je "wow efekt".

**Scenár 1: Jednoduché hľadanie**
"Skúsme nájsť niečo s kuracím mäsom."
```bash
./packaging/run.sh search_lucene "chicken" 3
```
*(Ukáž vo výstupe zvýraznené slová a hlavne sekciu **📚 FROM WIKIPEDIA** – to je tvoja pridaná hodnota!)*

**Scenár 2: Komplexný filter (ak je čas)**
"A teraz niečo špecifické: Mexická kuchyňa, hotové do 30 minút."
```bash
./packaging/run.sh search_lucene "tortilla" 3 --filter '{"cuisine": "Mexican", "max_total_minutes": 30}'
```

---

## 6. Záver

**🗣 Čo povedať:**
"Na záver – podarilo sa mi vytvoriť funkčný prototyp vyhľadávača, ktorý kombinuje klasické full-text vyhľadávanie so sémantickou znalosťou z Wikipédie.
Celý systém je postavený modulárne, dáta sú perzistentné a vyhľadávanie je vďaka indexu okamžité."

*(Tu čakaj na otázky. Máš pripravený `DEFENSE_PREPARATION.md` na odpovede.)*
