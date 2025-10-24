#!/usr/bin/env python3
"""
Recipe Enricher - Adds Wikipedia knowledge to recipes
Matches recipe ingredients/cuisines/titles with Wikipedia entities
and enriches recipes with historical and cultural context.
"""

import argparse
import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

try:
    import ahocorasick
except ImportError:
    print("Installing pyahocorasick...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "pyahocorasick"])
    import ahocorasick

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RecipeEnricher:
    """Enrich recipes with Wikipedia knowledge."""
    
    def __init__(self):
        self.gazetteer: Dict[str, Dict] = {}  # norm -> {wiki_title, type, surface}
        self.wiki_entities: Dict[str, Dict] = {}  # title -> full entity
        self.automaton = None
        
        self.stats = {
            'total_recipes': 0,
            'enriched_recipes': 0,
            'total_links': 0,
            'links_by_type': defaultdict(int),
            'cuisines_inferred': 0
        }
    
    def load_gazetteer(self, gazetteer_file: Path):
        """Load gazetteer TSV file."""
        logger.info(f"Loading gazetteer from {gazetteer_file}")
        
        count = 0
        with open(gazetteer_file, 'r', encoding='utf-8') as f:
            header = next(f)  # Skip header
            
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) != 4:
                    continue
                
                surface, wiki_title, entity_type, norm = parts
                
                # Store by normalized form for quick lookup
                if norm not in self.gazetteer:
                    self.gazetteer[norm] = {
                        'wiki_title': wiki_title,
                        'type': entity_type,
                        'surface': surface,
                        'variants': set()
                    }
                
                self.gazetteer[norm]['variants'].add(surface)
                count += 1
        
        logger.info(f"Loaded {len(self.gazetteer)} unique normalized entities ({count} total entries)")
    
    def load_wiki_entities(self, wiki_jsonl: Path):
        """Load Wikipedia entity details from JSONL."""
        logger.info(f"Loading Wikipedia entities from {wiki_jsonl}")
        
        with open(wiki_jsonl, 'r', encoding='utf-8') as f:
            for line in f:
                entity = json.loads(line.strip())
                title = entity['title']
                self.wiki_entities[title] = entity
        
        logger.info(f"Loaded {len(self.wiki_entities)} Wikipedia entities with metadata")
    
    def build_automaton(self):
        """Build Aho-Corasick automaton for fast string matching."""
        logger.info("Building Aho-Corasick automaton...")
        
        self.automaton = ahocorasick.Automaton()
        
        # Add all surface forms
        for norm, data in self.gazetteer.items():
            for surface in data['variants']:
                # Case-insensitive matching
                key = surface.lower()
                value = (norm, data['wiki_title'], data['type'])
                self.automaton.add_word(key, value)
        
        self.automaton.make_automaton()
        logger.info(f"Automaton built with {len(self.automaton)} patterns")
    
    def find_entities(self, text: str) -> List[Dict]:
        """Find entity mentions in text using Aho-Corasick."""
        if not text or not self.automaton:
            return []
        
        text_lower = text.lower()
        matches = []
        seen = set()
        
        for end_pos, (norm, wiki_title, entity_type) in self.automaton.iter(text_lower):
            # Avoid duplicate matches
            if wiki_title not in seen:
                seen.add(wiki_title)
                
                # Get full entity info
                entity_info = {
                    'surface': text[end_pos - len(norm) + 1:end_pos + 1],  # Original case
                    'wiki_title': wiki_title,
                    'type': entity_type,
                    'norm': norm
                }
                
                # Add Wikipedia metadata if available (full abstract, no truncation)
                if wiki_title in self.wiki_entities:
                    wiki_data = self.wiki_entities[wiki_title]
                    entity_info['abstract'] = wiki_data.get('abstract', '')  # FULL abstract
                    entity_info['categories'] = wiki_data.get('categories', [])[:5]
                
                matches.append(entity_info)
        
        return matches
    
    def enrich_recipe(self, recipe: Dict) -> Dict:
        """Enrich a single recipe with Wikipedia knowledge."""
        enriched = recipe.copy()
        
        # Find entities in different fields
        all_links = []
        
        # 1. Match title (for dish articles like "Caesar Salad")
        title_links = self.find_entities(recipe.get('title', ''))
        all_links.extend(title_links)
        
        # 2. Match ingredients
        ingredients_text = ' '.join(recipe.get('ingredients', []))
        ingredient_links = self.find_entities(ingredients_text)
        all_links.extend(ingredient_links)
        
        # 3. Match instructions (for techniques)
        instructions_text = ' '.join(recipe.get('instructions', []))
        instruction_links = self.find_entities(instructions_text)
        all_links.extend(instruction_links)
        
        # 4. Match existing cuisine field
        cuisine_text = ' '.join(recipe.get('cuisine', []))
        cuisine_links = self.find_entities(cuisine_text)
        all_links.extend(cuisine_links)
        
        # Remove duplicates (same wiki_title)
        unique_links = {}
        for link in all_links:
            title = link['wiki_title']
            if title not in unique_links:
                unique_links[title] = link
        
        wiki_links = list(unique_links.values())
        
        # Add wiki_links field
        enriched['wiki_links'] = wiki_links
        
        # Count by type
        for link in wiki_links:
            self.stats['links_by_type'][link['type']] += 1
        
        self.stats['total_links'] += len(wiki_links)
        
        # Infer cuisine if missing
        if not recipe.get('cuisine'):
            inferred_cuisines = [
                link['wiki_title'] 
                for link in wiki_links 
                if link['type'] == 'cuisine'
            ]
            if inferred_cuisines:
                enriched['cuisine'] = inferred_cuisines
                self.stats['cuisines_inferred'] += 1
        
        if wiki_links:
            self.stats['enriched_recipes'] += 1
        
        return enriched
    
    def enrich_recipes(self, input_file: Path, output_file: Path, limit: Optional[int] = None):
        """Enrich all recipes from input JSONL and save to output JSONL."""
        logger.info(f"Enriching recipes from {input_file}")
        logger.info(f"Output will be saved to {output_file}")
        
        if limit:
            logger.info(f"Processing limit: {limit} recipes")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(input_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            
            for line_num, line in enumerate(f_in, 1):
                if limit and line_num > limit:
                    break
                
                try:
                    recipe = json.loads(line.strip())
                    enriched = self.enrich_recipe(recipe)
                    
                    f_out.write(json.dumps(enriched, ensure_ascii=False) + '\n')
                    
                    self.stats['total_recipes'] += 1
                    
                    # Progress logging
                    if line_num % 100 == 0:
                        logger.info(f"Processed {line_num} recipes, "
                                  f"{self.stats['enriched_recipes']} enriched")
                
                except json.JSONDecodeError as e:
                    logger.error(f"JSON error at line {line_num}: {e}")
                    continue
        
        logger.info(f"Enrichment completed: {self.stats['total_recipes']} recipes processed")
    
    def print_stats(self):
        """Print enrichment statistics."""
        print("\n" + "="*60)
        print("ENRICHMENT STATISTICS")
        print("="*60)
        print(f"Total recipes processed:     {self.stats['total_recipes']:,}")
        print(f"Recipes enriched:            {self.stats['enriched_recipes']:,} "
              f"({self.stats['enriched_recipes']/max(1,self.stats['total_recipes'])*100:.1f}%)")
        print(f"Total wiki links added:      {self.stats['total_links']:,}")
        print(f"Avg links per recipe:        {self.stats['total_links']/max(1,self.stats['total_recipes']):.2f}")
        print(f"Cuisines inferred:           {self.stats['cuisines_inferred']:,}")
        print("\nLinks by type:")
        for entity_type, count in sorted(self.stats['links_by_type'].items()):
            print(f"  {entity_type:15s} {count:,}")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Enrich recipes with Wikipedia knowledge'
    )
    parser.add_argument(
        '--recipes',
        type=Path,
        default=Path('data/normalized/recipes_foodcom.jsonl'),
        help='Input recipes JSONL file (Food.com parse)'
    )
    parser.add_argument(
        '--gazetteer',
        type=Path,
        default=Path('entities/wiki_gazetteer.tsv'),
        help='Wikipedia gazetteer TSV file'
    )
    parser.add_argument(
        '--wiki-entities',
        type=Path,
        default=Path('data/normalized/wiki_culinary.jsonl'),
        help='Wikipedia entities JSONL file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/normalized/recipes_enriched.jsonl'),
        help='Output enriched recipes JSONL file'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of recipes to process (for testing)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.recipes.exists():
        logger.error(f"Recipes file not found: {args.recipes}")
        return 1
    
    if not args.gazetteer.exists():
        logger.error(f"Gazetteer file not found: {args.gazetteer}")
        return 1
    
    if not args.wiki_entities.exists():
        logger.error(f"Wiki entities file not found: {args.wiki_entities}")
        return 1
    
    # Create enricher
    enricher = RecipeEnricher()
    
    # Load data
    enricher.load_gazetteer(args.gazetteer)
    enricher.load_wiki_entities(args.wiki_entities)
    enricher.build_automaton()
    
    # Enrich recipes
    enricher.enrich_recipes(args.recipes, args.output, limit=args.limit)
    
    # Print stats
    enricher.print_stats()
    
    logger.info("✅ Enrichment completed successfully!")
    return 0


if __name__ == '__main__':
    exit(main())
