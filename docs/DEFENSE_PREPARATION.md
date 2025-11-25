# 🎓 Príprava na Obhajobu: Food Recipes IR Pipeline

Tento dokument slúži ako komplexný sprievodca na obhajobu projektu. Obsahuje základné fakty, technické detaily, vysvetlenia algoritmov a odpovede na "záludné" otázky.

---

## 1. ⚡ Rýchle Fakty (Cheat Sheet)

Ak sa opýta na čísla, strieľaj tieto hodnoty:

*   **Počet receptov:** `5 646` (Food.com)
*   **Počet wiki entít:** `8 459` (kulinárske články z Wikipédie)
*   **Gazetteer:** `8 460` záznamov (pre entity linking)
*   **Prepojenia (Links):** `107 614` (priemerne ~19 wiki odkazov na jeden recept)
*   **Technológie:** Python 3.14, PyLucene (Java wrapper), PySpark, Regex, Aho-Corasick.
*   **Rýchlosť indexácie:** ~2.7 sekundy (pre celý dataset).
*   **Rýchlosť vyhľadávania:** milisekundy (vďaka invertovanému indexu).

---

## 2. 🏗 Architektúra a Pipeline

**Otázka: Popíšte, ako to celé funguje (Big Picture).**
**Odpoveď:**
Projekt je **E2E (End-to-End) Information Retrieval pipeline**. Skladá sa zo 6 krokov:
1.  **Crawler:** Stiahne surové HTML stránky z Food.com (dodržiava `robots.txt`, politeness).
2.  **Parser:** Extrahuje štruktúrované dáta (JSON-LD alebo Regex fallback) -> `recipes_foodcom.jsonl`.
3.  **Wiki Processing (Spark):** Spracuje obrovský XML dump Wikipédie, vyfiltruje len kulinárske veci -> `wiki_culinary.jsonl`.
4.  **Enrichment:** Spojí recepty s Wikipédiou pomocou **Aho-Corasick** algoritmu (nájde v texte receptu kľúčové slová ako "Taco" a pridá k nim link/abstrakt).
5.  **Indexing (PyLucene):** Vytvorí **invertovaný index** (BM25 model) pre rýchle vyhľadávanie.
6.  **Search:** CLI rozhranie, ktoré umožňuje full-text vyhľadávanie a filtrovanie (čas, kuchyňa, ingrediencie).

---

## 3. 🧠 Technické Deep-Dive (Rafinované otázky)

### 🔍 A. Regulárne výrazy (Regex) v Parsery

**Otázka: Ako presne funguje váš parser? Čo ak sa zmení dizajn stránky?**
**Odpoveď:**
Mám **dvojvrstvový parser** pre robustnosť:
1.  **Vrstva 1 (Moderná): JSON-LD.** Väčšina moderných stránok (vrátane Food.com) obsahuje v HTML skrytý JSON blok (`<script type="application/ld+json">`) podľa štandardu Schema.org. Toto je najpresnejšie a nezávislé od dizajnu (CSS).
2.  **Vrstva 2 (Fallback): Regexy.** Ak JSON chýba, nastupujú regulárne výrazy.

**Otázka: Vysvetlite mi tento regex na parsovanie času: `PT(\d+H)?(\d+M)?`**
**Odpoveď:**
Toto parsuje ISO 8601 formát trvania (napr. `PT1H30M` = 1 hodina 30 minút).
*   `PT`: Literál, začiatok stringu (Period Time).
*   `(\d+H)?`: Prvá zachytávacia skupina pre hodiny. `\d+` znamená jedno alebo viac čísel, `H` je znak hodiny. Celé je to v zátvorke s `?`, čo znamená, že táto časť je **nepovinná** (môže byť len 30 minút bez hodín).
*   `(\d+M)?`: To isté pre minúty.

