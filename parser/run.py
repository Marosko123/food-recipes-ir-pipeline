"""
Phase C: Parser & Normalization
Extracts structured recipe data from downloaded HTML files.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import time

from .json_ld_parser import JSONLDParser
from .html_parser import HTMLParser

def setup_logging(level: int = logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/parse.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_recipe_file(html_file: Path, url: str) -> Dict[str, Any]:
    """Parse a single recipe HTML file."""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Try JSON-LD parser first
        json_ld_parser = JSONLDParser()
        recipe = json_ld_parser.parse_recipe(html_content, url)
        
        # If JSON-LD parsing failed or returned empty data, try HTML parser
        if not recipe.get('title') or not recipe.get('ingredients'):
            logger.debug(f"JSON-LD parsing failed for {url}, trying HTML parser")
            html_parser = HTMLParser()
            recipe = html_parser.parse_recipe(html_content, url)
        
        return recipe
        
    except Exception as e:
        logger.error(f"Error parsing {html_file}: {e}")
        return None

def run_parse_phase(args) -> Dict[str, Any]:
    """Run Phase C: Parse and normalize recipe data."""
    # TODO: Add multi-threading for faster parsing
    logger.info("Starting Phase C: Parser & Normalization")
    
    # Create output directory
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find HTML files
    raw_dir = Path(args.raw)
    if not raw_dir.exists():
        logger.error(f"Raw directory not found: {raw_dir}")
        return {"error": "Raw directory not found"}
    
    html_files = list(raw_dir.rglob("*.html"))
    if not html_files:
        logger.error(f"No HTML files found in {raw_dir}")
        return {"error": "No HTML files found"}
    
    logger.info(f"Found {len(html_files)} HTML files to parse")
    
    # Parse files
    recipes = []
    stats = {
        "total_files": len(html_files),
        "parsed_successfully": 0,
        "parse_failed": 0,
        "json_ld_success": 0,
        "html_fallback_success": 0,
        "start_time": time.time()
    }
    
    for i, html_file in enumerate(html_files):
        try:
            # Extract URL from file path
            # Assuming structure: data/raw/www.food.com/{doc_id}.html
            doc_id = html_file.stem
            url = f"https://www.food.com/recipe/{doc_id}"
            
            logger.info(f"Parsing {i+1}/{len(html_files)}: {html_file.name}")
            
            # FIXME: Some recipes have malformed JSON-LD, handle gracefully
            recipe = parse_recipe_file(html_file, url)
            
            if recipe and recipe.get('title'):
                recipes.append(recipe)
                stats["parsed_successfully"] += 1
                
                # Determine parsing method
                if recipe.get('ingredients') and recipe.get('instructions'):
                    if 'json-ld' in str(recipe):  # This would need to be tracked
                        stats["json_ld_success"] += 1
                    else:
                        stats["html_fallback_success"] += 1
            else:
                stats["parse_failed"] += 1
                logger.warning(f"Failed to parse {html_file.name}")
            
            # Progress update
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{len(html_files)} files parsed")
                
        except Exception as e:
            logger.error(f"Error processing {html_file}: {e}")
            stats["parse_failed"] += 1
    
    # Save results
    output_file = output_dir / "recipes.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for recipe in recipes:
            f.write(json.dumps(recipe, ensure_ascii=False) + '\n')
    
    # Calculate final stats
    stats["end_time"] = time.time()
    stats["total_time"] = stats["end_time"] - stats["start_time"]
    stats["parse_rate"] = stats["parsed_successfully"] / stats["total_time"] if stats["total_time"] > 0 else 0
    stats["success_rate"] = stats["parsed_successfully"] / stats["total_files"] if stats["total_files"] > 0 else 0
    
    # Save statistics
    stats_file = output_dir / "parse_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Phase C completed successfully!")
    logger.info(f"Parsed {stats['parsed_successfully']} recipes out of {stats['total_files']} files")
    logger.info(f"Success rate: {stats['success_rate']:.2%}")
    logger.info(f"Parse rate: {stats['parse_rate']:.2f} recipes/second")
    logger.info(f"Results saved to: {output_file}")
    
    return stats

def main():
    """Main entry point for the parser."""
    parser = argparse.ArgumentParser(description="Food Recipes Parser - Phase C")
    parser.add_argument("--raw", default="data/raw",
                       help="Directory containing raw HTML files")
    parser.add_argument("--out", default="data/normalized",
                       help="Output directory for normalized data")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    global logger
    logger = logging.getLogger(__name__)
    
    try:
        stats = run_parse_phase(args)
        logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
        
        if "error" in stats:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Parsing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

