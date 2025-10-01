#!/usr/bin/env python3
"""
Ingredient link extractor - extracts canonical ingredient names from food.com HTML links.
Parses <a href="/about/ingredient-ID">ingredient name</a> patterns.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Set
import json

logger = logging.getLogger(__name__)


class IngredientExtractor:
    """Extract and normalize ingredients from food.com ingredient links."""
    
    def __init__(self):
        self.ingredient_pattern = re.compile(
            r'<a\s+href="/about/([^"]+?)-(\d+)">([^<]+)</a>',
            re.IGNORECASE
        )
    
    def extract_from_html(self, html_content: str) -> Set[tuple]:
        """
        Extract ingredient links from HTML content.
        Returns set of tuples: (ingredient_id, ingredient_slug, ingredient_name)
        """
        ingredients = set()
        
        for match in self.ingredient_pattern.finditer(html_content):
            slug = match.group(1)
            ingredient_id = match.group(2)
            name = match.group(3).strip()
            
            if name and len(name) > 1:
                ingredients.add((ingredient_id, slug, name))
        
        return ingredients
    
    def extract_from_raw_files(self, raw_dir: Path) -> Dict[str, str]:
        """
        Extract all unique ingredients from raw HTML files.
        Returns dict mapping ingredient_id -> ingredient_name (canonical)
        """
        ingredient_map = {}
        
        # Find all HTML files
        html_files = list(raw_dir.glob('**/*.html'))
        logger.info(f"Processing {len(html_files)} HTML files for ingredient extraction")
        
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                    
                ingredients = self.extract_from_html(html_content)
                
                for ing_id, slug, name in ingredients:
                    # If we already have this ingredient, keep the shorter/cleaner name
                    if ing_id in ingredient_map:
                        existing = ingredient_map[ing_id]
                        # Prefer shorter names (usually more canonical)
                        if len(name) < len(existing):
                            ingredient_map[ing_id] = name
                    else:
                        ingredient_map[ing_id] = name
                        
            except Exception as e:
                logger.debug(f"Error processing {html_file}: {e}")
                continue
        
        logger.info(f"Extracted {len(ingredient_map)} unique ingredients")
        return ingredient_map
    
    def save_ingredient_map(self, ingredient_map: Dict[str, str], output_file: Path):
        """Save ingredient mapping to a JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ingredient_map, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved ingredient map to {output_file}")


def main():
    """CLI for extracting ingredients from raw HTML files."""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Extract canonical ingredients from raw HTML')
    parser.add_argument(
        '--raw-dir',
        type=Path,
        default=Path('data/raw/www.food.com'),
        help='Directory containing raw HTML files'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/entities/ingredient_map.json'),
        help='Output file for ingredient mapping'
    )
    
    args = parser.parse_args()
    
    # Create output directory if needed
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract ingredients
    extractor = IngredientExtractor()
    ingredient_map = extractor.extract_from_raw_files(args.raw_dir)
    
    # Save results
    extractor.save_ingredient_map(ingredient_map, args.output)
    
    # Print some stats
    print(f"\nExtracted {len(ingredient_map)} unique ingredients")
    print(f"\nSample ingredients:")
    for i, (ing_id, name) in enumerate(sorted(ingredient_map.items())[:20]):
        print(f"  {ing_id}: {name}")


if __name__ == '__main__':
    main()
