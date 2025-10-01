"""
Sitemap parsing utilities for Food Recipes crawler.
"""
import gzip
import requests
import logging
from typing import Iterator, List
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
import brotli

logger = logging.getLogger(__name__)

# XML namespaces for sitemap parsing
SITEMAP_NS = {
    'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    'sitemapindex': 'http://www.sitemaps.org/schemas/sitemap/0.9'
}


def iter_sitemaps(sitemap_urls: List[str], user_agent: str = "FoodRecipesBot/0.1", 
                  timeout: int = 15) -> Iterator[str]:
    """
    Iterate through sitemap URLs and yield child sitemap URLs from sitemap index files.
    
    Args:
        sitemap_urls: List of sitemap URLs to process
        user_agent: User agent string for requests
        timeout: Request timeout in seconds
        
    Yields:
        Child sitemap URLs found in sitemap index files
    """
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate, br"
    }
    
    for sitemap_url in sitemap_urls:
        try:
            logger.info(f"Processing sitemap: {sitemap_url}")
            
            # Fetch sitemap content
            response = requests.get(sitemap_url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Handle compressed content - check actual content first
            if response.content.startswith(b'<?xml'):
                # Content is already decompressed, use as-is
                content = response.content.decode('utf-8')
            elif sitemap_url.endswith('.gz') or response.headers.get('content-encoding', '').lower() == 'gzip':
                # Decompress gzipped content
                content = gzip.decompress(response.content).decode('utf-8')
            elif response.headers.get('content-encoding', '').lower() == 'br':
                # Decompress brotli content
                content = brotli.decompress(response.content).decode('utf-8')
            else:
                # Use response.text which handles encoding automatically
                content = response.text
            
            # Parse XML
            root = ET.fromstring(content)
            
            # Check if this is a sitemap index
            if root.tag.endswith('sitemapindex'):
                logger.info(f"Found sitemap index: {sitemap_url}")
                for sitemap_elem in root.findall('.//sitemap:sitemap', SITEMAP_NS):
                    loc_elem = sitemap_elem.find('sitemap:loc', SITEMAP_NS)
                    if loc_elem is not None and loc_elem.text:
                        child_url = loc_elem.text.strip()
                        logger.debug(f"Found child sitemap: {child_url}")
                        yield child_url
            else:
                # This is a regular sitemap, yield it for URL extraction
                logger.info(f"Found regular sitemap: {sitemap_url}")
                yield sitemap_url
                
        except Exception as e:
            logger.error(f"Error processing sitemap {sitemap_url}: {e}")
            continue


def iter_urls_from_sitemap(sitemap_url: str, user_agent: str = "FoodRecipesBot/0.1", 
                          timeout: int = 15) -> Iterator[str]:
    """
    Extract URLs from a sitemap file.
    
    Args:
        sitemap_url: URL of the sitemap to process
        user_agent: User agent string for requests
        timeout: Request timeout in seconds
        
    Yields:
        URLs found in the sitemap
    """
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate, br"
    }
    
    try:
        logger.info(f"Extracting URLs from sitemap: {sitemap_url}")
        
        # Fetch sitemap content
        response = requests.get(sitemap_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Handle compressed content - check actual content first
        if response.content.startswith(b'<?xml'):
            # Content is already decompressed, use as-is
            content = response.content.decode('utf-8')
        elif sitemap_url.endswith('.gz') or response.headers.get('content-encoding', '').lower() == 'gzip':
            # Decompress gzipped content
            content = gzip.decompress(response.content).decode('utf-8')
        elif response.headers.get('content-encoding', '').lower() == 'br':
            # Decompress brotli content
            content = brotli.decompress(response.content).decode('utf-8')
        else:
            # Use response.text which handles encoding automatically
            content = response.text
        
        # Parse XML
        root = ET.fromstring(content)
        
        # Extract URLs
        url_count = 0
        for url_elem in root.findall('.//sitemap:url', SITEMAP_NS):
            loc_elem = url_elem.find('sitemap:loc', SITEMAP_NS)
            if loc_elem is not None and loc_elem.text:
                url = loc_elem.text.strip()
                url_count += 1
                yield url
        
        logger.info(f"Extracted {url_count} URLs from {sitemap_url}")
        
    except Exception as e:
        logger.error(f"Error extracting URLs from sitemap {sitemap_url}: {e}")


def filter_recipe_urls(urls: Iterator[str], base_domain: str = "www.food.com") -> Iterator[str]:
    """
    Filter URLs to only include recipe URLs from the specified domain.
    
    Args:
        urls: Iterator of URLs to filter
        base_domain: Base domain to filter for
        
    Yields:
        Recipe URLs matching the pattern /recipe/<slug>-<id>
    """
    import re
    
    recipe_pattern = re.compile(rf"https://{re.escape(base_domain)}/recipe/[^/]*-(\d+)(?:/.*)?$")
    
    for url in urls:
        if recipe_pattern.match(url):
            yield url
