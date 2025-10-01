"""
Robots.txt parsing utilities for Food Recipes crawler.
"""
import re
import requests
import logging
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


def fetch_robots(base_url: str, user_agent: str = "FoodRecipesBot/0.1", timeout: int = 15) -> str:
    """
    Fetch robots.txt from the given base URL.
    
    Args:
        base_url: Base URL of the site (e.g., "https://www.food.com")
        user_agent: User agent string to use
        timeout: Request timeout in seconds
        
    Returns:
        Raw robots.txt content as string
        
    Raises:
        requests.RequestException: If fetch fails
    """
    robots_url = urljoin(base_url, "/robots.txt")
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate, br"
    }
    
    logger.info(f"Fetching robots.txt from {robots_url}")
    
    # Use a fresh session to avoid rate limiting
    session = requests.Session()
    response = session.get(robots_url, headers=headers, timeout=timeout)
    response.raise_for_status()
    
    # The requests library automatically handles gzip decompression
    logger.debug(f"Robots.txt content length: {len(response.text)}")
    logger.debug(f"Contains sitemap: {'sitemap' in response.text.lower()}")
    return response.text


def parse_robots(text: str) -> Dict[str, List[str]]:
    """
    Parse robots.txt content and extract disallow rules and sitemaps.
    
    Args:
        text: Raw robots.txt content
        
    Returns:
        Dictionary with 'disallow' and 'sitemaps' keys containing lists of patterns/URLs
    """
    disallow_patterns = []
    sitemaps = []
    
    current_user_agent = None
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Parse User-agent directive
        if line.lower().startswith('user-agent:'):
            current_user_agent = line.split(':', 1)[1].strip()
            continue
            
        # Parse Sitemap directive (case insensitive) - process regardless of user agent
        if line.lower().startswith('sitemap:'):
            sitemap_url = line.split(':', 1)[1].strip()
            if sitemap_url:
                sitemaps.append(sitemap_url)
            continue
            
        # Only process disallow rules for our bot or wildcard
        if current_user_agent not in ['*', 'FoodRecipesBot', 'FoodRecipesBot/0.1']:
            continue
            
        # Parse Disallow directive
        if line.lower().startswith('disallow:'):
            pattern = line.split(':', 1)[1].strip()
            if pattern:
                disallow_patterns.append(pattern)
    
    logger.info(f"Parsed {len(disallow_patterns)} disallow patterns and {len(sitemaps)} sitemaps")
    
    return {
        "disallow": disallow_patterns,
        "sitemaps": sitemaps
    }


def is_allowed(url: str, disallow_patterns: List[str]) -> bool:
    """
    Check if a URL is allowed based on robots.txt disallow patterns.
    
    Args:
        url: URL to check
        disallow_patterns: List of disallow patterns from robots.txt
        
    Returns:
        True if URL is allowed, False if disallowed
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    for pattern in disallow_patterns:
        # Convert robots.txt pattern to regex
        # Escape special regex chars except *
        regex_pattern = re.escape(pattern).replace(r'\*', '.*')
        
        # Add anchors for exact matching
        if pattern.endswith('*'):
            regex_pattern = f"^{regex_pattern}"
        else:
            regex_pattern = f"^{regex_pattern}$"
            
        if re.match(regex_pattern, path):
            logger.debug(f"URL {url} matches disallow pattern: {pattern}")
            return False
    
    return True


def get_disallowed_patterns_summary(disallow_patterns: List[str]) -> str:
    """
    Generate a summary of disallowed patterns for reporting.
    
    Args:
        disallow_patterns: List of disallow patterns
        
    Returns:
        Formatted string summary
    """
    if not disallow_patterns:
        return "No disallow patterns found."
    
    summary = "Disallow patterns found:\n"
    for pattern in disallow_patterns:
        summary += f"  - {pattern}\n"
    
    # Highlight known problematic patterns
    problematic = [p for p in disallow_patterns if any(x in p for x in ['/search/', 'finder', '.php', '.zsp'])]
    if problematic:
        summary += "\n⚠️  Known problematic patterns (will be avoided):\n"
        for pattern in problematic:
            summary += f"  - {pattern}\n"
    
    return summary
