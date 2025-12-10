#!/usr/bin/env python3
"""
Benchmark script for comparing Simple TSV index vs Lucene index.
Runs 30+ queries and measures performance metrics.
"""

import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test queries - diverse set covering different aspects
TEST_QUERIES = [
    # Simple ingredient queries
    {"id": 1, "query": "chicken", "category": "single_ingredient"},
    {"id": 2, "query": "pasta", "category": "single_ingredient"},
    {"id": 3, "query": "beef", "category": "single_ingredient"},
    {"id": 4, "query": "chocolate", "category": "single_ingredient"},
    {"id": 5, "query": "salmon", "category": "single_ingredient"},
    
    # Two-word queries
    {"id": 6, "query": "chicken pasta", "category": "two_words"},
    {"id": 7, "query": "chocolate cake", "category": "two_words"},
    {"id": 8, "query": "beef stew", "category": "two_words"},
    {"id": 9, "query": "grilled salmon", "category": "two_words"},
    {"id": 10, "query": "tomato soup", "category": "two_words"},
    
    # Cuisine-specific
    {"id": 11, "query": "italian pasta", "category": "cuisine"},
    {"id": 12, "query": "mexican tacos", "category": "cuisine"},
    {"id": 13, "query": "asian stir fry", "category": "cuisine"},
    {"id": 14, "query": "french dessert", "category": "cuisine"},
    {"id": 15, "query": "indian curry", "category": "cuisine"},
    
    # Cooking method
    {"id": 16, "query": "baked chicken", "category": "method"},
    {"id": 17, "query": "fried rice", "category": "method"},
    {"id": 18, "query": "grilled vegetables", "category": "method"},
    {"id": 19, "query": "roasted potatoes", "category": "method"},
    {"id": 20, "query": "steamed fish", "category": "method"},
    
    # Complex queries
    {"id": 21, "query": "easy chicken dinner", "category": "complex"},
    {"id": 22, "query": "healthy vegetable salad", "category": "complex"},
    {"id": 23, "query": "quick breakfast recipe", "category": "complex"},
    {"id": 24, "query": "homemade bread recipe", "category": "complex"},
    {"id": 25, "query": "creamy mushroom sauce", "category": "complex"},
    
    # Specific dishes
    {"id": 26, "query": "lasagna", "category": "dish"},
    {"id": 27, "query": "tiramisu", "category": "dish"},
    {"id": 28, "query": "guacamole", "category": "dish"},
    {"id": 29, "query": "risotto", "category": "dish"},
    {"id": 30, "query": "cheesecake", "category": "dish"},
    
    # Dietary
    {"id": 31, "query": "vegetarian dinner", "category": "dietary"},
    {"id": 32, "query": "low fat chicken", "category": "dietary"},
    {"id": 33, "query": "gluten free bread", "category": "dietary"},
    {"id": 34, "query": "healthy smoothie", "category": "dietary"},
    {"id": 35, "query": "sugar free dessert", "category": "dietary"},
]


def benchmark_simple_index(index_path: str, queries: List[Dict], metric: str = "bm25") -> Dict[str, Any]:
    """Benchmark Simple TSV index."""
    from search_cli.run import RobustRecipeSearcher
    
    results = {
        "index_type": "simple_tsv",
        "metric": metric,
        "queries": [],
        "total_time_ms": 0,
        "avg_time_ms": 0,
        "load_time_ms": 0,
    }
    
    # Measure index load time
    start = time.time()
    searcher = RobustRecipeSearcher(index_path)
    results["load_time_ms"] = (time.time() - start) * 1000
    
    total_time = 0
    for q in queries:
        query_result = {
            "id": q["id"],
            "query": q["query"],
            "category": q["category"],
            "results": [],
            "time_ms": 0,
            "num_results": 0,
        }
        
        start = time.time()
        if metric == "bm25":
            search_results = searcher.search_bm25(q["query"], k=10)
        else:
            search_results = searcher.search_tfidf(q["query"], k=10)
        elapsed = (time.time() - start) * 1000
        
        query_result["time_ms"] = round(elapsed, 2)
        query_result["num_results"] = len(search_results)
        
        # Store top 5 results
        for doc_id, score, snippet in search_results[:5]:
            meta = searcher.doc_metadata.get(doc_id, {})
            query_result["results"].append({
                "rank": len(query_result["results"]) + 1,
                "doc_id": doc_id,
                "title": meta.get("title", snippet),
                "score": round(score, 4),
                "url": meta.get("url", ""),
            })
        
        results["queries"].append(query_result)
        total_time += elapsed
    
    results["total_time_ms"] = round(total_time, 2)
    results["avg_time_ms"] = round(total_time / len(queries), 2)
    
    return results


