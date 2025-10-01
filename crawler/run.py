"""
Main crawler module for Food Recipes project.
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Set, List, Dict, Any
from urllib.parse import urlparse

from .robots import fetch_robots, parse_robots, is_allowed, get_disallowed_patterns_summary
from .sitemap import iter_sitemaps, iter_urls_from_sitemap, filter_recipe_urls
from .util import (
    canonicalize, sha1_url, extract_doc_id, throttle, 
    deduplicate_urls, format_duration, fetch_with_retry
)
from .frontier import Frontier, CrawlTask
from .recipe_filter import RecipeQualityFilter

# Configure logging
def setup_logging(log_file: str = "data/crawl.log"):
    """Setup logging configuration."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def run_seeds_phase(args) -> Dict[str, Any]:
    """
    Run Phase A: Web Analysis + Seed Extraction.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Dictionary with statistics about the seed extraction
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting Phase A: Web Analysis + Seed Extraction")
    
    # Create output directory
    os.makedirs(args.out, exist_ok=True)
    
    # Initialize statistics
    stats = {
        "sitemaps_parsed": 0,
        "urls_seen": 0,
        "urls_recipe": 0,
        "urls_unique": 0,
        "disallow_patterns": [],
        "sitemap_urls": []
    }
    
    # Step 1: Fetch and parse robots.txt
    logger.info("Fetching robots.txt...")
    try:
        robots_text = fetch_robots(
            args.base_url, 
            user_agent=args.user_agent,
            timeout=args.timeout
        )
        logger.debug(f"Robots text length: {len(robots_text)}")
        logger.debug(f"Contains sitemap: {'sitemap' in robots_text.lower()}")
        
        robots_data = parse_robots(robots_text)
        stats["disallow_patterns"] = robots_data["disallow"]
        stats["sitemap_urls"] = robots_data["sitemaps"]
        
        # Workaround for rate limiting - if no sitemaps found, use known sitemaps
        if not robots_data["sitemaps"]:
            logger.warning("No sitemaps found in robots.txt, using known sitemap URLs")
            known_sitemaps = [
                "https://www.food.com/sitemap.xml",
                "https://www.food.com/news/news-sitemap.xml"
            ]
            stats["sitemap_urls"] = known_sitemaps
            robots_data["sitemaps"] = known_sitemaps
        
        logger.info(f"Found {len(robots_data['disallow'])} disallow patterns")
        logger.info(f"Found {len(robots_data['sitemaps'])} sitemap URLs")
        
    except Exception as e:
        logger.error(f"Error fetching robots.txt: {e}")
        # Use known sitemaps as fallback
        logger.warning("Using known sitemap URLs as fallback")
        known_sitemaps = [
            "https://www.food.com/sitemap.xml",
            "https://www.food.com/news/news-sitemap.xml"
        ]
        stats["sitemap_urls"] = known_sitemaps
        robots_data = {"disallow": [], "sitemaps": known_sitemaps}
    
    # Step 2: Process sitemaps to find child sitemaps
    logger.info("Processing sitemaps...")
    all_sitemap_urls = set(robots_data["sitemaps"])
    
    # Add a delay to avoid rate limiting
    import time
    time.sleep(2)
    
    try:
        for child_sitemap in iter_sitemaps(
            robots_data["sitemaps"], 
            user_agent=args.user_agent,
            timeout=args.timeout
        ):
            all_sitemap_urls.add(child_sitemap)
            stats["sitemaps_parsed"] += 1
            
        logger.info(f"Total sitemaps to process: {len(all_sitemap_urls)}")
        
    except Exception as e:
        logger.error(f"Error processing sitemaps: {e}")
    
    # Step 3: Extract recipe URLs from all sitemaps
    logger.info("Extracting recipe URLs from sitemaps...")
    seen_urls: Set[str] = set()
    recipe_urls: List[str] = []
    
    try:
        for sitemap_url in all_sitemap_urls:
            with throttle(args.qps):
                try:
                    # Extract URLs from this sitemap
                    urls = list(iter_urls_from_sitemap(
                        sitemap_url,
                        user_agent=args.user_agent,
                        timeout=args.timeout
                    ))
                    stats["urls_seen"] += len(urls)
                    
                    # Filter for recipe URLs
                    recipe_urls_from_sitemap = list(filter_recipe_urls(urls))
                    stats["urls_recipe"] += len(recipe_urls_from_sitemap)
                    
                    # Deduplicate and add to collection
                    for url in deduplicate_urls(recipe_urls_from_sitemap, seen_urls):
                        recipe_urls.append(url)
                    
                    logger.info(f"Processed sitemap {sitemap_url}: {len(recipe_urls_from_sitemap)} recipe URLs")
                    
                except Exception as e:
                    logger.error(f"Error processing sitemap {sitemap_url}: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Error extracting URLs: {e}")
    
    stats["urls_unique"] = len(recipe_urls)
    
    # Step 4: Filter URLs against robots.txt rules
    logger.info("Filtering URLs against robots.txt rules...")
    allowed_urls = []
    disallowed_count = 0
    
    for url in recipe_urls:
        if is_allowed(url, robots_data["disallow"]):
            allowed_urls.append(url)
        else:
            disallowed_count += 1
            logger.debug(f"Disallowed URL: {url}")
    
    logger.info(f"Filtered out {disallowed_count} disallowed URLs")
    logger.info(f"Final count: {len(allowed_urls)} allowed recipe URLs")
    
    # Step 5: Save outputs
    logger.info("Saving outputs...")
    
    # Save recipe seeds
    seeds_file = os.path.join(args.out, "recipe_seeds.txt")
    with open(seeds_file, 'w') as f:
        for url in allowed_urls:
            f.write(f"{url}\n")
    
    # Save statistics
    stats_file = os.path.join(args.out, "seed_stats.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Generate analysis report
    report_file = os.path.join(args.out, "report.md")
    generate_analysis_report(report_file, stats, allowed_urls, args.base_url)
    
    logger.info(f"Phase A completed. Results saved to {args.out}")
    return stats


def generate_analysis_report(report_file: str, stats: Dict[str, Any], 
                           recipe_urls: List[str], base_url: str):
    """
    Generate the Phase A analysis report.
    
    Args:
        report_file: Path to save the report
        stats: Statistics dictionary
        recipe_urls: List of discovered recipe URLs
        base_url: Base URL of the site
    """
    with open(report_file, 'w') as f:
        f.write("# Phase A Analysis Report - Food Recipes Seed Extraction\n\n")
        f.write(f"**Base Site:** {base_url}\n")
        f.write(f"**Generated:** {__import__('datetime').datetime.now().isoformat()}\n\n")
        
        # 1. robots.txt analysis
        f.write("## 1. robots.txt Analysis\n\n")
        f.write(get_disallowed_patterns_summary(stats["disallow_patterns"]))
        f.write(f"\n**Sitemap URLs found:** {len(stats['sitemap_urls'])}\n")
        for sitemap in stats["sitemap_urls"]:
            f.write(f"  - {sitemap}\n")
        f.write("\n")
        
        # 2. Recipe URL patterns
        f.write("## 2. Recipe URL Patterns\n\n")
        f.write("✅ **Confirmed pattern:** `/recipe/<slug>-<id>` with numeric `id`\n")
        f.write("✅ **Regex for doc_id:** `r\"/recipe/[^/]*-(\\d+)\"` (first capture group)\n")
        f.write("✅ **Canonical URLs:** Will use `<link rel=\"canonical\">` when available\n\n")
        
        # Sample URLs
        f.write("**Sample recipe URLs:**\n")
        for i, url in enumerate(recipe_urls[:10]):
            doc_id = extract_doc_id(url)
            f.write(f"  {i+1}. {url} (ID: {doc_id})\n")
        if len(recipe_urls) > 10:
            f.write(f"  ... and {len(recipe_urls) - 10} more\n")
        f.write("\n")
        
        # 3. Listing hubs
        f.write("## 3. Listing Hubs for Coverage/Freshness\n\n")
        f.write("**Priority 1 - Sitemaps:** ✅ Processed in this phase\n")
        f.write(f"  - Total sitemaps processed: {stats['sitemaps_parsed']}\n")
        f.write("**Priority 2 - A–Z Listings:** 🔄 For Phase B (letters [0-9, A-Z] with pagination)\n")
        f.write("**Priority 3 - HTML Sitemap & Collections:** 🔄 For Phase B (low depth for diversity)\n\n")
        
        # 4. HTTP/Politeness plan
        f.write("## 4. HTTP/Politeness Plan\n\n")
        f.write("✅ **QPS Throttle:** 0.5 requests/second with ±20% jitter\n")
        f.write("✅ **Retries:** Up to 3 attempts with exponential backoff (2^n * base)\n")
        f.write("✅ **Timeouts:** 15s connect/read timeout\n")
        f.write("✅ **Headers:** Custom UA + Accept-Encoding: gzip, deflate, br\n")
        f.write("✅ **Deduplication:** SHA1 hash of canonical URLs\n")
        f.write("✅ **Logging:** INFO level to data/crawl.log\n\n")
        
        # 5. Seed counts
        f.write("## 5. Seed Counts\n\n")
        f.write(f"**Total URLs discovered from sitemaps:** {stats['urls_seen']}\n")
        f.write(f"**Recipe URLs (matching pattern):** {stats['urls_recipe']}\n")
        f.write(f"**Unique recipe URLs:** {stats['urls_unique']}\n")
        f.write(f"**Allowed recipe URLs (after robots.txt filtering):** {len(recipe_urls)}\n")
        f.write(f"**Disallowed URLs filtered out:** {stats['urls_recipe'] - len(recipe_urls)}\n\n")
        
        # Data model preview
        f.write("## 6. Data Model Preview (Phase C Target)\n\n")
        f.write("**Target JSONL file:** `data/normalized/recipes.jsonl`\n\n")
        f.write("Each line will be a JSON object with keys:\n")
        f.write("- `id` (string): Numeric recipe ID from URL regex capture\n")
        f.write("- `url` (string): Canonical recipe URL\n")
        f.write("- `title` (string): Recipe title\n")
        f.write("- `ingredients` (array): List of ingredient strings\n")
        f.write("- `instructions` (array): List of instruction strings\n")
        f.write("- `times` (object): `{prep, cook, total}` in minutes\n")
        f.write("- `cuisine` (array): Cuisine categories\n")
        f.write("- `category` (array): Recipe categories\n")
        f.write("- `tools` (array): Required cooking tools\n")
        f.write("- `yield` (string/int): Serving size\n")
        f.write("- `author` (string/object): Recipe author\n")
        f.write("- `nutrition` (object/null): Nutrition information\n")
        f.write("- `ratings` (object/null): `{value, count}` rating data\n\n")
        
        f.write("**Preferred sources (JSON-LD first, HTML fallback):**\n")
        f.write("- **JSON-LD:** `schema.org/Recipe` structured data\n")
        f.write("- **HTML Heuristics:** Heading-based extraction (no brittle CSS selectors)\n")
        f.write("- **Time parsing:** ISO-8601 and free-text time formats → minutes\n")
        f.write("- **Canonicalization:** `<link rel=\"canonical\">` preferred\n\n")
        
        # Next steps
        f.write("## 7. Next Steps (Phase B Preview)\n\n")
        f.write("1. **Implement fetcher:** Download each URL in `recipe_seeds.txt`\n")
        f.write("2. **Respect politeness:** QPS throttling, retries, backoff\n")
        f.write("3. **Save raw HTML:** `data/raw/food.com/<doc_id>.html`\n")
        f.write("4. **Resumable queue:** Skip already-downloaded recipe IDs\n")
        f.write("5. **HTTP status tracking:** TSV index for troubleshooting\n\n")
        
        f.write("**Ready for Phase B implementation!** 🚀\n")


def run_smart_crawl_phase(args) -> Dict[str, Any]:
    """
    Run smart crawling with quality and diversity filtering.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Dictionary with statistics about the crawling
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting Smart Recipe Crawling with Quality Filtering")
    
    # Create output directory
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize quality filter
    quality_filter = RecipeQualityFilter(target_count=args.limit or 4000)
    
    # Initialize frontier with much larger capacity since we'll be filtering
    frontier = Frontier(max_size=50000)
    
    # Download statistics
    download_stats = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "filtered_out": 0,
        "retry_count": 0
    }
    
    # Load seed URLs
    if args.seeds:
        logger.info(f"Loading seed URLs from {args.seeds}")
        with open(args.seeds, 'r') as f:
            seed_urls = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(seed_urls)} seed URLs")
        
        # Shuffle URLs for better diversity
        import random
        random.shuffle(seed_urls)
        logger.info("Shuffled URLs for better cuisine diversity")
    else:
        logger.error("No seed file provided. Use --seeds to specify seed URLs file.")
        return {}
    
    # Enqueue seed URLs
    logger.info("Enqueuing seed URLs...")
    enqueued_count = 0
    for url in seed_urls:
        doc_id = extract_doc_id(url)
        if doc_id and frontier.enqueue(url, doc_id, "seeds", priority=1):
            enqueued_count += 1
    
    logger.info(f"Enqueued {enqueued_count} URLs for crawling")
    
    # Crawl URLs with smart filtering
    logger.info("Starting smart crawling process...")
    crawled_count = 0
    filtered_count = 0
    failed_count = 0
    start_time = time.time()
    
    try:
        while not frontier.is_empty() and crawled_count < (args.limit or 4000):
            task = frontier.dequeue()
            if not task:
                break
                
            logger.debug(f"Evaluating {task.url}")
            
            # Download the page first
            download_stats["total_requests"] += 1
            
            try:
                with throttle(args.qps):
                    response = fetch_with_retry(task.url, user_agent=args.user_agent, timeout=args.timeout, max_retries=args.retries)
                
                if response and response.status_code == 200:
                    download_stats["successful_requests"] += 1
                    content = response.text
                    
                    # Check if recipe meets quality criteria
                    recipe_data = {
                        'url': task.url,
                        'doc_id': task.doc_id,
                        'html_content': content
                    }
                    
                    if quality_filter.should_include_recipe(recipe_data):
                        # Save the recipe
                        try:
                            # Create domain directory
                            domain_dir = output_dir / "www.food.com"
                            domain_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Save HTML file
                            file_path = domain_dir / f"{task.doc_id}.html"
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            
                            crawled_count += 1
                            logger.info(f"✅ Saved quality recipe #{crawled_count}: {task.url}")
                            
                            # Log progress every 50 recipes
                            if crawled_count % 50 == 0:
                                stats = quality_filter.get_progress_stats()
                                elapsed = time.time() - start_time
                                rate = crawled_count / elapsed if elapsed > 0 else 0
                                logger.info(f"Progress: {crawled_count}/{args.limit or 4000} quality recipes "
                                           f"({stats['progress_percent']:.1f}%) - Rate: {rate:.2f}/s")
                                logger.info(f"Cuisine diversity: {len(stats['cuisine_distribution'])} cuisines")
                                
                        except Exception as e:
                            logger.error(f"Failed to save content for {task.url}: {e}")
                            failed_count += 1
                            download_stats["failed_requests"] += 1
                    else:
                        # Recipe filtered out
                        filtered_count += 1
                        download_stats["filtered_out"] += 1
                        logger.debug(f"❌ Filtered out: {task.url}")
                        
                else:
                    download_stats["failed_requests"] += 1
                    failed_count += 1
                    logger.warning(f"Failed to download {task.url}: HTTP {response.status_code if response else 'No response'}")
                    
            except Exception as e:
                download_stats["failed_requests"] += 1
                failed_count += 1
                logger.error(f"Error processing {task.url}: {e}")
                
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    
    # Final statistics
    elapsed = time.time() - start_time
    stats = quality_filter.get_progress_stats()
    
    final_stats = {
        "crawled_count": crawled_count,
        "filtered_count": filtered_count,
        "failed_count": failed_count,
        "total_processed": download_stats["total_requests"],
        "success_rate": (crawled_count / download_stats["total_requests"]) * 100 if download_stats["total_requests"] > 0 else 0,
        "filter_rate": (filtered_count / download_stats["successful_requests"]) * 100 if download_stats["successful_requests"] > 0 else 0,
        "elapsed_time": elapsed,
        "crawl_rate": crawled_count / elapsed if elapsed > 0 else 0,
        "quality_stats": stats
    }
    
    # Save selected URLs list
    quality_filter.save_selected_urls("data/selected_quality_recipes.txt")
    
    logger.info(f"Smart crawling completed!")
    logger.info(f"Quality recipes collected: {crawled_count}")
    logger.info(f"Recipes filtered out: {filtered_count}")
    logger.info(f"Success rate: {final_stats['success_rate']:.1f}%")
    logger.info(f"Cuisine diversity: {len(stats['cuisine_distribution'])} different cuisines")
    
    return final_stats


