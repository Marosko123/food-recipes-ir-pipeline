# Testing Guide - Lupyne Recipe Search

Návod na testovanie indexu a vyhľadávania.

## Predpoklady

Potrebuješ:
- PyLucene 10.0.0 + Lupyne 3.3 (inštalácia v LUPYNE_INSTALL.md)
- Python 3.14 z Homebrew
- Postavený index v `index/lucene/v2/`

POZOR: Ak máš Java chyby, skontroluj JAVA_HOME!

## Základné vyhľadávanie

Jednoduchý search:
```bash
python3.14 search_cli/run.py --index index/lucene/v2 --q "chocolate cake" --k 10
```

Malo by vrátiť 10 výsledkov. Skóre je zvyčajne 12-20 pre dobré zhody.

## Filtrovanie

Čas (recepty do 30 min):
```bash
python3.14 search_cli/run.py --index index/lucene/v2 --q "quick dinner" \
  --filter '{"max_total_minutes": 30}'
```

Ingrediencie (musí obsahovať):
```bash
python3.14 search_cli/run.py --index index/lucene/v2 --q "pasta" \
  --filter '{"include_ingredients": ["garlic", "tomato"]}'
```

NOTE: Ingredient filter používa full-text (nie exact match), takže "chicken" 
matchne aj "chicken breast", "grilled chicken" atď.

Kuchyňa (Mexican alebo Italian):
```bash
python3.14 search_cli/run.py --index index/lucene/v2 --q "rice" \
  --filter '{"cuisine": ["Mexican", "Italian"]}'
```

## Známe problémy

1. **AlreadyClosedException warning** - Lupyne bug, ignoruj (search funguje)
2. **0 results** - skontroluj či je index postavený správne
3. **Filter nefunguje** - skontroluj JSON syntax (úvodzovky!)
4. **bytesPerDim mismatch** - používaj LongPoint (nie IntPoint) pre time filter

## Wikipedia entity links

Preveriť pokrytie:
```bash
python3.14 -c "
import json
with open('data/normalized/recipes_enriched.jsonl') as f:
    recipes = [json.loads(line) for line in f]
    
with_wiki = sum(1 for r in recipes if r.get('wiki_links'))
print(f'Recipes with wiki_links: {with_wiki}/{len(recipes)}')
"
```

Expected: 5144/5646 (91.1%)

## Expected results

| Query | Top Result | Score |
|-------|-----------|-------|
| "chocolate cake" | Chocolate cake recipes | 12-18 |
| "mexican chicken" | Nachos, Tacos | 15-20 |

TODO: Pridať viac test queries

## Evaluácia

Spustiť všetky queries:
```bash
python3.14 eval/run.py --index index/lucene/v2 \
  --queries eval/queries.tsv --qrels eval/qrels.tsv \
  --output eval/runs/bm25_run.tsv --similarity bm25
```

Vypočítať metriky:
```bash
python3.14 eval/run.py --run eval/runs/bm25_run.tsv \
  --qrels eval/qrels.tsv --metrics
```

Expected: P@10 ~0.70-0.85, MAP ~0.65-0.80

---

Version: 2025-01-25
