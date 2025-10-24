#!/usr/bin/env python3
"""
Wikipedia Entity Extractor for Culinary Domain
Extracts food-related entities (ingredients, cuisines, techniques, tools, condiments)
from Wikipedia dumps using streaming XML parsing.
"""

import argparse
import bz2
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import lxml
try:
    from lxml import etree
except ImportError:
    logger.error("lxml not found. Please install: pip3 install --user lxml")
    sys.exit(1)


class WikiCulinaryExtractor:
    """Extract culinary entities from Wikipedia dumps."""
    
    def __init__(self):
        # Infobox patterns we care about
        self.infobox_patterns = [
            re.compile(r'{{\s*Infobox\s+food', re.IGNORECASE),
            re.compile(r'{{\s*Infobox\s+prepared\s+food', re.IGNORECASE),
            re.compile(r'{{\s*Infobox\s+ingredient', re.IGNORECASE),
            re.compile(r'{{\s*Infobox\s+cuisine', re.IGNORECASE),
        ]
        
        # Blacklist patterns - skip these
        self.blacklist_titles = {
            # Geographic
            'aberdeen', 'andalusia', 'azores', 'berlin', 'brussels', 'brandenburg',
            'bavaria', 'bohemia', 'catalonia', 'prague', 'vienna', 'warsaw',
            # Non-food
            'apollo', 'apollo 10', 'apollo 11', 'boat', 'ship', 'aircraft', 
            'electromagnetic coil', 'hydrofoil', 'acupuncture',
            # People
            'christopher marlowe', 'erasmus darwin', 'ethan allen', 'francis bacon',
            # Fish species (not edible)
            'actinopterygii', 'northern cavefish', 'mexican tetra', 'galjoen', 'zebrafish',
            # Abstract concepts
            'food', 'cuisine', 'dessert', 'dairy product',
        }
        
        self.blacklist_patterns = [
            # Fish family names
            re.compile(r'idae$'),
            re.compile(r'\bcavefish\b', re.IGNORECASE),
            # Scientific names
            re.compile(r'^[A-Z][a-z]+ [a-z]+$'),  # "Genus species" format
        ]
        
        # Positive food signals (must have at least one)
        self.food_signals = [
            'food', 'cuisine', 'dish', 'ingredient', 'edible', 'cooking', 
            'culinary', 'recipe', 'meal', 'beverage', 'drink'
        ]
        
        # Category patterns for type detection
        self.category_patterns = {
            'ingredient': [
                'ingredients', 'vegetables', 'fruits', 'herbs', 'spices',
                'meat', 'fish', 'seafood', 'dairy products', 'cheese', 'grains',
                'legumes', 'nuts', 'edible plants', 'food ingredients',
                'cooking oils', 'sugars', 'flours', 'seeds', 'root vegetables'
            ],
            'cuisine': [
                'national cuisines', 'regional cuisines', 'cuisine by country',
                'cuisine by region', 'ethnic cuisines'
            ],
            'technique': [
                'cooking techniques', 'food preparation', 'culinary techniques',
                'food preparation techniques', 'cooking methods'
            ],
            'tool': [
                'cooking appliances', 'kitchen equipment', 'cookware',
                'cooking vessels', 'kitchen utensils'
            ],
            'condiment': [
                'condiments', 'dressings', 'food pastes'
            ],
            'dish': [
                'foods', 'dishes', 'salads', 'soups', 'desserts', 'cakes',
                'pies', 'breads', 'pastries'
            ]
        }
        
        # Keywords in title/abstract for type detection
        self.title_keywords = {
            'ingredient': ['bean', 'pepper', 'onion', 'garlic', 'tomato', 'flour', 
                          'sugar', 'salt', 'oil', 'butter', 'cheese', 'milk'],
            'cuisine': ['cuisine'],
            'technique': ['cooking', 'baking', 'roasting', 'grilling', 'frying', 
                         'boiling', 'braising', 'sautéing'],
            'tool': ['pan', 'pot', 'oven', 'grill', 'blender', 'mixer'],
            'condiment': ['sauce', 'dressing', 'mayo', 'ketchup', 'mustard']
        }
        
        # Stats
        self.stats = {
            'total_pages': 0,
            'food_pages': 0,
            'entities_by_type': defaultdict(int)
        }
        
        # Storage
        self.entities: Dict[str, Dict] = {}
    
    def is_food_related(self, title: str, text: str, categories: List[str]) -> Optional[str]:
        """
        Determine if page is food-related and return entity type.
        Returns: type string or None
        
        STRICTNESS IMPROVEMENTS (v2):
        - Require Infobox food OR strong category signals
        - Require at least one food_signal keyword in abstract/categories
        - Better person/location/concept blacklisting
        """
        # Skip disambiguation, lists, and technical pages
        title_lower = title.lower()
        if any(skip in title_lower for skip in ['disambiguation', 'list of', 'template:', 'category:', 'wikipedia:']):
            return None
        
        # BLACKLIST: Exact title match
        if title_lower in self.blacklist_titles:
            return None
        
        # BLACKLIST: Pattern match
        for pattern in self.blacklist_patterns:
            if pattern.search(title):
                return None
        
        # BLACKLIST: Skip people categories (very common false positive)
        categories_text = ' '.join(categories).lower()
        people_indicators = ['births', 'deaths', 'people', 'writers', 'poets', 'activists', 
                             'politicians', 'musicians', 'actors', 'scientists']
        if any(ind in categories_text for ind in people_indicators):
            # Unless it explicitly has food-related categories
            if not any(food in categories_text for food in ['foods', 'dishes', 'ingredients', 'cuisine']):
                return None
        
        # Require at least ONE positive food signal
        combined_text = (title_lower + ' ' + ' '.join(categories[:10]).lower()).lower()
        has_food_signal = any(signal in combined_text for signal in self.food_signals)
        
        if not has_food_signal:
            return None
        
        # Check for Infobox food (highest confidence)
        has_infobox = any(pattern.search(text) for pattern in self.infobox_patterns)
        
        if has_infobox:
            # Try to determine type from categories
            categories_lower = ' '.join(categories).lower()
            
            # Check category patterns (check 'dish' first, then others)
            for entity_type in ['dish', 'ingredient', 'cuisine', 'technique', 'tool', 'condiment']:
                if entity_type in self.category_patterns:
                    keywords = self.category_patterns[entity_type]
                    if any(kw in categories_lower for kw in keywords):
                        return entity_type
            
            # Check title keywords
            for entity_type, keywords in self.title_keywords.items():
                if any(kw in title_lower for kw in keywords):
                    return entity_type
            
            # Default to ingredient for infobox food (only if we have food signal)
            return 'ingredient'
        
        # NO INFOBOX: require stronger signals
        categories_lower = ' '.join(categories).lower()
        
        # Check for cuisine pages (ONLY if title ends with "cuisine")
        if title_lower.endswith('cuisine') or title_lower.endswith(' cuisine'):
            if title_lower.split()[-1] == 'cuisine':
                return 'cuisine'
        
        # For non-infobox pages, require at least 2 matching category keywords
        for entity_type, keywords in self.category_patterns.items():
            matches = sum(1 for kw in keywords if kw in categories_lower)
            if matches >= 2:  # Stricter: require 2+ category matches
                # Additional validation
                if entity_type == 'ingredient':
                    # Must have title keyword or abstract mention
                    if any(kw in title_lower for kw in self.title_keywords.get('ingredient', [])):
                        return entity_type
                elif entity_type == 'dish':
                    # Dishes must have explicit "foods" or "dishes" category
                    if 'foods' in categories_lower or 'dishes' in categories_lower:
                        return entity_type
                else:
                    return entity_type
        
        return None
    
    def extract_categories(self, text: str) -> List[str]:
        """Extract category names from wikitext."""
        # Pattern: [[Category:Something]]
        category_pattern = re.compile(r'\[\[Category:([^\]|]+)(?:\|[^\]]+)?\]\]', re.IGNORECASE)
        categories = []
        
        for match in category_pattern.finditer(text):
            cat_name = match.group(1).strip()
            if cat_name:
                categories.append(cat_name)
        
        return categories
    
    def extract_origin_from_categories(self, categories: List[str]) -> Dict:
        """Extract origin info from category names."""
        origin_info = {}
        
        for cat in categories:
            # "Crops originating from Peru" -> Peru
            if 'originating from' in cat.lower():
                match = re.search(r'originating from (.+)', cat, re.IGNORECASE)
                if match:
                    origin_info['origin_category'] = match.group(1).strip()
            
            # "Italian cuisine" -> Italy
            if cat.endswith('cuisine') and cat != 'Cuisine':
                cuisine_name = cat.replace(' cuisine', '').strip()
                if cuisine_name not in ['World', 'Regional', 'Ancient']:
                    if 'cuisine_region' not in origin_info:
                        origin_info['cuisine_region'] = cuisine_name
        
        return origin_info
    
    def extract_infobox_metadata(self, text: str) -> Dict:
        """Extract historical metadata from Infobox (place_of_origin, country, region, year)."""
        metadata = {}
        
        # Find Infobox
        infobox_match = re.search(r'\{\{Infobox[^}]*?\n(.*?)\n\}\}', text, re.DOTALL | re.IGNORECASE)
        if not infobox_match:
            return metadata
        
        infobox = infobox_match.group(0)
        
        # Extract fields
        fields = {
            'place_of_origin': r'\|\s*place_of_origin\s*=\s*([^\n|]+)',
            'country': r'\|\s*country\s*=\s*([^\n|]+)',
            'region': r'\|\s*region\s*=\s*([^\n|]+)',
            'year': r'\|\s*year\s*=\s*([^\n|]+)',
            'creator': r'\|\s*creator\s*=\s*([^\n|]+)',
        }
        
        for field_name, pattern in fields.items():
            match = re.search(pattern, infobox, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean wiki markup: [[Italy]] -> Italy, [[File:...|Italy]] -> Italy
                value = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', value)
                value = re.sub(r'\{\{[^}]+\}\}', '', value)  # Remove templates
                value = re.sub(r'<[^>]+>', '', value)  # Remove HTML
                value = value.strip()
                if value and value != '':
                    metadata[field_name] = value
        
        return metadata
    
    def extract_abstract(self, text: str, max_length: int = None) -> str:
        """Extract first paragraph as abstract, skipping Infobox and templates.
        
        Args:
            text: Wikipedia page text
            max_length: Maximum characters (None = full first paragraph)
        """
        lines = text.split('\n')
        abstract_parts = []
        inside_template = 0
        
        for line in lines:
            # Track template depth (nested {{...}})
            inside_template += line.count('{{') - line.count('}}')
            
            # Skip if inside template
            if inside_template > 0:
                continue
            
            # Stop at first section header
            if line.startswith('=='):
                break
            
            # Skip templates, categories, files
            if line.startswith('{{') or line.startswith('[[Category:') or line.startswith('[[File:'):
                continue
            
            # Skip lines starting with '|' (Infobox remnants)
            if line.strip().startswith('|'):
                continue
            
            # Remove wiki markup
            line = re.sub(r'\[\[([^|\]]+\|)?([^\]]+)\]\]', r'\2', line)
            line = re.sub(r"'''?([^']+)'''?", r'\1', line)
            line = re.sub(r'<[^>]+>', '', line)
            line = re.sub(r'\{\{[^}]+\}\}', '', line)  # Remove inline templates
            
            # Clean up
            line = line.strip()
            
            if line and not line.startswith('#') and not line.startswith('*'):
                abstract_parts.append(line)
                
                # Stop when we have enough (if limit set)
                if max_length is not None and len(' '.join(abstract_parts)) > max_length:
                    break
        
        abstract = ' '.join(abstract_parts)
        
        # Final cleanup: remove any remaining markup
        abstract = re.sub(r'\[\[|\]\]', '', abstract)
        abstract = re.sub(r'\{\{|\}\}', '', abstract)
        abstract = re.sub(r'\s+', ' ', abstract)
        
        # Truncate if needed
        if max_length is not None and len(abstract) > max_length:
            # Find sentence boundary
            sentences = re.split(r'[.!?]\s+', abstract[:max_length*2])
            abstract = sentences[0] + '.' if sentences else abstract[:max_length]
        
        return abstract.strip()
    
    def normalize_surface(self, text: str) -> str:
        """Normalize surface form for matching."""
        # Lowercase, remove accents (simple approach)
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        return text.strip()
    
    def process_page(self, page_elem) -> Optional[Dict]:
        """Process a single Wikipedia page."""
        # Extract basic fields
        title = page_elem.findtext(".//{*}title")
        text = page_elem.findtext(".//{*}revision/{*}text")
        
        if not title or not text:
            return None
        
        # Extract categories
        categories = self.extract_categories(text)
        
        # Check if food-related
        entity_type = self.is_food_related(title, text, categories)
        
        if not entity_type:
            return None
        
        # Extract full abstract (complete first paragraph, no limit)
        abstract = self.extract_abstract(text, max_length=None)
        
        # Extract historical metadata from Infobox
        metadata = self.extract_infobox_metadata(text)
        
        # Extract origin from categories
        category_origin = self.extract_origin_from_categories(categories)
        
        # Merge metadata (Infobox has priority over category-derived)
        merged_metadata = {**category_origin, **metadata}
        
        # Create entity
        entity = {
            'id': title.replace(' ', '_'),
            'title': title,
            'type': entity_type,
            'categories': categories,
            'abstract': abstract,
            'redirects': [],  # Will be populated later
            **merged_metadata  # Add all historical metadata
        }
        
        self.stats['food_pages'] += 1
        self.stats['entities_by_type'][entity_type] += 1
        
        return entity
    
    def stream_dump(self, dump_file: Path, limit: Optional[int] = None):
        """Stream through Wikipedia dump and extract entities."""
        logger.info(f"Streaming dump: {dump_file}")
        logger.info(f"Limit: {limit if limit else 'None (full dump)'}")
        
        with bz2.open(dump_file, 'rb') as f:
            context = etree.iterparse(f, events=('end',), tag='{*}page')
            
            for event, page_elem in context:
                self.stats['total_pages'] += 1
                
                # Process page
                entity = self.process_page(page_elem)
                
                if entity:
                    self.entities[entity['title']] = entity
                
                # Clear element to free memory
                page_elem.clear()
                while page_elem.getprevious() is not None:
                    del page_elem.getparent()[0]
                
                # Progress logging
                if self.stats['total_pages'] % 1000 == 0:
                    logger.info(f"Processed {self.stats['total_pages']:,} pages, "
                              f"found {self.stats['food_pages']} food entities")
                
                # Check limit
                if limit and self.stats['total_pages'] >= limit:
                    logger.info(f"Reached limit of {limit} pages")
                    break
        
        logger.info(f"Finished streaming. Total: {self.stats['total_pages']:,} pages, "
                   f"{self.stats['food_pages']} food entities")
    
    def build_gazetteer(self) -> List[Tuple[str, str, str, str]]:
        """
        Build gazetteer: (surface, wiki_title, type, norm)
        Returns list of tuples for TSV output.
        """
        gazetteer = []
        
        for title, entity in self.entities.items():
            entity_type = entity['type']
            
            # Add main title
            surface = title
            norm = self.normalize_surface(surface)
            gazetteer.append((surface, title, entity_type, norm))
        
        logger.info(f"Built gazetteer with {len(gazetteer)} entries")
        return gazetteer
    
    def save_gazetteer(self, gazetteer: List[Tuple], output_file: Path):
        """Save gazetteer to TSV file."""
        logger.info(f"Saving gazetteer to {output_file}")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("surface\twiki_title\ttype\tnorm\n")
            
            # Entries
            for surface, wiki_title, entity_type, norm in sorted(gazetteer):
                f.write(f"{surface}\t{wiki_title}\t{entity_type}\t{norm}\n")
        
        logger.info(f"Saved {len(gazetteer)} gazetteer entries")
    
    def save_entities_jsonl(self, output_file: Path):
        """Save entities to JSONL file."""
        logger.info(f"Saving entities to {output_file}")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for entity in self.entities.values():
                f.write(json.dumps(entity, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(self.entities)} entities")
    
    def print_stats(self):
        """Print extraction statistics."""
        print("\n" + "="*60)
        print("EXTRACTION STATISTICS")
        print("="*60)
        print(f"Total pages processed:  {self.stats['total_pages']:,}")
        print(f"Food entities found:    {self.stats['food_pages']:,}")
        print("\nEntities by type:")
        for entity_type, count in sorted(self.stats['entities_by_type'].items()):
            print(f"  {entity_type:15s} {count:,}")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Extract culinary entities from Wikipedia dump'
    )
    parser.add_argument(
        '--dump',
        required=True,
        type=Path,
        help='Path to enwiki-latest-pages-articles-multistream.xml.bz2'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of pages to process (for testing)'
    )
    parser.add_argument(
        '--out-gazetteer',
        type=Path,
        default=Path('entities/wiki_gazetteer.tsv'),
        help='Output path for gazetteer TSV'
    )
    parser.add_argument(
        '--out-jsonl',
        type=Path,
        default=Path('data/normalized/wiki_culinary.jsonl'),
        help='Output path for entities JSONL'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input files
    if not args.dump.exists():
        logger.error(f"Dump file not found: {args.dump}")
        sys.exit(1)
    
    # Create extractor
    extractor = WikiCulinaryExtractor()
    
    # Stream and extract
    extractor.stream_dump(args.dump, limit=args.limit)
    
    # Build gazetteer
    gazetteer = extractor.build_gazetteer()
    
    # Save outputs
    extractor.save_gazetteer(gazetteer, args.out_gazetteer)
    extractor.save_entities_jsonl(args.out_jsonl)
    
    # Print stats
    extractor.print_stats()
    
    logger.info("✅ Extraction completed successfully!")


if __name__ == '__main__':
    main()