**Otázka: Ako parsujete ingrediencie cez Regex?**
**Odpoveď:**
Hľadám vzory zoznamov v HTML. Napríklad:
`re.compile(r'<li[^>]*class="[^"]*ingredient[^"]*"[^>]*>(.*?)</li>', re.IGNORECASE)`
*   `<li`: Začiatok list itemu.
*   `[^>]*`: Preskoč akékoľvek znaky, kým nenájdeš `>`.
*   `class="...ingredient..."`: Hľadám triedu, ktorá obsahuje slovo "ingredient".
*   `(.*?)`: **Non-greedy capture group**. Zachyť všetko vnútri tagu, ale zastav sa pri prvom možnom `</li>`. Keby tam nebol otáznik (`.*`), regex by "zožral" všetko až po posledný `</li>` na stránke (greedy).

### ⚡ B. Aho-Corasick Algoritmus (Enrichment)

**Otázka: Prečo ste na hľadanie entít nepoužili obyčajný `str.find()` alebo Regex?**
**Odpoveď:**
Pretože mám **8 460 entít** (kľúčových slov) a tisíce receptov.
*   Keby som použil `str.find()` v cykle pre každú entitu, zložitosť by bola `O(N * M)` (dĺžka textu * počet entít). To by trvalo hodiny.
*   **Aho-Corasick** postaví z kľúčových slov **konečný automat (Trie / strom)**.
*   Text receptu prejde týmto automatom **iba raz**.
*   Zložitosť je lineárna `O(N)` (dĺžka textu + počet výskytov). Preto enrichment 5000 receptov trvá len pár sekúnd.

### 📚 C. PyLucene a BM25 (Indexing)

**Otázka: Čo je to ten "Invertovaný Index"?**
**Odpoveď:**
Je to štruktúra podobná registru na konci knihy.
*   Namiesto ukladania `Dokument -> Slová`, ukladáme `Slovo -> Zoznam Dokumentov (Postings list)`.
*   Napríklad pre slovo "chicken": `chicken -> [Doc1, Doc5, Doc99]`.
*   To umožňuje extrémne rýchle vyhľadávanie, lebo nemusíme prechádzať všetky texty, len sa pozrieme do indexu.

**Otázka: Prečo ste prešli z vlastného indexera na PyLucene? (Old vs New)**
**Odpoveď:**
Začal som s vlastným indexerom (`indexer/run.py`), ktorý ukladal dáta do TSV súborov.
*   **Starý (TSV):** Jednoduchý na pochopenie, ale pomalý pri veľkých dátach, nepodporuje pokročilé query (fuzzy, ranges) a nemá kompresiu.
*   **Nový (PyLucene):** Profesionálne riešenie. Je to wrapper nad Java Lucene.
    *   **Rýchlosť:** Binárny formát, memory mapping.
    *   **Funkcie:** BM25 ranking (lepší ako TF-IDF), stemming, stop-words, range queries (pre čas a dátumy).
    *   **Výsledok:** PyLucene je o rády rýchlejší a presnejší.

**Otázka: Ako funguje BM25 (Best Matching 25)? Prečo nie len TF-IDF?**
**Odpoveď:**
BM25 je vylepšenie TF-IDF.
1.  **TF (Term Frequency):** Čím viackrát sa slovo vyskytuje, tým je relevantnejšie. Ale BM25 má **saturáciu** – ak sa slovo vyskytuje 100x, nie je to 10x lepšie ako 10x. Krivka sa splošťuje.
2.  **IDF (Inverse Document Frequency):** Vzácne slová (napr. "šafran") majú vyššiu váhu ako bežné ("soľ").
3.  **Normalizácia dĺžky:** BM25 penalizuje dlhé dokumenty. Ak sa slovo "chicken" vyskytne 1x v krátkom recepte, je to dôležitejšie, ako keď sa vyskytne 1x v 10-stranovom článku.

---

## 4. 🛡 Obrana a "Chytáky"

**Otázka: Prečo ste nepoužili SQL databázu?**
**Odpoveď:**
Pre Information Retrieval (IR) systémy nie je SQL ideálne.
*   SQL je dobré na presné zhody (`WHERE name = 'Pizza'`).
*   IR potrebuje **full-text search**, ranking (zoradenie podľa relevancie), fuzzy matching a prácu s tokenmi. Na to sú špecializované indexy ako Lucene (alebo Elasticsearch/Solr, ktoré na Lucene stoja).
*   Pre ukladanie dát používam **JSONL** (Line-delimited JSON), čo je štandard pre Big Data a logy – ľahko sa číta streamovaním (riadok po riadku) a nezaberá pamäť ako načítanie celého JSON poľa.