def benchmark_lucene_index(index_path: str, queries: List[Dict], metric: str = "bm25") -> Dict[str, Any]:
    """Benchmark Lucene index."""
    from search_cli.lupyne_searcher import LupyneRecipeSearcher
    
    results = {
        "index_type": "lucene",
        "metric": metric,
        "queries": [],
        "total_time_ms": 0,
        "avg_time_ms": 0,
        "load_time_ms": 0,
    }
    
    # Measure index load time
    start = time.time()
    searcher = LupyneRecipeSearcher(index_path)
    results["load_time_ms"] = (time.time() - start) * 1000
    
    total_time = 0
    for q in queries:
        query_result = {
            "id": q["id"],
            "query": q["query"],
            "category": q["category"],
            "results": [],
            "time_ms": 0,
            "num_results": 0,
        }
        
        start = time.time()
        if metric == "bm25":
            search_results = searcher.search_bm25(q["query"], k=10)
        else:
            search_results = searcher.search_tfidf(q["query"], k=10)
        elapsed = (time.time() - start) * 1000
        
        query_result["time_ms"] = round(elapsed, 2)
        query_result["num_results"] = len(search_results)
        
        # Store top 5 results
        for res in search_results[:5]:
            query_result["results"].append({
                "rank": res.get("rank", 0),
                "doc_id": res.get("docId", ""),
                "title": res.get("title", res.get("title_text", "")),
                "score": round(res.get("score", 0), 4),
                "url": res.get("url", ""),
            })
        
        results["queries"].append(query_result)
        total_time += elapsed
    
    searcher.close()
    
    results["total_time_ms"] = round(total_time, 2)
    results["avg_time_ms"] = round(total_time / len(queries), 2)
    
    return results


def generate_csv_report(all_results: List[Dict], output_path: str):
    """Generate CSV for Excel analysis."""
    lines = []
    
    # Header
    lines.append("query_id,query,category,index_type,metric,time_ms,num_results,top1_title,top1_score,top1_doc_id")
    
    for result_set in all_results:
        index_type = result_set["index_type"]
        metric = result_set["metric"]
        
        for q in result_set["queries"]:
            top1 = q["results"][0] if q["results"] else {"title": "", "score": 0, "doc_id": ""}
            # Escape quotes in title
            title = top1.get("title", "").replace('"', '""')
            line = f'{q["id"]},"{q["query"]}",{q["category"]},{index_type},{metric},{q["time_ms"]},{q["num_results"]},"{title}",{top1.get("score", 0)},{top1.get("doc_id", "")}'
            lines.append(line)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"CSV report saved to: {output_path}")


def generate_comparison_csv(all_results: List[Dict], output_path: str):
    """Generate side-by-side comparison CSV."""
    # Group by query
    query_data = {}
    for result_set in all_results:
        key = f"{result_set['index_type']}_{result_set['metric']}"
        for q in result_set["queries"]:
            qid = q["id"]
            if qid not in query_data:
                query_data[qid] = {"query": q["query"], "category": q["category"]}
            query_data[qid][f"{key}_time"] = q["time_ms"]
            query_data[qid][f"{key}_results"] = q["num_results"]
            top1 = q["results"][0] if q["results"] else {"title": "", "score": 0}
            query_data[qid][f"{key}_top1"] = top1.get("title", "")[:50]
            query_data[qid][f"{key}_score"] = top1.get("score", 0)
    
    lines = []
    lines.append("query_id,query,category,simple_bm25_time,simple_bm25_results,simple_tfidf_time,simple_tfidf_results,lucene_bm25_time,lucene_bm25_results,lucene_tfidf_time,lucene_tfidf_results")
    
    for qid in sorted(query_data.keys()):
        d = query_data[qid]
        line = f'{qid},"{d["query"]}",{d["category"]}'
        for variant in ["simple_tsv_bm25", "simple_tsv_tfidf", "lucene_bm25", "lucene_tfidf"]:
            line += f',{d.get(f"{variant}_time", "")},{d.get(f"{variant}_results", "")}'
        lines.append(line)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Comparison CSV saved to: {output_path}")


