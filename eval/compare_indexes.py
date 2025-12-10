#!/usr/bin/env python3
"""
Index Comparison Tool

Compares:
1. Simple Python index (index/v1) - Pure Python, no external deps
2. PyLucene index (index/v2) - Using Lupyne wrapper

Generates metrics for speed, precision, and result overlap.

Usage:
    python -m eval.compare_indexes \
        --simple-index index/v1 \
        --lucene-index index/v2 \
        --queries eval/queries.tsv \
        --output eval/index_comparison.json
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleIndexSearcherWrapper:
    """Wrapper for SimpleSearcher from indexer.simple_indexer."""
    
    def __init__(self, index_dir: str):
        from indexer.simple_indexer import SimpleSearcher
        self.searcher = SimpleSearcher(index_dir)
        self.index_dir = index_dir
        logger.info(f"Loaded Simple index: {index_dir}")
    
    def search_tfidf(self, query: str, k: int = 10) -> Tuple[List[Dict[str, Any]], float]:
        """Search using TF-IDF, return results and elapsed time."""
        start_time = time.time()
        results = self.searcher.search_tfidf(query, k=k)
        elapsed = time.time() - start_time
        
        # Normalize format
        for r in results:
            r['title_text'] = r.get('title', '')
            r['elapsed_ms'] = elapsed * 1000
        
        return results, elapsed * 1000
    
    def search_bm25(self, query: str, k: int = 10) -> Tuple[List[Dict[str, Any]], float]:
        """Search using BM25, return results and elapsed time."""
        start_time = time.time()
        results = self.searcher.search_bm25(query, k=k)
        elapsed = time.time() - start_time
        
        # Normalize format
        for r in results:
            r['title_text'] = r.get('title', '')
            r['elapsed_ms'] = elapsed * 1000
        
        return results, elapsed * 1000


class LuceneIndexSearcherWrapper:
    """Wrapper for PyLucene-based searcher."""
    
    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        self.searcher = None
        self.available = False
        self._init_searcher()
    
    def _init_searcher(self):
        """Initialize Lupyne searcher."""
        try:
            from search_cli.lupyne_searcher import LupyneRecipeSearcher
            self.searcher = LupyneRecipeSearcher(str(self.index_dir))
            self.available = True
            logger.info(f"Loaded Lucene index: {self.index_dir}")
        except ImportError as e:
            logger.warning(f"PyLucene not available: {e}")
            self.available = False
        except Exception as e:
            logger.warning(f"Cannot load Lucene index: {e}")
            self.available = False
    
    def search_bm25(self, query: str, k: int = 10) -> Tuple[List[Dict[str, Any]], float]:
        """Search using BM25, return results and elapsed time."""
        if not self.available:
            return [], 0
        
        start_time = time.time()
        results = self.searcher.search_bm25(query, k=k)
        elapsed = time.time() - start_time
        
        for r in results:
            r['elapsed_ms'] = elapsed * 1000
        
        return results, elapsed * 1000
    
    def search_tfidf(self, query: str, k: int = 10) -> Tuple[List[Dict[str, Any]], float]:
        """Search using TF-IDF, return results and elapsed time."""
        if not self.available:
            return [], 0
        
        start_time = time.time()
        results = self.searcher.search_tfidf(query, k=k)
        elapsed = time.time() - start_time
        
        for r in results:
            r['elapsed_ms'] = elapsed * 1000
        
        return results, elapsed * 1000
    
    def search_fuzzy(self, query: str, k: int = 10) -> Tuple[List[Dict[str, Any]], float]:
        """Fuzzy search, return results and elapsed time."""
        if not self.available:
            return [], 0
        
        start_time = time.time()
        results = self.searcher.search_fuzzy(query, k=k)
        elapsed = time.time() - start_time
        
        for r in results:
            r['elapsed_ms'] = elapsed * 1000
        
        return results, elapsed * 1000
    
    def close(self):
        if self.searcher:
            self.searcher.close()


def load_queries(queries_file: str) -> List[Dict[str, str]]:
    """Load queries from TSV file."""
    queries = []
    with open(queries_file, 'r', encoding='utf-8') as f:
        next(f)  # Skip header
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                queries.append({
                    'qid': parts[0],
                    'query': parts[1],
                    'notes': parts[2] if len(parts) > 2 else ''
                })
    return queries


def calculate_overlap(results1: List[Dict], results2: List[Dict], k: int = 10) -> Dict[str, Any]:
    """Calculate overlap metrics between two result sets."""
    ids1 = set(str(r['docId']) for r in results1[:k])
    ids2 = set(str(r['docId']) for r in results2[:k])
    
    intersection = ids1 & ids2
    union = ids1 | ids2
    
    return {
        'overlap_count': len(intersection),
        'overlap_ratio': len(intersection) / k if k > 0 else 0,
        'jaccard': len(intersection) / len(union) if union else 0,
        'ids_only_in_first': list(ids1 - ids2),
        'ids_only_in_second': list(ids2 - ids1),
        'common_ids': list(intersection)
    }


def compare_rankings(results1: List[Dict], results2: List[Dict], k: int = 10) -> float:
    """Calculate Kendall's Tau rank correlation."""
    # Get common documents
    ids1 = {str(r['docId']): i for i, r in enumerate(results1[:k])}
    ids2 = {str(r['docId']): i for i, r in enumerate(results2[:k])}
    
    common = set(ids1.keys()) & set(ids2.keys())
    if len(common) < 2:
        return 0.0
    
    # Calculate concordant/discordant pairs
    common_list = list(common)
    concordant = 0
    discordant = 0
    
    for i in range(len(common_list)):
        for j in range(i + 1, len(common_list)):
            doc_i, doc_j = common_list[i], common_list[j]
            
            rank1_i, rank1_j = ids1[doc_i], ids1[doc_j]
            rank2_i, rank2_j = ids2[doc_i], ids2[doc_j]
            
            if (rank1_i < rank1_j and rank2_i < rank2_j) or (rank1_i > rank1_j and rank2_i > rank2_j):
                concordant += 1
            else:
                discordant += 1
    
    total = concordant + discordant
    if total == 0:
        return 0.0
    
    return (concordant - discordant) / total


