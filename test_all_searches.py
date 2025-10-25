#!/usr/bin/env python3
"""
Test All Search Types - Comprehensive Search Testing
Author: Maroš Bednár (AIS 116822)

This script tests all search functionalities and generates a detailed log file.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import search modules
try:
    from search_cli.run import detect_index_type, LupyneRecipeSearcher, RobustRecipeSearcher
    SEARCH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Search modules not fully available: {e}")
    SEARCH_AVAILABLE = False


class SearchTester:
    """Comprehensive search testing with logging."""
    
    def __init__(self, log_file: str = "data/logs/search_test.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.results = []
        self.start_time = datetime.now()
        
    def log(self, message: str, level: str = "INFO"):
        """Write to log file and print."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def log_separator(self, title: str = ""):
        """Log a visual separator."""
        separator = "=" * 80
        if title:
            self.log(separator)
            self.log(f"  {title}")
            self.log(separator)
        else:
            self.log(separator)
    
    def test_query(self, searcher, query: str, k: int, filters: Dict = None, 
                   test_name: str = "", metric: str = "bm25"):
        """Test a single query and log results."""
        self.log_separator(f"TEST: {test_name}")
        self.log(f"Query: '{query}'")
        self.log(f"Metric: {metric.upper()}")
        self.log(f"Top-k: {k}")
        if filters:
            self.log(f"Filters: {json.dumps(filters, indent=2)}")
        
        try:
            start = time.time()
            
            # Execute search based on searcher type
            if hasattr(searcher, 'search_bm25'):
                # Lupyne searcher
                if metric == 'bm25':
                    results = searcher.search_bm25(query, k=k, filters=filters)
                else:
                    results = searcher.search_tfidf(query, k=k, filters=filters)
            else:
                # TSV searcher
                results = searcher.search(query, metric=metric, k=k, filters=filters)
            
            elapsed = time.time() - start
            
            self.log(f"Search completed in {elapsed:.3f}s")
            self.log(f"Results found: {len(results)}")
            self.log("")
            
            # Log top results
            if results:
                self.log("TOP RESULTS:")
                for i, result in enumerate(results[:5], 1):  # Top 5
                    if isinstance(result, dict):
                        # Lupyne format
                        title = result.get('title', result.get('title_text', 'N/A'))
                        score = result.get('score', 0.0)
                        doc_id = result.get('docId', 'N/A')
                        total_min = result.get('total_minutes')
                        cuisine = result.get('cuisine', '')
                        
                        self.log(f"\n  #{i} [{score:.4f}] {title}")
                        self.log(f"      Doc ID: {doc_id}")
                        if total_min:
                            self.log(f"      Time: {total_min} min")
                        if cuisine:
                            self.log(f"      Cuisine: {cuisine}")
                        
                        # Wikipedia links
                        wiki_links = result.get('wiki_links', [])
                        if wiki_links:
                            self.log(f"      Wiki Entities: {len(wiki_links)}")
                            entity_types = {}
                            for link in wiki_links:
                                etype = link.get('type', 'unknown')
                                entity_types[etype] = entity_types.get(etype, 0) + 1
                            self.log(f"      Entity Breakdown: {dict(entity_types)}")
                    else:
                        # TSV format (tuple)
                        doc_id, score, snippet = result
                        self.log(f"\n  #{i} [{score:.4f}]")
                        self.log(f"      Doc ID: {doc_id}")
                        self.log(f"      Snippet: {snippet[:100]}...")
            else:
                self.log("  No results found!")
            
            # Store result summary
            self.results.append({
                'test_name': test_name,
                'query': query,
                'metric': metric,
                'filters': filters,
                'result_count': len(results),
                'elapsed_time': elapsed,
                'success': True
            })
            
            self.log("")
            return True
            
        except Exception as e:
            self.log(f"ERROR: {str(e)}", level="ERROR")
            self.log(f"Traceback: {type(e).__name__}", level="ERROR")
            self.results.append({
                'test_name': test_name,
                'query': query,
                'metric': metric,
                'filters': filters,
                'result_count': 0,
                'elapsed_time': 0,
                'success': False,
                'error': str(e)
            })
            self.log("")
            return False
    
    def run_all_tests(self):
        """Run comprehensive test suite."""
        self.log_separator("SEARCH TEST SUITE - START")
        self.log(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("")
        
        # Detect available indexes
        lucene_index = Path("index/lucene/v2")
        tsv_index = Path("data/index/v1")
        
        searcher = None
        index_type = None
        
        # Try Lupyne index first
        if lucene_index.exists():
            self.log(f"Found Lupyne index: {lucene_index}")
            try:
                import lucene
                if not lucene.getVMEnv():
                    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
                searcher = LupyneRecipeSearcher(str(lucene_index))
                index_type = "lupyne"
                self.log("✓ Lupyne searcher initialized")
            except Exception as e:
                self.log(f"✗ Lupyne initialization failed: {e}", level="WARNING")
        
        # Fallback to TSV index
        if searcher is None and tsv_index.exists():
            self.log(f"Found TSV index: {tsv_index}")
            try:
                searcher = RobustRecipeSearcher(str(tsv_index))
                index_type = "tsv"
                self.log("✓ TSV searcher initialized")
            except Exception as e:
                self.log(f"✗ TSV initialization failed: {e}", level="ERROR")
                return
        
        if searcher is None:
            self.log("✗ No index found! Build an index first:", level="ERROR")
            self.log("  ./packaging/run.sh index_lucene  (Lupyne)")
            self.log("  ./packaging/run.sh index         (TSV)")
            return
        
        self.log(f"Index Type: {index_type.upper()}")
        self.log("")
        
        # =====================================================================
        # TEST SUITE
        # =====================================================================
        
        # 1. Basic searches
        self.test_query(
            searcher, 
            query="chicken pasta", 
            k=10,
            test_name="Basic Search - Chicken Pasta",
            metric="bm25"
        )
        
        self.test_query(
            searcher, 
            query="chocolate cake dessert", 
            k=10,
            test_name="Basic Search - Chocolate Cake",
            metric="bm25"
        )
        
        self.test_query(
            searcher, 
            query="mexican tacos", 
            k=10,
            test_name="Basic Search - Mexican Tacos",
            metric="bm25"
        )
        
        # 2. BM25 vs TF-IDF comparison (if Lupyne)
        if index_type == "lupyne":
            self.test_query(
                searcher, 
                query="italian pasta", 
                k=5,
                test_name="BM25 - Italian Pasta",
                metric="bm25"
            )
            
            self.test_query(
                searcher, 
                query="italian pasta", 
                k=5,
                test_name="TF-IDF - Italian Pasta",
                metric="tfidf"
            )
        
        # 3. Time-constrained searches (if Lupyne)
        if index_type == "lupyne":
            self.test_query(
                searcher,
                query="quick dinner",
                k=10,
                filters={"max_total_minutes": 30},
                test_name="Time Filter - Quick Dinner (<30 min)",
                metric="bm25"
            )
            
            self.test_query(
                searcher,
                query="easy breakfast",
                k=10,
                filters={"max_total_minutes": 15},
                test_name="Time Filter - Easy Breakfast (<15 min)",
                metric="bm25"
            )
        
        # 4. Ingredient filters (if Lupyne)
        if index_type == "lupyne":
            self.test_query(
                searcher,
                query="pasta sauce",
                k=10,
                filters={"include_ingredients": ["garlic", "tomato"]},
                test_name="Ingredient Filter - Garlic + Tomato",
                metric="bm25"
            )
            
            self.test_query(
                searcher,
                query="chicken recipe",
                k=10,
                filters={"include_ingredients": ["chicken", "lemon"]},
                test_name="Ingredient Filter - Chicken + Lemon",
                metric="bm25"
            )
        
        # 5. Cuisine filters (if Lupyne)
        if index_type == "lupyne":
            self.test_query(
                searcher,
                query="rice dish",
                k=10,
                filters={"cuisine": ["Mexican", "Italian"]},
                test_name="Cuisine Filter - Mexican OR Italian",
                metric="bm25"
            )
            
            self.test_query(
                searcher,
                query="soup",
                k=10,
                filters={"cuisine": ["Asian", "Chinese"]},
                test_name="Cuisine Filter - Asian OR Chinese",
                metric="bm25"
            )
        
        # 6. Combined filters (if Lupyne)
        if index_type == "lupyne":
            self.test_query(
                searcher,
                query="chicken tacos",
                k=5,
                filters={
                    "max_total_minutes": 45,
                    "include_ingredients": ["chicken"],
                    "cuisine": ["Mexican"]
                },
                test_name="Combined Filter - Quick Mexican Chicken",
                metric="bm25"
            )
        
        # 7. Edge cases
        self.test_query(
            searcher,
            query="",
            k=5,
            test_name="Edge Case - Empty Query",
            metric="bm25"
        )
        
        self.test_query(
            searcher,
            query="zzzzxxxxxqqqqq",
            k=5,
            test_name="Edge Case - Nonexistent Terms",
            metric="bm25"
        )
        
        self.test_query(
            searcher,
            query="the and or in",
            k=5,
            test_name="Edge Case - Stopwords Only",
            metric="bm25"
        )
        
        # Cleanup
        if hasattr(searcher, 'close'):
            searcher.close()
        
        # =====================================================================
        # SUMMARY
        # =====================================================================
        
        self.log_separator("TEST SUMMARY")
        
        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r['success'])
        failed = total_tests - successful
        
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Successful: {successful}")
        self.log(f"Failed: {failed}")
        self.log(f"Success Rate: {(successful/total_tests*100):.1f}%")
        self.log("")
        
        # Results breakdown
        self.log("RESULTS BREAKDOWN:")
        for result in self.results:
            status = "✓" if result['success'] else "✗"
            self.log(f"  {status} {result['test_name']}: {result['result_count']} results in {result['elapsed_time']:.3f}s")
            if not result['success']:
                self.log(f"      Error: {result.get('error', 'Unknown')}")
        
        self.log("")
        
        # Performance stats
        total_time = sum(r['elapsed_time'] for r in self.results if r['success'])
        avg_time = total_time / successful if successful > 0 else 0
        
        self.log("PERFORMANCE STATS:")
        self.log(f"  Total Search Time: {total_time:.3f}s")
        self.log(f"  Average Search Time: {avg_time:.3f}s")
        self.log(f"  Fastest Search: {min((r['elapsed_time'] for r in self.results if r['success']), default=0):.3f}s")
        self.log(f"  Slowest Search: {max((r['elapsed_time'] for r in self.results if r['success']), default=0):.3f}s")
        
        self.log("")
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        self.log(f"Test Suite Duration: {duration:.2f}s")
        self.log(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.log_separator("SEARCH TEST SUITE - END")
        self.log("")
        self.log(f"Full log saved to: {self.log_file.absolute()}")
        
        # Create summary JSON
        summary_file = self.log_file.parent / "search_test_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'index_type': index_type,
                'total_tests': total_tests,
                'successful': successful,
                'failed': failed,
                'results': self.results
            }, f, indent=2)
        
        self.log(f"Summary JSON saved to: {summary_file.absolute()}")


def main():
    """Main entry point."""
    print("=" * 80)
    print("  COMPREHENSIVE SEARCH TEST SUITE")
    print("  Food Recipes IR Pipeline")
    print("=" * 80)
    print()
    
    # Initialize tester
    tester = SearchTester()
    
    # Run all tests
    tester.run_all_tests()
    
    print()
    print("=" * 80)
    print("  TEST COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