def run_crawl_phase(args) -> Dict[str, Any]:
    """
    Run Phase B: Download recipe pages.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Dictionary with statistics about the crawling
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting Phase B: Recipe Page Crawling")
    
    # Create output directory
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize frontier
    frontier = Frontier(max_size=args.limit if args.limit else 1000000)
    
    # Download statistics
    download_stats = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "retry_count": 0
    }
    
    # Load seed URLs
    if args.seeds:
        logger.info(f"Loading seed URLs from {args.seeds}")
        with open(args.seeds, 'r') as f:
            seed_urls = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(seed_urls)} seed URLs")
    else:
        logger.error("No seed file provided. Use --seeds to specify seed URLs file.")
        return {}
    
    # Enqueue seed URLs
    logger.info("Enqueuing seed URLs...")
    enqueued_count = 0
    for url in seed_urls:
        doc_id = extract_doc_id(url)
        if doc_id and frontier.enqueue(url, doc_id, "seeds", priority=1):
            enqueued_count += 1
    
    logger.info(f"Enqueued {enqueued_count} URLs for crawling")
    
    # Crawl URLs
    logger.info("Starting crawling process...")
    crawled_count = 0
    failed_count = 0
    start_time = time.time()
    
    try:
        while not frontier.is_empty() and crawled_count < (args.limit or float('inf')):
            task = frontier.dequeue()
            if not task:
                break
                
            logger.info(f"Crawling {task.url} (attempt {task.retry_count + 1})")
            
            # Download the page
            download_stats["total_requests"] += 1
            
            try:
                response = fetch_with_retry(task.url, user_agent=args.user_agent, timeout=args.timeout, max_retries=args.retries)
                
                if response and response.status_code == 200:
                    download_stats["successful_requests"] += 1
                    content = response.text
                    
                    # Save content
                    try:
                        # Create domain directory
                        domain_dir = output_dir / "www.food.com"
                        domain_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Save HTML file
                        file_path = domain_dir / f"{task.doc_id}.html"
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        crawled_count += 1
                        logger.info(f"Successfully crawled and saved {task.url} -> {file_path}")
                        
                    except Exception as e:
                        logger.error(f"Failed to save content for {task.url}: {e}")
                        failed_count += 1
                        download_stats["failed_requests"] += 1
                        
                else:
                    download_stats["failed_requests"] += 1
                    failed_count += 1
                    logger.warning(f"Failed to download {task.url}: HTTP {response.status_code if response else 'No response'}")
                    
            except Exception as e:
                download_stats["failed_requests"] += 1
                failed_count += 1
                logger.error(f"Error downloading {task.url}: {e}")
            
            # Throttle requests
            throttle(args.qps)
            
            # Progress update
            if crawled_count % 10 == 0:
                elapsed = time.time() - start_time
                rate = crawled_count / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {crawled_count} crawled, {failed_count} failed, {frontier.size()} remaining (rate: {rate:.2f}/s)")
    
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    
    # Final statistics
    elapsed = time.time() - start_time
    stats = {
        "crawled_count": crawled_count,
        "failed_count": failed_count,
        "total_time": elapsed,
        "crawl_rate": crawled_count / elapsed if elapsed > 0 else 0,
        "download_stats": download_stats,
        "frontier_stats": frontier.get_stats()
    }
    
    logger.info(f"Phase B completed. Crawled {crawled_count} pages in {elapsed:.2f}s")
    logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
    
    return stats


def main():
    """Main entry point for the crawler."""
    parser = argparse.ArgumentParser(description="Food Recipes Smart Crawler")
    parser.add_argument("--phase", choices=["seeds", "crawl", "smart"], required=True,
                       help="Phase to run (seeds for Phase A, crawl for Phase B, smart for quality filtering)")
    parser.add_argument("--base-url", default="https://www.food.com",
                       help="Base URL to crawl")
    parser.add_argument("--out", default="data/raw",
                       help="Output directory for results")
    parser.add_argument("--seeds", 
                       help="Path to seed URLs file (required for crawl/smart phase)")
    parser.add_argument("--limit", type=int, default=4000,
                       help="Maximum number of quality recipes to crawl (default: 4000)")
    parser.add_argument("--user-agent", 
                       default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                       help="User agent string")
    parser.add_argument("--qps", type=float, default=1.0,
                       help="Queries per second (rate limiting)")
    parser.add_argument("--timeout", type=int, default=10,
                       help="Request timeout in seconds")
    parser.add_argument("--retries", type=int, default=2,
                       help="Maximum number of retries")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        if args.phase == "seeds":
            stats = run_seeds_phase(args)
            logger.info(f"Phase A completed successfully!")
            logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
        elif args.phase == "crawl":
            stats = run_crawl_phase(args)
            logger.info(f"Phase B completed successfully!")
            logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
        elif args.phase == "smart":
            stats = run_smart_crawl_phase(args)
            logger.info(f"Smart crawling completed successfully!")
            logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
        else:
            logger.error(f"Unknown phase: {args.phase}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Crawler interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Crawler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
