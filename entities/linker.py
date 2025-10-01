#!/usr/bin/env python3
"""
Phase E: Entity Linker
Links entities to Wikipedia and generates entity links JSONL.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from entities.matcher import create_entity_matcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityLinker:
    """Links entities in recipe data to Wikipedia."""
    
    def __init__(self, gazetteer_file: str):
        self.gazetteer_file = gazetteer_file
        self.matcher = create_entity_matcher()
        self.matcher.load_gazetteer(gazetteer_file)
        
        # Statistics
        self.stats = {
            'recipes_processed': 0,
            'entities_found': 0,
            'links_generated': 0
        }
    
    def process_recipe(self, recipe: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single recipe and extract entity links."""
        doc_id = recipe.get('id', '')
        if not doc_id:
            logger.warning("Recipe without ID, skipping")
            return []
        
        links = []
        
        # Process different fields
        fields_to_process = [
            ('title', recipe.get('title', '')),
            ('ingredients', ' '.join(recipe.get('ingredients', []))),
            ('instructions', ' '.join(recipe.get('instructions', []))),
            ('description', recipe.get('description', ''))
        ]
        
        for field, text in fields_to_process:
            if not text:
                continue
            
            # Find entities in this field
            entities = self.matcher.find_entities(text)
            
            for start, end, surface, wiki_title, normalized in entities:
                link = {
                    'docId': doc_id,
                    'field': field,
                    'start': start,
                    'end': end,
                    'surface': surface,
                    'wiki_title': wiki_title
                }
                links.append(link)
                self.stats['links_generated'] += 1
        
        self.stats['entities_found'] += len(entities)
        return links
    
    def process_recipes_file(self, input_file: str, output_file: str):
        """Process all recipes in a JSONL file."""
        logger.info(f"Processing recipes from {input_file}")
        
        input_path = Path(input_file)
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            for line_num, line in enumerate(infile, 1):
                try:
                    line = line.strip()
                    if not line:
                        continue
                    
                    recipe = json.loads(line)
                    links = self.process_recipe(recipe)
                    
                    # Write each link as a separate JSONL line
                    for link in links:
                        outfile.write(json.dumps(link) + '\n')
                    
                    self.stats['recipes_processed'] += 1
                    
                    if line_num % 10 == 0:
                        logger.info(f"Processed {line_num} recipes")
                
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error at line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing recipe at line {line_num}: {e}")
                    continue
        
        logger.info(f"Entity linking completed. Statistics: {self.stats}")
        logger.info(f"Links saved to {output_file}")

def main():
    """Main function for entity linker."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Link entities in recipe data to Wikipedia')
    parser.add_argument('--gazetteer', required=True, help='Gazetteer TSV file')
    parser.add_argument('--input', required=True, help='Input JSONL file with recipes')
    parser.add_argument('--output', required=True, help='Output JSONL file for entity links')
    
    args = parser.parse_args()
    
    logger.info("Starting Phase E: Entity Linker")
    
    try:
        linker = EntityLinker(args.gazetteer)
        linker.process_recipes_file(args.input, args.output)
        logger.info("Phase E (Entity Linker) completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Phase E (Entity Linker) failed: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())

