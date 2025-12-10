#!/usr/bin/env python3
"""
Recipe Enricher
Combines recipes_foodcom.jsonl with wiki_culinary.jsonl to create recipes_enriched.jsonl

Enrichment includes:
- Entity linking: Match ingredients to Wikipedia articles
- Cuisine inference: Infer cuisine from ingredients with known origins
- Historical context: Add historical information about dishes/ingredients
- Ingredient origins: Add origin information for each ingredient

Usage:
    python3 entities/recipe_enricher.py \
        --recipes data/normalized/recipes_foodcom.jsonl \
        --wiki data/normalized/wiki_culinary.jsonl \
        --gazetteer entities/wiki_gazetteer.tsv \
        --output data/normalized/recipes_enriched.jsonl
"""

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import ahocorasick
except ImportError:
    logger.error("ahocorasick not found. Install: pip install pyahocorasick")
    import sys
    sys.exit(1)


class RecipeEnricher:
    """Enrich recipes with Wikipedia data."""
    
    def __init__(self, gazetteer_path: Path, wiki_jsonl_path: Path):
        """Initialize enricher with gazetteer and wiki data."""
        self.gazetteer_path = gazetteer_path
        self.wiki_jsonl_path = wiki_jsonl_path
        
        # Data structures
        self.automaton = None  # Aho-Corasick automaton for entity matching
        self.wiki_articles: Dict[str, Dict] = {}  # wiki_title -> article data
        self.surface_to_title: Dict[str, str] = {}  # surface -> wiki_title mapping
        self.title_to_type: Dict[str, str] = {}  # wiki_title -> type
        
        # Stats
        self.stats = {
            'recipes_processed': 0,
            'recipes_enriched': 0,
            'total_entities_linked': 0,
            'cuisines_inferred': 0
        }
    
    def load_data(self):
        """Load gazetteer and wiki articles."""
        logger.info("Loading gazetteer...")
        self._load_gazetteer()
        
        logger.info("Loading Wikipedia articles...")
        self._load_wiki_articles()
        
        logger.info("Building Aho-Corasick automaton...")
        self._build_automaton()
        
        logger.info(f"Loaded {len(self.wiki_articles)} Wikipedia articles")
        logger.info(f"Loaded {len(self.surface_to_title)} gazetteer entries")
    
    def _load_gazetteer(self):
        """Load gazetteer TSV file."""
        with open(self.gazetteer_path, 'r', encoding='utf-8') as f:
            next(f)  # Skip header
            
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    surface, wiki_title, entity_type = parts[:3]
                    self.surface_to_title[surface.lower()] = wiki_title
                    self.title_to_type[wiki_title] = entity_type
    
    def _load_wiki_articles(self):
        """Load Wikipedia articles from JSONL."""
        with open(self.wiki_jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                article = json.loads(line)
                wiki_title = article['wiki_title']
                self.wiki_articles[wiki_title] = article
    
    def _build_automaton(self):
        """Build Aho-Corasick automaton for entity matching."""
        self.automaton = ahocorasick.Automaton()
        
        for surface, wiki_title in self.surface_to_title.items():
            # Add surface form (lowercase for case-insensitive matching)
            self.automaton.add_word(surface.lower(), (surface, wiki_title))
        
        self.automaton.make_automaton()
    
    def find_entities(self, text: str) -> List[Dict]:
        """
        Find entities in text using Aho-Corasick.
        
        Returns list of dicts:
        - surface: matched text
        - wiki_title: Wikipedia article title
        - type: entity type (ingredient/dish/cuisine/etc)
        - position: (start, end) position in text
        """
        if not text:
            return []
        
        text_lower = text.lower()
        matches = []
        seen_positions = set()
        
        for end_pos, (surface, wiki_title) in self.automaton.iter(text_lower):
            start_pos = end_pos - len(surface) + 1
            
            # Skip if overlaps with existing match
            if any(start_pos <= pos < end_pos for pos in seen_positions):
                continue
            
            # Get entity type
            entity_type = self.title_to_type.get(wiki_title, 'unknown')
            
            # Get wiki article
            wiki_article = self.wiki_articles.get(wiki_title, {})
            
            matches.append({
                'surface': surface,
                'wiki_title': wiki_title,
                'type': entity_type,
                'position': (start_pos, end_pos),
                'origin_country': wiki_article.get('origin_country'),
                'origin_region': wiki_article.get('origin_region'),
                'year_origin': wiki_article.get('year_origin')
            })
            
            # Mark positions as used
            for pos in range(start_pos, end_pos + 1):
                seen_positions.add(pos)
        
        return matches
    
    def infer_cuisine(self, entities: List[Dict], current_cuisines: List[str]) -> List[str]:
        """
        Infer cuisine from entity origins.
        
        Returns list of inferred cuisines.
        """
        inferred = set(current_cuisines) if current_cuisines else set()
        
        # Count origins
        origin_counts = defaultdict(int)
        
        for entity in entities:
            if entity['type'] in ['ingredient', 'dish']:
                # Country
                if entity.get('origin_country'):
                    country = entity['origin_country']
                    # Map country to cuisine (simple heuristics)
                    if 'italy' in country.lower():
                        origin_counts['Italian'] += 2
                    elif 'mexico' in country.lower():
                        origin_counts['Mexican'] += 2
                    elif 'france' in country.lower():
                        origin_counts['French'] += 2
                    elif 'china' in country.lower():
                        origin_counts['Chinese'] += 2
                    elif 'india' in country.lower():
                        origin_counts['Indian'] += 2
                    elif 'japan' in country.lower():
                        origin_counts['Japanese'] += 2
                    elif 'spain' in country.lower():
                        origin_counts['Spanish'] += 2
                    elif 'greece' in country.lower():
                        origin_counts['Greek'] += 2
                
                # Region
                if entity.get('origin_region'):
                    region = entity['origin_region'].lower()
                    if 'asia' in region:
                        origin_counts['Asian'] += 1
                    elif 'europe' in region:
                        origin_counts['European'] += 1
                    elif 'mediterranean' in region:
                        origin_counts['Mediterranean'] += 1
        
        # Add cuisines with count >= 2
        for cuisine, count in origin_counts.items():
            if count >= 2:
                inferred.add(cuisine)
                self.stats['cuisines_inferred'] += 1
        
        return sorted(list(inferred))
    
    def enrich_recipe(self, recipe: Dict) -> Dict:
        """
        Enrich a single recipe with Wikipedia data.
        
        Returns enriched recipe dict.
        """
        self.stats['recipes_processed'] += 1
        
        # Combine text fields for entity matching
        text_fields = []
        text_fields.append(recipe.get('title', ''))
        text_fields.extend(recipe.get('ingredients', []))
        text_fields.extend(recipe.get('instructions', []))
        text_fields.append(recipe.get('description', ''))
        
        combined_text = ' '.join(text_fields)
        
        # Find entities
        entities = self.find_entities(combined_text)
        
        if not entities:
            return recipe  # No enrichment
        
        self.stats['recipes_enriched'] += 1
        self.stats['total_entities_linked'] += len(entities)
        
        # Create enriched recipe
        enriched = recipe.copy()
        
        # Add wiki_links
        enriched['wiki_links'] = [
            {
                'surface': e['surface'],
                'wiki_title': e['wiki_title'],
                'type': e['type'],
                'origin_country': e.get('origin_country'),
                'origin_region': e.get('origin_region'),
                'abstract': self.wiki_articles.get(e['wiki_title'], {}).get('abstract', '')[:500]  # Include abstract for indexing
            }
            for e in entities
        ]
        
        # Infer cuisine
        current_cuisines = recipe.get('cuisine', [])
        enriched['cuisine'] = self.infer_cuisine(entities, current_cuisines)
        
        # Add historical context for dishes (prefer History section, fallback to abstract)
        dish_entities = [e for e in entities if e['type'] == 'dish']
        if dish_entities:
            dish_title = dish_entities[0]['wiki_title']
            dish_article = self.wiki_articles.get(dish_title)
            if dish_article:
                # Prefer dedicated History section
                if dish_article.get('history'):
                    enriched['historical_context'] = dish_article['history'][:600]
                elif dish_article.get('abstract'):
                    enriched['historical_context'] = dish_article['abstract'][:500]
                
                # Add infobox data (selected fields)
                if dish_article.get('infobox'):
                    infobox = dish_article['infobox']
                    enriched['dish_info'] = {
                        'name': infobox.get('name'),
                        'type': infobox.get('type'),
                        'country': infobox.get('country'),
                        'region': infobox.get('region'),
                        'main_ingredient': infobox.get('main_ingredient'),
                        'variations': infobox.get('variations')
                    }
                    # Remove None values
                    enriched['dish_info'] = {k: v for k, v in enriched['dish_info'].items() if v}
        
        # Add ingredient origins (with infobox data)
        ingredient_entities = [e for e in entities if e['type'] == 'ingredient']
        if ingredient_entities:
            enriched['ingredient_origins'] = {}
            for e in ingredient_entities:
                wiki_title = e['wiki_title']
                ingredient_article = self.wiki_articles.get(wiki_title)
                
                origin_data = {
                    'country': e.get('origin_country'),
                    'region': e.get('origin_region'),
                    'year': e.get('year_origin')
                }
                
                # Add infobox main_ingredient if available
                if ingredient_article and ingredient_article.get('infobox'):
                    infobox = ingredient_article['infobox']
                    if infobox.get('type'):
                        origin_data['type'] = infobox['type']
                
                # Only add if has some data
                if any(v for v in origin_data.values()):
                    enriched['ingredient_origins'][wiki_title] = origin_data
        
        return enriched
    
    def process_recipes(self, recipes_path: Path, output_path: Path):
        """Process all recipes and write enriched versions."""
        logger.info(f"Processing recipes from {recipes_path}")
        logger.info(f"Output will be written to {output_path}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(recipes_path, 'r', encoding='utf-8') as f_in, \
             open(output_path, 'w', encoding='utf-8') as f_out:
            
            for line_no, line in enumerate(f_in, 1):
                recipe = json.loads(line)
                enriched = self.enrich_recipe(recipe)
                
                f_out.write(json.dumps(enriched, ensure_ascii=False) + '\n')
                
                if line_no % 1000 == 0:
                    logger.info(f"Processed {line_no:,} recipes, "
                              f"enriched {self.stats['recipes_enriched']:,}")
        
        logger.info(f"Finished processing {self.stats['recipes_processed']:,} recipes")
    
    def print_stats(self):
        """Print enrichment statistics."""
        print("\n" + "="*60)
        print("ENRICHMENT STATISTICS")
        print("="*60)
        print(f"Recipes processed:       {self.stats['recipes_processed']:,}")
        print(f"Recipes enriched:        {self.stats['recipes_enriched']:,}")
        print(f"Total entities linked:   {self.stats['total_entities_linked']:,}")
        print(f"Cuisines inferred:       {self.stats['cuisines_inferred']:,}")
        
        if self.stats['recipes_enriched'] > 0:
            avg_entities = self.stats['total_entities_linked'] / self.stats['recipes_enriched']
            print(f"Avg entities per recipe: {avg_entities:.2f}")
        
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Enrich recipes with Wikipedia data'
    )
    parser.add_argument(
        '--recipes',
        type=Path,
        default=Path('data/normalized/recipes_foodcom.jsonl'),
        help='Input recipes JSONL file'
    )
    parser.add_argument(
        '--wiki',
        type=Path,
        default=Path('data/normalized/wiki_culinary.jsonl'),
        help='Wikipedia culinary articles JSONL'
    )
    parser.add_argument(
        '--gazetteer',
        type=Path,
        default=Path('entities/wiki_gazetteer.tsv'),
        help='Gazetteer TSV file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/normalized/recipes_enriched.jsonl'),
        help='Output enriched recipes JSONL'
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("Recipe Enricher")
    logger.info("="*60)
    logger.info(f"Recipes:   {args.recipes}")
    logger.info(f"Wiki:      {args.wiki}")
    logger.info(f"Gazetteer: {args.gazetteer}")
    logger.info(f"Output:    {args.output}")
    logger.info("="*60)
    
    # Validate inputs
    if not args.recipes.exists():
        logger.error(f"Recipes file not found: {args.recipes}")
        return 1
    
    if not args.wiki.exists():
        logger.error(f"Wiki file not found: {args.wiki}")
        return 1
    
    if not args.gazetteer.exists():
        logger.error(f"Gazetteer file not found: {args.gazetteer}")
        return 1
    
    # Create enricher
    enricher = RecipeEnricher(args.gazetteer, args.wiki)
    
    # Load data
    enricher.load_data()
    
    # Process recipes
    enricher.process_recipes(args.recipes, args.output)
    
    # Print stats
    enricher.print_stats()
    
    logger.info("✅ Enrichment completed successfully!")
    
    return 0


if __name__ == '__main__':
    exit(main())
