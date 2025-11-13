#!/usr/bin/env python3
"""
PySpark Wikipedia Culinary Parser
Extracts food-related articles from enwiki XML dumps using PySpark.

Outputs:
1. wiki_culinary.jsonl - Extracted culinary articles with metadata
2. wiki_gazetteer.tsv - Entity gazetteer for linking

Usage:
    spark-submit spark_jobs/enwiki_spark_parser.py \
        --input data/enwiki/enwiki-latest-pages-articles11.xml-p5399367p6899366.bz2 \
        --output-jsonl data/normalized/wiki_culinary.jsonl \
        --output-gazetteer entities/wiki_gazetteer.tsv \
        --limit 1000
"""

import argparse
import json
import logging
import re
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import udf, col, explode
from pyspark.sql.types import (
    StructType, StructField, StringType, ArrayType, IntegerType, BooleanType, MapType
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WikiXMLParser:
    """Parser for Wikipedia XML page elements."""
    
    # Infobox patterns
    INFOBOX_PATTERNS = [
        re.compile(r'{{\s*Infobox\s+food', re.IGNORECASE),
        re.compile(r'{{\s*Infobox\s+prepared\s+food', re.IGNORECASE),
        re.compile(r'{{\s*Infobox\s+ingredient', re.IGNORECASE),
        re.compile(r'{{\s*Infobox\s+cuisine', re.IGNORECASE),
    ]
    
    # Blacklist (skip these)
    BLACKLIST_TITLES = {
        'aberdeen', 'andalusia', 'azores', 'berlin', 'brussels', 'brandenburg',
        'bavaria', 'bohemia', 'catalonia', 'prague', 'vienna', 'warsaw',
        'apollo', 'apollo 10', 'apollo 11', 'boat', 'ship', 'aircraft',
        'electromagnetic coil', 'hydrofoil', 'acupuncture',
        'christopher marlowe', 'erasmus darwin', 'ethan allen', 'francis bacon',
        'actinopterygii', 'northern cavefish', 'mexican tetra', 'galjoen', 'zebrafish',
        'food', 'cuisine', 'dessert', 'dairy product',
    }
    
    BLACKLIST_PATTERNS = [
        re.compile(r'idae$'),  # Fish families
        re.compile(r'\bcavefish\b', re.IGNORECASE),
        re.compile(r'^[A-Z][a-z]+ [a-z]+$'),  # Scientific names
    ]
    
    # Positive food signals
    FOOD_SIGNALS = [
        'food', 'cuisine', 'dish', 'ingredient', 'edible', 'cooking',
        'culinary', 'recipe', 'meal', 'beverage', 'drink'
    ]
    
    # Category patterns for type detection
    CATEGORY_PATTERNS = {
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
            'condiments', 'dressings', 'food pastes', 'sauces'
        ],
        'dish': [
            'foods', 'dishes', 'salads', 'soups', 'desserts', 'cakes',
            'pies', 'breads', 'pastries'
        ]
    }
    
    # Common ingredients for extraction
    INGREDIENT_KEYWORDS = [
        'garlic', 'onion', 'tomato', 'pepper', 'salt', 'sugar', 'flour',
        'butter', 'oil', 'cheese', 'milk', 'egg', 'chicken', 'beef',
        'pork', 'fish', 'rice', 'pasta', 'bread', 'potato', 'carrot',
        'basil', 'oregano', 'thyme', 'cumin', 'coriander', 'ginger',
        'lemon', 'lime', 'vinegar', 'soy sauce', 'cream', 'yogurt'
    ]
    
    # Pre-compiled regex patterns for performance
    _TITLE_PATTERN = re.compile(r'<title>(.+?)</title>', re.DOTALL)
    _ID_PATTERN = re.compile(r'<id>(\d+)</id>')
    _REDIRECT_PATTERN = re.compile(r'<redirect title="(.+?)"')
    _TEXT_PATTERN = re.compile(r'<text[^>]*>(.+?)</text>', re.DOTALL)
    
    @staticmethod
    def parse_page_xml(xml_text: str) -> Optional[Dict]:
        """
        Parse a single Wikipedia page XML block.
        
        Optimized with pre-compiled regex patterns.
        
        Returns dict with:
        - wiki_id, wiki_title, text, redirect
        """
        if not xml_text or '<page>' not in xml_text:
            return None
        
        try:
            # Extract title (using pre-compiled pattern)
            title_match = WikiXMLParser._TITLE_PATTERN.search(xml_text)
            if not title_match:
                return None
            title = title_match.group(1).strip()
            
            # Extract id
            id_match = WikiXMLParser._ID_PATTERN.search(xml_text)
            page_id = id_match.group(1) if id_match else None
            
            # Check for redirect (skip redirects early for performance)
            redirect_match = WikiXMLParser._REDIRECT_PATTERN.search(xml_text)
            if redirect_match:
                return {
                    'wiki_id': page_id,
                    'wiki_title': title,
                    'text': '',
                    'redirect': redirect_match.group(1),
                    'is_redirect': True
                }
            
            # Extract text content
            text_match = WikiXMLParser._TEXT_PATTERN.search(xml_text)
            if not text_match:
                return None
            text = text_match.group(1).strip()
            
            return {
                'wiki_id': page_id,
                'wiki_title': title,
                'text': text,
                'redirect': None,
                'is_redirect': False
            }
        
        except Exception as e:
            # Silent fail for performance (can log if needed)
            return None
    
    # Pre-compiled category pattern
    _CATEGORY_PATTERN = re.compile(r'\[\[Category:([^\]|]+)(?:\|[^\]]+)?\]\]', re.IGNORECASE)
    
    @staticmethod
    def extract_categories(text: str) -> List[str]:
        """Extract category names from wikitext (optimized)."""
        categories = []
        
        for match in WikiXMLParser._CATEGORY_PATTERN.finditer(text):
            cat_name = match.group(1).strip()
            if cat_name:
                categories.append(cat_name)
        
        return categories
    
    @staticmethod
    def extract_abstract(text: str, max_sentences: int = 3) -> str:
        """Extract first paragraph as abstract, skipping templates."""
        lines = text.split('\n')
        abstract_parts = []
        inside_template = 0
        
        for line in lines:
            # Track template depth
            inside_template += line.count('{{') - line.count('}}')
            
            if inside_template > 0:
                continue
            
            # Stop at first section header
            if line.startswith('=='):
                break
            
            # Skip templates, categories, files
            if (line.startswith('{{') or line.startswith('[[Category:') or 
                line.startswith('[[File:') or line.strip().startswith('|')):
                continue
            
            # Remove wiki markup
            line = re.sub(r'\[\[([^|\]]+\|)?([^\]]+)\]\]', r'\2', line)
            line = re.sub(r"'''?([^']+)'''?", r'\1', line)
            line = re.sub(r'<[^>]+>', '', line)
            line = re.sub(r'\{\{[^}]+\}\}', '', line)
            
            line = line.strip()
            
            if line and not line.startswith('#') and not line.startswith('*'):
                abstract_parts.append(line)
                
                # Stop after enough sentences
                if len(abstract_parts) >= max_sentences:
                    break
        
        abstract = ' '.join(abstract_parts)
        # More aggressive cleaning
        abstract = re.sub(r'\[\[|\]\]|\{\{|\}\}', '', abstract)
        abstract = re.sub(r'<ref[^>]*>.*?</ref>', '', abstract)  # Remove ref tags
        abstract = re.sub(r'<ref[^>]*/?>', '', abstract)  # Remove self-closing refs
        abstract = re.sub(r'&lt;/?(ref|br|div|span)[^&]*?&gt;', '', abstract)  # Remove HTML entities
        
        # Decode HTML entities
        import html
        abstract = html.unescape(abstract)
        
        # Remove any remaining markup
        abstract = re.sub(r'<[^>]+>', '', abstract)  # Remove any HTML tags
        abstract = re.sub(r'\s+', ' ', abstract)
        
        return abstract.strip()
    
    @staticmethod
    def extract_infobox_field(text: str, field_name: str) -> Optional[str]:
        """Extract a field from Infobox."""
        infobox_match = re.search(r'\{\{Infobox[^}]*?\n(.*?)\n\}\}', text, re.DOTALL | re.IGNORECASE)
        if not infobox_match:
            return None
        
        infobox = infobox_match.group(0)
        pattern = r'\|\s*' + field_name + r'\s*=\s*([^\n|]+)'
        match = re.search(pattern, infobox, re.IGNORECASE)
        
        if match:
            value = match.group(1).strip()
            # Clean wiki markup
            value = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', value)
            value = re.sub(r'\{\{[^}]+\}\}', '', value)
            value = re.sub(r'<[^>]+>', '', value)
            value = value.strip()
            return value if value else None
        
        return None
    
    @staticmethod
    def extract_complete_infobox(text: str) -> Dict[str, str]:
        """Extract ALL fields from Infobox as a dictionary."""
        infobox_match = re.search(r'\{\{Infobox[^}]*?\n(.*?)\n\}\}', text, re.DOTALL | re.IGNORECASE)
        if not infobox_match:
            return {}
        
        infobox = infobox_match.group(1)
        fields = {}
        
        # Extract all | field = value pairs
        field_pattern = r'\|\s*([^=|]+?)\s*=\s*([^\n|]*(?:\n(?!\|)[^\n]*)*)'
        for match in re.finditer(field_pattern, infobox):
            field_name = match.group(1).strip()
            value = match.group(2).strip()
            
            if value:
                # Remove references first
                value = re.sub(r'<ref[^>]*>.*?</ref>', '', value, flags=re.DOTALL)
                value = re.sub(r'<ref[^>]*/?>', '', value)
                
                # Clean wiki markup
                value = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', value)
                value = re.sub(r'\{\{[^}]+\}\}', '', value)
                value = re.sub(r'<[^>]+>', '', value)
                
                # Decode HTML entities
                import html
                value = html.unescape(value)
                
                value = re.sub(r'\s+', ' ', value).strip()
                
                if value:
                    fields[field_name] = value
        
        return fields
    
    @staticmethod
    def extract_history_section(text: str) -> Optional[str]:
        """Extract History/Origins section text."""
        # Look for ==History== or ==Origins== section
        history_patterns = [
            r'==\s*History\s*==\s*\n(.*?)(?:\n==|$)',
            r'==\s*Origins\s*==\s*\n(.*?)(?:\n==|$)',
            r'==\s*Origin\s*==\s*\n(.*?)(?:\n==|$)',
        ]
        
        for pattern in history_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                history_text = match.group(1).strip()
                
                # Clean up the text
                # Remove references
                history_text = re.sub(r'<ref[^>]*>.*?</ref>', '', history_text, flags=re.DOTALL)
                history_text = re.sub(r'<ref[^>]*/?>', '', history_text)
                
                # Remove wiki markup
                history_text = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', history_text)
                history_text = re.sub(r"'''?([^']+)'''?", r'\1', history_text)
                history_text = re.sub(r'\{\{[^}]+\}\}', '', history_text)
                
                # Decode HTML entities
                import html
                history_text = html.unescape(history_text)
                
                # Remove any remaining markup
                history_text = re.sub(r'<[^>]+>', '', history_text)
                history_text = re.sub(r'\s+', ' ', history_text)
                
                # Limit to first 2-3 paragraphs (max ~800 chars)
                if len(history_text) > 800:
                    sentences = re.split(r'[.!?]\s+', history_text[:1200])
                    history_text = '. '.join(sentences[:5]) + '.'
                
                return history_text.strip() if history_text.strip() else None
        
        return None
    
    @staticmethod
    def extract_ingredients_mentioned(text: str, abstract: str) -> List[str]:
        """Extract ingredients mentioned in text."""
        combined_text = (text[:2000] + ' ' + abstract).lower()
        found = []
        
        for ingredient in WikiXMLParser.INGREDIENT_KEYWORDS:
            if ingredient in combined_text:
                found.append(ingredient)
        
        return found
    
    @staticmethod
    def detect_type(title: str, text: str, categories: List[str]) -> Optional[str]:
        """Detect entity type based on title, text, and categories."""
        title_lower = title.lower()
        
        # Check if it's food-related first
        if not WikiXMLParser.is_food_related(title, text, categories):
            return None
        
        categories_lower = ' '.join(categories).lower()
        
        # Check category patterns (dish first, then others)
        for entity_type in ['dish', 'ingredient', 'cuisine', 'technique', 'tool', 'condiment']:
            if entity_type in WikiXMLParser.CATEGORY_PATTERNS:
                keywords = WikiXMLParser.CATEGORY_PATTERNS[entity_type]
                if any(kw in categories_lower for kw in keywords):
                    return entity_type
        
        # Check for Infobox
        has_infobox = any(pattern.search(text) for pattern in WikiXMLParser.INFOBOX_PATTERNS)
        if has_infobox:
            return 'ingredient'  # Default for infobox food
        
        # Check if it's a cuisine by title
        if title_lower.endswith('cuisine'):
            return 'cuisine'
        
        return None
    
    @staticmethod
    def is_food_related(title: str, text: str, categories: List[str]) -> bool:
        """Check if page is food-related."""
        title_lower = title.lower()
        
        # Skip disambiguation, lists
        if any(skip in title_lower for skip in ['disambiguation', 'list of', 'template:', 'category:', 'wikipedia:']):
            return False
        
        # Blacklist exact matches
        if title_lower in WikiXMLParser.BLACKLIST_TITLES:
            return False
        
        # Blacklist patterns
        for pattern in WikiXMLParser.BLACKLIST_PATTERNS:
            if pattern.search(title):
                return False
        
        # Blacklist people categories
        categories_text = ' '.join(categories).lower()
        people_indicators = ['births', 'deaths', 'people', 'writers', 'poets', 'activists',
                             'politicians', 'musicians', 'actors', 'scientists']
        if any(ind in categories_text for ind in people_indicators):
            if not any(food in categories_text for food in ['foods', 'dishes', 'ingredients', 'cuisine']):
                return False
        
        # Require at least one food signal
        combined_text = (title_lower + ' ' + ' '.join(categories[:10]).lower())
        has_food_signal = any(signal in combined_text for signal in WikiXMLParser.FOOD_SIGNALS)
        
        return has_food_signal
    
    @staticmethod
    def process_page(page_data: Dict) -> Optional[Dict]:
        """Process parsed page and extract culinary metadata."""
        if not page_data or page_data.get('is_redirect', False):
            return None
        
        title = page_data['wiki_title']
        text = page_data['text']
        page_id = page_data['wiki_id']
        
        # Extract categories
        categories = WikiXMLParser.extract_categories(text)
        
        # Detect type
        entity_type = WikiXMLParser.detect_type(title, text, categories)
        if not entity_type:
            return None
        
        # Extract metadata
        abstract = WikiXMLParser.extract_abstract(text)
        
        # Extract complete infobox
        infobox_data = WikiXMLParser.extract_complete_infobox(text)
        
        # Extract specific fields (with fallbacks)
        origin_country = infobox_data.get('place_of_origin') or \
                        infobox_data.get('country') or \
                        infobox_data.get('origin')
        origin_region = infobox_data.get('region')
        year_origin = infobox_data.get('year') or infobox_data.get('created')
        
        # Extract history section
        history = WikiXMLParser.extract_history_section(text)
        
        # Extract ingredients mentioned
        ingredients_mentioned = WikiXMLParser.extract_ingredients_mentioned(text, abstract)
        
        return {
            'wiki_id': page_id,
            'wiki_title': title,
            'type': entity_type,
            'abstract': abstract,
            'history': history,
            'infobox': infobox_data,
            'origin_country': origin_country,
            'origin_region': origin_region,
            'year_origin': year_origin,
            'categories': categories,
            'ingredients_mentioned': ingredients_mentioned
        }