def main():
    parser = argparse.ArgumentParser(description='Compare Simple vs Lucene index performance')
    parser.add_argument('--simple-index', type=str, default='index/v1',
                        help='Path to simple TSV-based index')
    parser.add_argument('--lucene-index', type=str, default='index/v2',
                        help='Path to Lucene index')
    parser.add_argument('--queries', type=str, default='eval/queries.tsv',
                        help='Path to queries TSV file')
    parser.add_argument('--output', type=str, default='eval/index_comparison.json',
                        help='Output JSON file for comparison results')
    parser.add_argument('--k', type=int, default=10,
                        help='Number of results to compare')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Index Comparison: Simple Python vs PyLucene")
    logger.info("=" * 60)
    
    # Load Simple index
    logger.info(f"Loading Simple index from: {args.simple_index}")
    try:
        simple_searcher = SimpleIndexSearcherWrapper(args.simple_index)
    except Exception as e:
        logger.error(f"Failed to load Simple index: {e}")
        sys.exit(1)
    
    # Load Lucene index (optional)
    logger.info(f"Loading Lucene index from: {args.lucene_index}")
    lucene_searcher = LuceneIndexSearcherWrapper(args.lucene_index)
    
    # Load queries
    logger.info(f"Loading queries from: {args.queries}")
    queries = load_queries(args.queries)
    logger.info(f"Loaded {len(queries)} queries")
    
    # Run comparison
    comparison_results = {
        'metadata': {
            'simple_index': args.simple_index,
            'lucene_index': args.lucene_index,
            'lucene_available': lucene_searcher.available,
            'queries_file': args.queries,
            'k': args.k,
            'num_queries': len(queries)
        },
        'queries': [],
        'summary': {}
    }
    
    # Timing accumulators
    simple_bm25_times = []
    simple_tfidf_times = []
    lucene_bm25_times = []
    lucene_tfidf_times = []
    overlap_ratios = []
    
    for q in queries:
        qid = q['qid']
        query = q['query']
        logger.info(f"\nQuery {qid}: '{query}'")
        
        query_result = {
            'qid': qid,
            'query': query,
            'notes': q.get('notes', '')
        }
        
        # ==================== SIMPLE INDEX ====================
        
        # Simple BM25
        simple_bm25_results, simple_bm25_time = simple_searcher.search_bm25(query, k=args.k)
        simple_bm25_times.append(simple_bm25_time)
        
        query_result['simple_bm25'] = {
            'time_ms': round(simple_bm25_time, 2),
            'num_results': len(simple_bm25_results),
            'top3': [{'docId': r['docId'], 'title': r['title'], 'score': round(r['score'], 4)} 
                     for r in simple_bm25_results[:3]]
        }
        logger.info(f"  Simple BM25:   {simple_bm25_time:.2f}ms, {len(simple_bm25_results)} results")
        
        # Simple TF-IDF
        simple_tfidf_results, simple_tfidf_time = simple_searcher.search_tfidf(query, k=args.k)
        simple_tfidf_times.append(simple_tfidf_time)
        
        query_result['simple_tfidf'] = {
            'time_ms': round(simple_tfidf_time, 2),
            'num_results': len(simple_tfidf_results),
            'top3': [{'docId': r['docId'], 'title': r['title'], 'score': round(r['score'], 4)} 
                     for r in simple_tfidf_results[:3]]
        }
        logger.info(f"  Simple TF-IDF: {simple_tfidf_time:.2f}ms, {len(simple_tfidf_results)} results")
        
        # Compare Simple BM25 vs TF-IDF
        simple_overlap = calculate_overlap(simple_bm25_results, simple_tfidf_results, k=args.k)
        query_result['simple_bm25_vs_tfidf'] = {
            'overlap_ratio': round(simple_overlap['overlap_ratio'], 2),
            'kendall_tau': round(compare_rankings(simple_bm25_results, simple_tfidf_results, args.k), 3)
        }
        
        # ==================== LUCENE INDEX ====================
        
        if lucene_searcher.available:
            # Lucene BM25
            lucene_bm25_results, lucene_bm25_time = lucene_searcher.search_bm25(query, k=args.k)
            lucene_bm25_times.append(lucene_bm25_time)
            
            query_result['lucene_bm25'] = {
                'time_ms': round(lucene_bm25_time, 2),
                'num_results': len(lucene_bm25_results),
                'top3': [{'docId': r['docId'], 'title': r.get('title', r.get('title_text', '')), 
                         'score': round(r['score'], 4)} 
                         for r in lucene_bm25_results[:3]]
            }
            logger.info(f"  Lucene BM25:   {lucene_bm25_time:.2f}ms, {len(lucene_bm25_results)} results")
            
            # Lucene TF-IDF
            lucene_tfidf_results, lucene_tfidf_time = lucene_searcher.search_tfidf(query, k=args.k)
            lucene_tfidf_times.append(lucene_tfidf_time)
            
            query_result['lucene_tfidf'] = {
                'time_ms': round(lucene_tfidf_time, 2),
                'num_results': len(lucene_tfidf_results),
                'top3': [{'docId': r['docId'], 'title': r.get('title', r.get('title_text', '')),
                         'score': round(r['score'], 4)} 
                         for r in lucene_tfidf_results[:3]]
            }
            logger.info(f"  Lucene TF-IDF: {lucene_tfidf_time:.2f}ms, {len(lucene_tfidf_results)} results")
            
            # Compare Simple vs Lucene (BM25)
            cross_overlap = calculate_overlap(simple_bm25_results, lucene_bm25_results, k=args.k)
            overlap_ratios.append(cross_overlap['overlap_ratio'])
            
            query_result['simple_vs_lucene_bm25'] = {
                'overlap_ratio': round(cross_overlap['overlap_ratio'], 2),
                'kendall_tau': round(compare_rankings(simple_bm25_results, lucene_bm25_results, args.k), 3)
            }
            logger.info(f"  Simple vs Lucene overlap: {cross_overlap['overlap_ratio']:.0%}")
        
        comparison_results['queries'].append(query_result)
    
    # ==================== SUMMARY ====================
    
    num_queries = len(queries)
    
    summary = {
        'simple_avg_bm25_time_ms': round(sum(simple_bm25_times) / num_queries, 2),
        'simple_avg_tfidf_time_ms': round(sum(simple_tfidf_times) / num_queries, 2),
    }
    
    if lucene_searcher.available and lucene_bm25_times:
        summary['lucene_avg_bm25_time_ms'] = round(sum(lucene_bm25_times) / num_queries, 2)
        summary['lucene_avg_tfidf_time_ms'] = round(sum(lucene_tfidf_times) / num_queries, 2)
        summary['avg_overlap_simple_vs_lucene'] = round(sum(overlap_ratios) / len(overlap_ratios), 2) if overlap_ratios else 0
        
        # Speedup calculation
        if summary['simple_avg_bm25_time_ms'] > 0:
            summary['lucene_speedup'] = round(summary['simple_avg_bm25_time_ms'] / summary['lucene_avg_bm25_time_ms'], 2) if summary['lucene_avg_bm25_time_ms'] > 0 else 0
    
    comparison_results['summary'] = summary
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Simple Index - Avg BM25 time:  {summary['simple_avg_bm25_time_ms']:.2f} ms")
    logger.info(f"Simple Index - Avg TF-IDF time: {summary['simple_avg_tfidf_time_ms']:.2f} ms")
    
    if lucene_searcher.available:
        logger.info(f"Lucene Index - Avg BM25 time:  {summary.get('lucene_avg_bm25_time_ms', 0):.2f} ms")
        logger.info(f"Lucene Index - Avg TF-IDF time: {summary.get('lucene_avg_tfidf_time_ms', 0):.2f} ms")
        logger.info(f"Avg Result Overlap (Simple vs Lucene): {summary.get('avg_overlap_simple_vs_lucene', 0):.0%}")
        logger.info(f"Lucene Speedup: {summary.get('lucene_speedup', 0):.1f}x")
    else:
        logger.info("Lucene Index: Not available (PyLucene not installed)")
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comparison_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nResults saved to: {output_path}")
    
    # Cleanup
    if lucene_searcher.available:
        lucene_searcher.close()
    
    logger.info("\n✅ Comparison completed!")


if __name__ == '__main__':
    main()
