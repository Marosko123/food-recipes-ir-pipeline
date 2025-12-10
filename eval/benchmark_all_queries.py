#!/usr/bin/env python3
"""
Comprehensive Benchmark: 4 Index/Metric Combinations x 10 Queries
Generates detailed comparison report.
"""

import subprocess
import json
import sys
import os
from pathlib import Path

# Define queries
QUERIES = [
    # Presné kľúčové slová (4)
    {"id": 1, "query": "chicken breast", "category": "keyword", "description": "Presné kľúčové slová"},
    {"id": 2, "query": "chocolate chip cookies", "category": "keyword", "description": "Presné kľúčové slová"},
    {"id": 3, "query": "pasta carbonara", "category": "keyword", "description": "Presné kľúčové slová"},
    {"id": 4, "query": "vegetable soup", "category": "keyword", "description": "Presné kľúčové slová"},
    # Celé vety (5)
    {"id": 5, "query": "easy dinner recipe for beginners", "category": "sentence", "description": "Natural language query"},
    {"id": 6, "query": "how to make a healthy breakfast", "category": "sentence", "description": "Natural language query"},
    {"id": 7, "query": "delicious Italian recipe with garlic", "category": "sentence", "description": "Natural language query"},
    {"id": 8, "query": "quick meal under 30 minutes", "category": "sentence", "description": "Natural language query"},
    {"id": 9, "query": "best dessert for birthday party", "category": "sentence", "description": "Natural language query"},
    # Nezmyselný vstup (1)
    {"id": 10, "query": "xyzfoo blarblar qwertyuiop asdfghjkl", "category": "nonsense", "description": "Test robustnosti"},
]

# Index configurations
CONFIGS = [
    {"name": "Simple_BM25", "index": "index/v1", "metric": "bm25", "index_type": "tsv", "python": sys.executable},
    {"name": "Simple_TFIDF", "index": "index/v1", "metric": "tfidf", "index_type": "tsv", "python": sys.executable},
    {"name": "Lucene_BM25", "index": "index/v2", "metric": "bm25", "index_type": "lucene", "python": "/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14"},
    {"name": "Lucene_TFIDF", "index": "index/v2_tfidf", "metric": "tfidf", "index_type": "lucene", "python": "/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14"},
]

def run_search(index_path, metric, query, k=10, python_cmd=None):
    """Run search and return results."""
    if python_cmd is None:
        python_cmd = sys.executable
    cmd = [
        python_cmd, "-m", "search_cli.run",
        "--index", index_path,
        "--metric", metric,
        "--q", query,
        "--k", str(k),
        "--json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout
        
        # Find JSON array in output
        start = output.find('[')
        end = output.rfind(']') + 1
        
        if start >= 0 and end > start:
            json_str = output[start:end]
            return json.loads(json_str)
        return []
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return []

def calculate_overlap(results1, results2, k=5):
    """Calculate overlap between two result sets at position k."""
    ids1 = set(r['doc_id'] for r in results1[:k])
    ids2 = set(r['doc_id'] for r in results2[:k])
    
    if not ids1 and not ids2:
        return 1.0  # Both empty = 100% match
    if not ids1 or not ids2:
        return 0.0
    
    overlap = len(ids1 & ids2)
    return overlap / k

def main():
    results = {}
    
    print("Running benchmark on 10 queries x 4 configurations...")
    print("=" * 60)
    
    for q in QUERIES:
        query_id = q['id']
        query_text = q['query']
        results[query_id] = {"query": q, "configs": {}}
        
        print(f"\nQuery {query_id}: '{query_text}'")
        
        for config in CONFIGS:
            config_name = config['name']
            print(f"  - {config_name}...", end=" ", flush=True)
            
            search_results = run_search(config['index'], config['metric'], query_text, k=10, python_cmd=config['python'])
            
            results[query_id]["configs"][config_name] = {
                "results": search_results,
                "count": len(search_results)
            }
            
            print(f"{len(search_results)} results")
    
    # Save results
    output_path = Path("eval/benchmark_results/full_benchmark_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to {output_path}")
    
    # Generate summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    
    for query_id, data in results.items():
        q = data['query']
        configs = data['configs']
        
        print(f"\nQuery {query_id}: '{q['query']}' ({q['category']})")
        
        # Compare all pairs
        config_names = list(configs.keys())
        for i, name1 in enumerate(config_names):
            for name2 in config_names[i+1:]:
                r1 = configs[name1]['results']
                r2 = configs[name2]['results']
                overlap = calculate_overlap(r1, r2, k=5)
                print(f"  {name1} vs {name2}: {overlap*100:.0f}% overlap @5")

if __name__ == "__main__":
    main()