def split_xml_pages(text_line: str) -> List[str]:
    """
    Split concatenated XML text into individual <page>...</page> blocks.
    """
    pages = []
    page_pattern = re.compile(r'<page>.*?</page>', re.DOTALL)
    
    for match in page_pattern.finditer(text_line):
        pages.append(match.group(0))
    
    return pages


def main():
    parser = argparse.ArgumentParser(
        description='PySpark Wikipedia Culinary Parser'
    )
    parser.add_argument(
        '--input',
        required=True,
        type=str,
        help='Path to enwiki XML dump (.bz2)'
    )
    parser.add_argument(
        '--output-jsonl',
        type=str,
        default='data/normalized/wiki_culinary.jsonl',
        help='Output path for culinary articles JSONL'
    )
    parser.add_argument(
        '--output-gazetteer',
        type=str,
        default='entities/wiki_gazetteer.tsv',
        help='Output path for gazetteer TSV'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of pages to process (for testing)'
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("PySpark Wikipedia Culinary Parser")
    logger.info("="*60)
    logger.info(f"Input: {args.input}")
    logger.info(f"Output JSONL: {args.output_jsonl}")
    logger.info(f"Output Gazetteer: {args.output_gazetteer}")
    logger.info(f"Limit: {args.limit if args.limit else 'None (full dump)'}")
    logger.info("="*60)
    
    # Create Spark session with minimal memory (we process in Python, not Spark)
    spark = SparkSession.builder \
        .appName("WikipediaCulinaryParser") \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "2g") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        # STREAMING APPROACH: Process file line-by-line to avoid OOM on 20GB file
        logger.info("Reading XML dump (streaming mode to avoid OutOfMemoryError)...")
        
        def stream_parse_xml():
            """Stream parse bz2 file without loading entire file into memory.
            
            Optimizations:
            - Streaming I/O (no full file load)
            - Progress tracking every 100k pages
            - Batch processing for Row creation
            - Time estimation
            """
            import bz2
            import time
            
            logger.info(f"Opening compressed file: {args.input}")
            logger.info("Starting streaming parse (this will take 2-4 hours for full dump)...")
            
            start_time = time.time()
            results = []
            page_buffer = []
            in_page = False
            pages_processed = 0
            last_log_time = start_time
            last_log_pages = 0
            
            # Progress logging intervals
            LOG_INTERVAL = 100000  # Log every 100k pages
            
            # Open and decompress on the fly (line-by-line streaming)
            with bz2.open(args.input, 'rt', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if '<page>' in line:
                        in_page = True
                        page_buffer = [line]
                    elif in_page:
                        page_buffer.append(line)
                        if '</page>' in line:
                            # Complete page found
                            page_xml = ''.join(page_buffer)
                            pages_processed += 1
                            
                            # Parse page (only if potentially culinary)
                            page_data = WikiXMLParser.parse_page_xml(page_xml)
                            if page_data:
                                # Process page (filter culinary)
                                result = WikiXMLParser.process_page(page_data)
                                if result:
                                    results.append(Row(**result))
                            
                            # Reset buffer
                            in_page = False
                            page_buffer = []
                            
                            # Progress logging every 100k pages
                            if pages_processed % LOG_INTERVAL == 0:
                                current_time = time.time()
                                elapsed = current_time - start_time
                                elapsed_since_log = current_time - last_log_time
                                pages_since_log = pages_processed - last_log_pages
                                
                                # Calculate speed
                                speed = pages_since_log / elapsed_since_log if elapsed_since_log > 0 else 0
                                
                                # Estimate total time (rough estimate based on 6M pages)
                                if speed > 0:
                                    estimated_total_pages = 6000000
                                    remaining_pages = estimated_total_pages - pages_processed
                                    eta_seconds = remaining_pages / speed
                                    eta_hours = eta_seconds / 3600
                                    
                                    logger.info(f"Progress: {pages_processed:,} pages processed | "
                                               f"{len(results):,} culinary articles found | "
                                               f"Speed: {speed:.0f} pages/sec | "
                                               f"Elapsed: {elapsed/60:.1f} min | "
                                               f"ETA: {eta_hours:.1f} hours")
                                else:
                                    logger.info(f"Progress: {pages_processed:,} pages processed | "
                                               f"{len(results):,} culinary articles found | "
                                               f"Elapsed: {elapsed/60:.1f} min")
                                
                                last_log_time = current_time
                                last_log_pages = pages_processed
                            
                            # Also log every 1000 culinary articles found
                            if len(results) > 0 and len(results) % 1000 == 0:
                                logger.info(f"✓ Found {len(results):,} culinary articles "
                                           f"(from {pages_processed:,} total pages)")
                            
                            # Check limit
                            if args.limit and pages_processed >= args.limit:
                                logger.info(f"Reached limit of {args.limit} pages")
                                break
            
            total_time = time.time() - start_time
            logger.info(f"")
            logger.info(f"{'='*60}")
            logger.info(f"Parsing completed!")
            logger.info(f"Total time: {total_time/60:.1f} minutes ({total_time/3600:.2f} hours)")
            logger.info(f"Total pages processed: {pages_processed:,}")
            logger.info(f"Culinary articles found: {len(results):,}")
            logger.info(f"Conversion rate: {100*len(results)/pages_processed:.3f}%")
            logger.info(f"Average speed: {pages_processed/total_time:.0f} pages/sec")
            logger.info(f"{'='*60}")
            
            return results
        
        # Process pages (stream in main Python process, not Spark to avoid OOM)
        logger.info("Parsing and filtering pages...")
        culinary_articles = stream_parse_xml()
        
        # Convert to RDD (small dataset now, only culinary articles)
        rdd_pages = spark.sparkContext.parallelize(culinary_articles)
        
        # Convert to DataFrame
        schema = StructType([
            StructField("wiki_id", StringType(), True),
            StructField("wiki_title", StringType(), True),
            StructField("type", StringType(), True),
            StructField("abstract", StringType(), True),
            StructField("history", StringType(), True),
            StructField("infobox", MapType(StringType(), StringType()), True),
            StructField("origin_country", StringType(), True),
            StructField("origin_region", StringType(), True),
            StructField("year_origin", StringType(), True),
            StructField("categories", ArrayType(StringType()), True),
            StructField("ingredients_mentioned", ArrayType(StringType()), True),
        ])
        
        df_pages = spark.createDataFrame(rdd_pages, schema=schema)
        
        # Cache for reuse
        df_pages.cache()
        
        total_count = df_pages.count()
        logger.info(f"Found {total_count} culinary articles")
        
        if total_count == 0:
            logger.warning("No culinary articles found! Check filters.")
            return
        
        # Show type distribution
        logger.info("\n" + "="*60)
        logger.info("TYPE DISTRIBUTION:")
        logger.info("="*60)
        type_dist = df_pages.groupBy("type").count().orderBy("count", ascending=False)
        type_dist.show(truncate=False)
        
        # Show sample
        logger.info("\n" + "="*60)
        logger.info("SAMPLE ARTICLES:")
        logger.info("="*60)
        df_pages.select("wiki_title", "type", "origin_country").show(10, truncate=False)
        
        # Show articles with history
        logger.info("\n" + "="*60)
        logger.info("ARTICLES WITH HISTORY SECTION:")
        logger.info("="*60)
        articles_with_history = df_pages.filter(col("history").isNotNull())
        history_count = articles_with_history.count()
        logger.info(f"Count: {history_count} ({100*history_count/total_count:.1f}%)")
        if history_count > 0:
            logger.info("\nSample:")
            articles_with_history.select("wiki_title", "type").show(5, truncate=False)
        
        # Save JSONL
        logger.info(f"\nSaving JSONL to {args.output_jsonl}...")
        output_jsonl_path = Path(args.output_jsonl)
        output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON strings and collect
        json_rdd = df_pages.rdd.map(lambda row: json.dumps(row.asDict(), ensure_ascii=False))
        json_lines = json_rdd.collect()
        
        with open(args.output_jsonl, 'w', encoding='utf-8') as f:
            for line in json_lines:
                f.write(line + '\n')
        
        logger.info(f"Saved {len(json_lines)} articles to JSONL")
        
        # Build gazetteer
        logger.info(f"\nBuilding gazetteer...")
        
        def normalize_surface(text: str) -> str:
            """Normalize surface form."""
            text = text.lower()
            text = re.sub(r'[^\w\s-]', '', text)
            return text.strip()
        
        gazetteer_entries = []
        for row in df_pages.collect():
            title = row['wiki_title']
            entity_type = row['type']
            surface = title
            norm = normalize_surface(surface)
            gazetteer_entries.append((surface, title, entity_type, norm))
        
        # Save gazetteer
        output_gaz_path = Path(args.output_gazetteer)
        output_gaz_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(args.output_gazetteer, 'w', encoding='utf-8') as f:
            f.write("surface\twiki_title\ttype\tnorm\n")
            for surface, wiki_title, entity_type, norm in sorted(gazetteer_entries):
                f.write(f"{surface}\t{wiki_title}\t{entity_type}\t{norm}\n")
        
        logger.info(f"Saved {len(gazetteer_entries)} entries to gazetteer")
        
        # Print statistics
        logger.info("\n" + "="*60)
        logger.info("STATISTICS")
        logger.info("="*60)
        logger.info(f"Total culinary articles: {total_count}")
        
        type_counts = df_pages.groupBy("type").count().collect()
        logger.info("\nBy type:")
        for row in sorted(type_counts, key=lambda x: x['count'], reverse=True):
            logger.info(f"  {row['type']:15s} {row['count']:,}")
        
        logger.info("="*60)
        logger.info("\n✅ Processing completed successfully!")
        
    finally:
        spark.stop()


if __name__ == '__main__':
    main()