def generate_markdown_report(all_results: List[Dict], output_path: str):
    """Generate comprehensive markdown report."""
    lines = []
    
    lines.append("# Benchmark Report: Simple TSV vs Lucene Index")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Number of queries:** {len(TEST_QUERIES)}")
    lines.append("")
    
    # Summary table
    lines.append("## Performance Summary")
    lines.append("")
    lines.append("| Index Type | Metric | Load Time (ms) | Avg Query Time (ms) | Total Time (ms) |")
    lines.append("|------------|--------|----------------|---------------------|-----------------|")
    
    for r in all_results:
        lines.append(f"| {r['index_type']} | {r['metric']} | {r['load_time_ms']:.1f} | {r['avg_time_ms']:.2f} | {r['total_time_ms']:.1f} |")
    
    lines.append("")
    
    # Query times by category
    lines.append("## Query Times by Category")
    lines.append("")
    
    categories = set(q["category"] for q in TEST_QUERIES)
    for cat in sorted(categories):
        lines.append(f"### {cat.replace('_', ' ').title()}")
        lines.append("")
        lines.append("| Query | Simple BM25 | Simple TF-IDF | Lucene BM25 | Lucene TF-IDF |")
        lines.append("|-------|-------------|---------------|-------------|---------------|")
        
        for q in [x for x in TEST_QUERIES if x["category"] == cat]:
            row = f"| {q['query']} |"
            for r in all_results:
                qr = next((x for x in r["queries"] if x["id"] == q["id"]), None)
                if qr:
                    row += f" {qr['time_ms']:.2f}ms |"
                else:
                    row += " - |"
            lines.append(row)
        lines.append("")
    
    # Top results comparison
    lines.append("## Top Result Comparison (Sample)")
    lines.append("")
    lines.append("Comparing top results for selected queries:")
    lines.append("")
    
    sample_queries = [6, 11, 21, 26, 31]  # chicken pasta, italian pasta, easy chicken dinner, lasagna, vegetarian dinner
    
    for qid in sample_queries:
        q = next((x for x in TEST_QUERIES if x["id"] == qid), None)
        if not q:
            continue
        
        lines.append(f"### Query: \"{q['query']}\"")
        lines.append("")
        lines.append("| Rank | Simple BM25 | Lucene BM25 |")
        lines.append("|------|-------------|-------------|")
        
        simple_bm25 = next((r for r in all_results if r["index_type"] == "simple_tsv" and r["metric"] == "bm25"), None)
        lucene_bm25 = next((r for r in all_results if r["index_type"] == "lucene" and r["metric"] == "bm25"), None)
        
        simple_results = []
        lucene_results = []
        
        if simple_bm25:
            qr = next((x for x in simple_bm25["queries"] if x["id"] == qid), None)
            if qr:
                simple_results = qr.get("results", [])
        
        if lucene_bm25:
            qr = next((x for x in lucene_bm25["queries"] if x["id"] == qid), None)
            if qr:
                lucene_results = qr.get("results", [])
        
        for i in range(5):
            s_title = simple_results[i]["title"][:40] if i < len(simple_results) else "-"
            l_title = lucene_results[i]["title"][:40] if i < len(lucene_results) else "-"
            lines.append(f"| {i+1} | {s_title} | {l_title} |")
        
        lines.append("")
    
    # Commands section
    lines.append("## Commands Used")
    lines.append("")
    lines.append("### Index Building")
    lines.append("")
    lines.append("```bash")
    lines.append("# Simple TSV Index")
    lines.append("cd /Users/marosbednar/programming/school/VINF")
    lines.append("source venv/bin/activate")
    lines.append("python -m indexer.simple_indexer --mode build")
    lines.append("")
    lines.append("# Lucene BM25 Index")
    lines.append("source venv314/bin/activate")
    lines.append("python -m indexer.lucene_indexer --input data/normalized/recipes_enriched.jsonl --output index/v2")
    lines.append("")
    lines.append("# Lucene TF-IDF Index")
    lines.append("python -m indexer.lucene_indexer --input data/normalized/recipes_enriched.jsonl --output index/v2_tfidf --similarity tfidf")
    lines.append("```")
    lines.append("")
    lines.append("### Search Commands")
    lines.append("")
    lines.append("```bash")
    lines.append("# Simple Index (Python 3.13)")
    lines.append("source venv/bin/activate")
    lines.append('python -m search_cli.run --index index/v1 --q "chicken pasta" --k 10')
    lines.append('python -m search_cli.run --index index/v1 --q "chicken pasta" --k 10 --metric tfidf')
    lines.append("")
    lines.append("# Lucene Index (Python 3.14)")
    lines.append("source venv314/bin/activate")
    lines.append('python -m search_cli.run --index index/v2 --q "chicken pasta" --k 10')
    lines.append('python -m search_cli.run --index index/v2_tfidf --q "chicken pasta" --k 10 --metric tfidf')
    lines.append("```")
    lines.append("")
    lines.append("### Benchmark Commands")
    lines.append("")
    lines.append("```bash")
    lines.append("# Run full benchmark (Python 3.14 for Lucene support)")
    lines.append("source venv314/bin/activate")
    lines.append("python eval/benchmark_queries.py")
    lines.append("```")
    lines.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Markdown report saved to: {output_path}")


