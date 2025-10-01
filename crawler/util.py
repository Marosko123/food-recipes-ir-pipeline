"""
Utility functions for Food Recipes crawler.
"""
import hashlib
import re
import time
import random
import logging
from typing import Optional, Iterator, Callable, Any
from contextlib import contextmanager
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def canonicalize(url: str, html: Optional[str] = None) -> str:
    """
    Canonicalize a URL, preferring <link rel="canonical"> if HTML is provided.
    
    Args:
        url: Original URL
        html: Optional HTML content to extract canonical URL from
        
    Returns:
        Canonical URL
    """
    if html:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            canonical_link = soup.find('link', rel='canonical')
            if canonical_link and canonical_link.get('href'):
                canonical_url = canonical_link['href']
                # Make absolute if relative
                if canonical_url.startswith('/'):
                    parsed = urlparse(url)
                    canonical_url = f"{parsed.scheme}://{parsed.netloc}{canonical_url}"
                elif not canonical_url.startswith('http'):
                    canonical_url = urljoin(url, canonical_url)
                return canonical_url
        except Exception as e:
            logger.debug(f"Error extracting canonical URL from HTML: {e}")
    
    return url


def sha1_url(url: str) -> str:
    """
    Generate SHA1 hash of a URL for deduplication.
    
    Args:
        url: URL to hash
        
    Returns:
        SHA1 hash as hexadecimal string
    """
    return hashlib.sha1(url.encode('utf-8')).hexdigest()


def extract_doc_id(url: str) -> Optional[str]:
    """
    Extract numeric document ID from recipe URL using regex pattern.
    
    Args:
        url: Recipe URL to extract ID from
        
    Returns:
        Numeric ID as string, or None if not found
    """
    pattern = r"/recipe/[^/]*-(\d+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


@contextmanager
def throttle(qps: float):
    """
    Context manager for rate limiting requests.
    
    Args:
        qps: Queries per second (requests per second)
    """
    if qps <= 0:
        yield
        return
    
    # Calculate delay between requests
    base_delay = 1.0 / qps
    
    # Add jitter (±20%)
    jitter = random.uniform(-0.2, 0.2) * base_delay
    delay = max(0, base_delay + jitter)
    
    start_time = time.time()
    yield
    elapsed = time.time() - start_time
    
    # Sleep for remaining time if needed
    if elapsed < delay:
        time.sleep(delay - elapsed)


def retry(max_retries: int = 3, base_delay: float = 1.0, 
          backoff_factor: float = 2.0, 
          retry_on: Callable[[Exception], bool] = None):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        backoff_factor: Multiplier for delay on each retry
        retry_on: Function to determine if exception should trigger retry
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry this exception
                    if retry_on and not retry_on(e):
                        raise e
                    
                    # Don't retry on last attempt
                    if attempt == max_retries:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = base_delay * (backoff_factor ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def is_transient_error(exception: Exception) -> bool:
    """
    Check if an exception represents a transient error that should trigger retry.
    
    Args:
        exception: Exception to check
        
    Returns:
        True if exception should trigger retry
    """
    if isinstance(exception, requests.RequestException):
        if hasattr(exception, 'response') and exception.response is not None:
            status_code = exception.response.status_code
            # Retry on 5xx server errors and 429 rate limiting
            return status_code >= 500 or status_code == 429
        # Retry on connection errors, timeouts, etc.
        return True
    
    return False


def fetch_with_retry(url: str, user_agent: str = "FoodRecipesBot/0.1", 
                    timeout: int = 15, max_retries: int = 3) -> requests.Response:
    """
    Fetch URL with retry logic for transient errors.
    
    Args:
        url: URL to fetch
        user_agent: User agent string
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        
    Returns:
        Response object
        
    Raises:
        requests.RequestException: If all retries fail
    """
    @retry(max_retries=max_retries, retry_on=is_transient_error)
    def _fetch():
        headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate, br"
        }
        return requests.get(url, headers=headers, timeout=timeout)
    
    return _fetch()


def deduplicate_urls(urls: Iterator[str], seen: Optional[set] = None) -> Iterator[str]:
    """
    Deduplicate URLs using a set to track seen URLs.
    
    Args:
        urls: Iterator of URLs
        seen: Optional set of already seen URL hashes
        
    Yields:
        Unique URLs
    """
    if seen is None:
        seen = set()
    
    for url in urls:
        url_hash = sha1_url(url)
        if url_hash not in seen:
            seen.add(url_hash)
            yield url
        else:
            logger.debug(f"Skipping duplicate URL: {url}")


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

