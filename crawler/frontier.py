"""
Frontier management for the crawler.
Implements FIFO round-robin queue with source tracking.
"""

import logging
from collections import deque, defaultdict
from typing import Iterator, Set, Dict, Any
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class CrawlTask:
    """Represents a single crawl task."""
    url: str
    doc_id: str
    source: str
    priority: int = 0
    retry_count: int = 0
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

class Frontier:
    """
    FIFO round-robin frontier with source tracking.
    Ensures fair distribution across different sources.
    """
    
    def __init__(self, max_size: int = 1000000):
        self.max_size = max_size
        self.queues: Dict[str, deque] = defaultdict(deque)
        self.seen_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.source_stats: Dict[str, int] = defaultdict(int)
        
    def enqueue(self, url: str, doc_id: str, source: str, priority: int = 0) -> bool:
        """
        Add a URL to the frontier.
        
        Args:
            url: URL to crawl
            doc_id: Document ID extracted from URL
            source: Source of the URL (e.g., 'sitemap', 'discovered')
            priority: Priority level (higher = more important)
            
        Returns:
            True if URL was added, False if already seen or frontier full
        """
        if url in self.seen_urls or url in self.failed_urls:
            return False
            
        if len(self.seen_urls) >= self.max_size:
            logger.warning(f"Frontier full ({self.max_size} URLs), dropping {url}")
            return False
            
        task = CrawlTask(url=url, doc_id=doc_id, source=source, priority=priority)
        self.queues[source].append(task)
        self.seen_urls.add(url)
        self.source_stats[source] += 1
        self.total_enqueued += 1
        
        logger.debug(f"Enqueued {url} from {source} (priority {priority})")
        return True
    
    def dequeue(self) -> CrawlTask:
        """
        Get the next task from the frontier using round-robin.
        
        Returns:
            Next CrawlTask to process, or None if frontier is empty
        """
        if not self.queues:
            return None
            
        # Round-robin: try each source in turn
        sources = list(self.queues.keys())
        for source in sources:
            if self.queues[source]:
                task = self.queues[source].popleft()
                self.total_dequeued += 1
                logger.debug(f"Dequeued {task.url} from {source}")
                return task
                
        return None
    
    def mark_failed(self, url: str, max_retries: int = 3) -> bool:
        """
        Mark a URL as failed and optionally retry.
        
        Args:
            url: URL that failed
            max_retries: Maximum number of retries
            
        Returns:
            True if URL should be retried, False if permanently failed
        """
        # Find the task in queues
        for source, queue in self.queues.items():
            for task in queue:
                if task.url == url:
                    task.retry_count += 1
                    if task.retry_count <= max_retries:
                        logger.debug(f"Retrying {url} (attempt {task.retry_count}/{max_retries})")
                        return True
                    else:
                        logger.warning(f"Permanently failed {url} after {max_retries} retries")
                        self.failed_urls.add(url)
                        return False
                        
        # If not found in queues, mark as permanently failed
        self.failed_urls.add(url)
        return False
    
    def size(self) -> int:
        """Get current frontier size."""
        return sum(len(queue) for queue in self.queues.values())
    
    def is_empty(self) -> bool:
        """Check if frontier is empty."""
        return self.size() == 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get frontier statistics."""
        return {
            "total_enqueued": self.total_enqueued,
            "total_dequeued": self.total_dequeued,
            "current_size": self.size(),
            "seen_urls": len(self.seen_urls),
            "failed_urls": len(self.failed_urls),
            "source_stats": dict(self.source_stats),
            "queue_sizes": {source: len(queue) for source, queue in self.queues.items()}
        }
    
    def clear(self):
        """Clear the frontier."""
        self.queues.clear()
        self.seen_urls.clear()
        self.failed_urls.clear()
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.source_stats.clear()
        logger.info("Frontier cleared")