def main():
    """Run benchmarks and generate reports."""
    print("=" * 60)
    print("Recipe Search Benchmark")
    print("=" * 60)
    print(f"Running {len(TEST_QUERIES)} test queries...")
    print()
    
    all_results = []
    
    # Simple index benchmarks
    print("Benchmarking Simple TSV Index...")
    try:
        print("  - BM25...")
        simple_bm25 = benchmark_simple_index("index/v1", TEST_QUERIES, "bm25")
        all_results.append(simple_bm25)
        print(f"    Avg time: {simple_bm25['avg_time_ms']:.2f}ms")
        
        print("  - TF-IDF...")
        simple_tfidf = benchmark_simple_index("index/v1", TEST_QUERIES, "tfidf")
        all_results.append(simple_tfidf)
        print(f"    Avg time: {simple_tfidf['avg_time_ms']:.2f}ms")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # Lucene index benchmarks
    print("\nBenchmarking Lucene Index...")
    try:
        print("  - BM25...")
        lucene_bm25 = benchmark_lucene_index("index/v2", TEST_QUERIES, "bm25")
        all_results.append(lucene_bm25)
        print(f"    Avg time: {lucene_bm25['avg_time_ms']:.2f}ms")
        
        print("  - TF-IDF...")
        lucene_tfidf = benchmark_lucene_index("index/v2_tfidf", TEST_QUERIES, "tfidf")
        all_results.append(lucene_tfidf)
        print(f"    Avg time: {lucene_tfidf['avg_time_ms']:.2f}ms")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # Generate reports
    print("\nGenerating reports...")
    
    # Create output directory
    output_dir = Path("eval/benchmark_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw JSON
    json_path = output_dir / f"benchmark_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"  Raw data: {json_path}")
    
    # Generate CSV for Excel
    csv_path = output_dir / f"benchmark_{timestamp}.csv"
    generate_csv_report(all_results, str(csv_path))
    
    # Generate comparison CSV
    comparison_path = output_dir / f"comparison_{timestamp}.csv"
    generate_comparison_csv(all_results, str(comparison_path))
    
    # Generate Markdown report
    md_path = output_dir / f"BENCHMARK_REPORT_{timestamp}.md"
    generate_markdown_report(all_results, str(md_path))
    
    # Summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    
    print("\n| Index Type | Metric | Load Time | Avg Query | Total Time |")
    print("|------------|--------|-----------|-----------|------------|")
    for r in all_results:
        print(f"| {r['index_type']:10} | {r['metric']:6} | {r['load_time_ms']:7.1f}ms | {r['avg_time_ms']:7.2f}ms | {r['total_time_ms']:8.1f}ms |")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