**Otázka: Ako riešite duplicity? (Napr. ak crawler stiahne to isté 2x)**
**Odpoveď:**
1.  **Crawler:** Používa `Set` navštívených URL (Frontier), aby nešiel na tú istú linku dvakrát.
2.  **Dáta:** Mám skripty (`uniq`, `sort`), ktorými som validoval, že `id` receptov sú unikátne.
3.  **Indexer:** Pri spustení indexácie (`IndexWriterConfig.OpenMode.CREATE`) sa starý index zmaže a vytvorí nanovo. Tým sa zabráni duplicitám v indexe pri opakovanom spustení.

**Otázka: Čo ak by ste mali 10 miliónov receptov? Zvládol by to váš systém?**
**Odpoveď:**
*   **Crawler:** Musel by byť distribuovaný (viac vlákien/strojov).
*   **Parser/Enricher:** Sú stavané na streamovanie (riadok po riadku), takže pamäť by nebola problém, len čas.
*   **Search:** PyLucene je veľmi efektívne, ale pri 10M by som už asi prešiel na **Elasticsearch** (čo je distribuovaný Lucene), aby som mohol index shardovať na viac serverov.

**Otázka: Použili ste AI? Nie je to plagiát?**
**Odpoveď:**
AI (Copilot) som používal ako **inteligentného asistenta**, nie autora.
*   **Moja práca:** Architektúra, výber algoritmov, logika spájania dát, ladenie parametrov BM25, písanie dokumentácie a pochopenie celého toku.
*   **AI práca:** Generovanie "boilerplate" kódu (napr. definície tried, importy), písanie regexov (ktoré som následne testoval), generovanie unit testov.
*   Kód som musel aktívne upravovať a debugovať (napr. problémy s PyLucene JVM, inštalácia závislostí), čo AI za mňa nevyrieši.

---

## 5. 🧪 Ukážkové Scenáre (Demo)

Ak bude chcieť vidieť demo, spusti toto:

1.  **Vyhľadávanie s filtrom:**
    *"Ukáž mi mexické recepty s kuracím mäsom, hotové do 30 minút."*
    ```bash
    ./packaging/run.sh search_lucene "chicken" 5 --filter '{"cuisine": "Mexican", "max_total_minutes": 30}'
    ```
    *(Poznámka: Syntax filtra v CLI môže vyžadovať úpravu podľa `search_cli/run.py`, ak nie, použi Python priamo)*:
    ```bash
    python3 search_cli/run.py --index index/lucene/v2 --q "chicken" --k 5 --filter '{"cuisine": "Mexican", "max_total_minutes": 30}'
    ```

2.  **Ukážka Wiki Entít:**
    *"Ukáž mi, ako funguje to prepojenie s Wikipédiou."*
    Spusti vyhľadávanie a ukáž sekciu `📚 FROM WIKIPEDIA` vo výstupe. Upozorni na to, že systém rozpoznal ingrediencie (napr. "Cumin") a priradil im popis.

3.  **Validácia dát:**
    *"Ako viem, že tie dáta sú správne?"*
    Ukáž logy alebo spusti `wc -l` na súbory, aby videl, že dáta reálne existujú a nie sú vymyslené.

---

## 6. 🐞 Známe Limitácie (Pre istotu)

Ak sa opýta, čo by sa dalo zlepšiť:
*   **Synonymá:** Zatiaľ nemám pokročilý slovník synoným (napr. "baklažán" = "eggplant").
*   **Lemmatizácia:** Vyhľadávanie je citlivé na tvary slov (chicken vs chickens), hoci Lucene `StandardAnalyzer` rieši základné veci, pre slovenčinu/iné jazyky by to chcelo lepší stemmer.
*   **Obrázky:** Sťahujem len URL, neukladám binárne dáta obrázkov (kvôli miestu).
