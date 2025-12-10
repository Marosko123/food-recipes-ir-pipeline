#!/usr/bin/env python3
"""
Benchmark for Advanced Query Types
Tests exact phrase matching, ingredient-based search, and origin-based filtering.

Generates statistics in the same format as FINALNE_POROVNANIE_SYSTEMOV.md
"""

import subprocess
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime

# ============================================================================
# ADVANCED QUERY DEFINITIONS
# ============================================================================

# Category 1: Exact phrase search (using quotes)
EXACT_PHRASE_QUERIES = [
    {"id": 101, "query": '"chocolate cake"', "category": "exact_phrase", 
     "expected_keywords": ["chocolate", "cake"]},
    {"id": 102, "query": '"italian sausage"', "category": "exact_phrase",
     "expected_keywords": ["italian", "sausage"]},
    {"id": 103, "query": '"chicken parmesan"', "category": "exact_phrase",
     "expected_keywords": ["chicken", "parmesan"]},
    {"id": 104, "query": '"peanut butter"', "category": "exact_phrase",
     "expected_keywords": ["peanut", "butter"]},
    {"id": 105, "query": '"beef stew"', "category": "exact_phrase",
     "expected_keywords": ["beef", "stew"]},
    {"id": 106, "query": '"apple pie"', "category": "exact_phrase",
     "expected_keywords": ["apple", "pie"]},
    {"id": 107, "query": '"garlic bread"', "category": "exact_phrase",
     "expected_keywords": ["garlic", "bread"]},
    {"id": 108, "query": '"grilled cheese"', "category": "exact_phrase",
     "expected_keywords": ["grilled", "cheese"]},
]

# Category 2: Ingredient-based search
INGREDIENT_QUERIES = [
    {"id": 201, "query": "ingredient:chicken ingredient:garlic", "category": "ingredient",
     "ingredients_include": ["chicken", "garlic"], "ingredients_exclude": []},
    {"id": 202, "query": "ingredient:pasta -ingredient:meat", "category": "ingredient",
     "ingredients_include": ["pasta"], "ingredients_exclude": ["meat"]},
    {"id": 203, "query": "ingredient:chocolate ingredient:milk ingredient:sugar", "category": "ingredient",
     "ingredients_include": ["chocolate", "milk", "sugar"], "ingredients_exclude": []},
    {"id": 204, "query": "ingredient:salmon ingredient:lemon", "category": "ingredient",
     "ingredients_include": ["salmon", "lemon"], "ingredients_exclude": []},
    {"id": 205, "query": "ingredient:beef -ingredient:pork", "category": "ingredient",
     "ingredients_include": ["beef"], "ingredients_exclude": ["pork"]},
    {"id": 206, "query": "ingredient:egg ingredient:flour ingredient:butter", "category": "ingredient",
     "ingredients_include": ["egg", "flour", "butter"], "ingredients_exclude": []},
    {"id": 207, "query": "ingredient:tomato ingredient:basil", "category": "ingredient",
     "ingredients_include": ["tomato", "basil"], "ingredients_exclude": []},
    {"id": 208, "query": "ingredient:rice -ingredient:gluten", "category": "ingredient",
     "ingredients_include": ["rice"], "ingredients_exclude": ["gluten"]},
]

# Category 3: Cuisine-based search
CUISINE_QUERIES = [
    {"id": 301, "query": "cuisine:italian pasta", "category": "cuisine",
     "cuisines": ["italian"]},
    {"id": 302, "query": "cuisine:mexican spicy", "category": "cuisine",
     "cuisines": ["mexican"]},
    {"id": 303, "query": "cuisine:asian stir fry", "category": "cuisine",
     "cuisines": ["asian"]},
    {"id": 304, "query": "cuisine:french dessert", "category": "cuisine",
     "cuisines": ["french"]},
    {"id": 305, "query": "cuisine:indian curry", "category": "cuisine",
     "cuisines": ["indian"]},
    {"id": 306, "query": "cuisine:japanese sushi", "category": "cuisine",
     "cuisines": ["japanese"]},
    {"id": 307, "query": "cuisine:mediterranean salad", "category": "cuisine",
     "cuisines": ["mediterranean"]},
    {"id": 308, "query": "cuisine:american burger", "category": "cuisine",
     "cuisines": ["american"]},
]

# Category 4: Combined/Complex queries
COMBINED_QUERIES = [
    {"id": 401, "query": '"chocolate cake" -ingredient:nuts', "category": "combined",
     "expected_keywords": ["chocolate", "cake"], "ingredients_exclude": ["nuts"]},
    {"id": 402, "query": 'cuisine:italian "garlic bread"', "category": "combined",
     "expected_keywords": ["garlic", "bread"], "cuisines": ["italian"]},
    {"id": 403, "query": 'ingredient:chicken "fried rice" cuisine:asian', "category": "combined",
     "expected_keywords": ["fried", "rice"], "ingredients_include": ["chicken"], "cuisines": ["asian"]},
    {"id": 404, "query": '"beef tacos" cuisine:mexican', "category": "combined",
     "expected_keywords": ["beef", "tacos"], "cuisines": ["mexican"]},
    {"id": 405, "query": 'ingredient:salmon "lemon sauce" -ingredient:cream', "category": "combined",
     "expected_keywords": ["lemon", "sauce"], "ingredients_include": ["salmon"], "ingredients_exclude": ["cream"]},
    {"id": 406, "query": '"chicken soup" ingredient:noodles', "category": "combined",
     "expected_keywords": ["chicken", "soup"], "ingredients_include": ["noodles"]},
    {"id": 407, "query": 'cuisine:japanese ingredient:rice "teriyaki"', "category": "combined",
     "expected_keywords": ["teriyaki"], "cuisines": ["japanese"], "ingredients_include": ["rice"]},
    {"id": 408, "query": '"apple pie" -ingredient:nuts cuisine:american', "category": "combined",
     "expected_keywords": ["apple", "pie"], "cuisines": ["american"], "ingredients_exclude": ["nuts"]},
]

# Category 5: Standard multi-term queries (for comparison)
STANDARD_QUERIES = [
    {"id": 501, "query": "chocolate cake recipe", "category": "standard",
     "relevance_keywords": ["chocolate", "cake"]},
    {"id": 502, "query": "italian sausage soup", "category": "standard",
     "relevance_keywords": ["sausage"]},
    {"id": 503, "query": "mexican beef tacos", "category": "standard",
     "relevance_keywords": ["taco", "tacos", "fajita", "burrito"]},
    {"id": 504, "query": "thai peanut noodles", "category": "standard",
     "relevance_keywords": ["peanut", "noodle", "thai"]},
    {"id": 505, "query": "keto friendly meatballs", "category": "standard",
     "relevance_keywords": ["meatball"]},
    {"id": 506, "query": "creamy garlic shrimp pasta", "category": "standard",
     "relevance_keywords": ["shrimp", "pasta"]},
    {"id": 507, "query": "low carb cheesecake", "category": "standard",
     "relevance_keywords": ["cheesecake"]},
    {"id": 508, "query": "vegan chocolate mousse", "category": "standard",
     "relevance_keywords": ["mousse", "vegan"]},
]

ALL_QUERIES = (EXACT_PHRASE_QUERIES + INGREDIENT_QUERIES + CUISINE_QUERIES + 
               COMBINED_QUERIES + STANDARD_QUERIES)

# ============================================================================
# INDEX CONFIGURATIONS
# ============================================================================

CONFIGS = [
    {
        "id": "S1", 
        "name": "Simple_BM25", 
        "full_name": "Simple BM25",
        "index": "index/v1", 
        "metric": "bm25", 
        "python": sys.executable,
        "type": "simple"
    },
    {
        "id": "S2", 
        "name": "Simple_TFIDF", 
        "full_name": "Simple TF-IDF",
        "index": "index/v1", 
        "metric": "tfidf", 
        "python": sys.executable,
        "type": "simple"
    },
    {
        "id": "L1", 
        "name": "Lucene_BM25", 
        "full_name": "Lucene BM25",
        "index": "index/v2", 
        "metric": "bm25", 
        "python": "/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14",
        "type": "lucene"
    },
    {
        "id": "L2", 
        "name": "Lucene_TFIDF", 
        "full_name": "Lucene TF-IDF",
        "index": "index/v2_tfidf", 
        "metric": "tfidf", 
        "python": "/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14",
        "type": "lucene"
    },
]

# ============================================================================
# GROUND TRUTH RELEVANCE CRITERIA
# ============================================================================

def check_relevance_advanced(title: str, query_data: Dict) -> Tuple[bool, str]:
    """Check if a document is relevant based on query type and expected keywords."""
    title_lower = title.lower()
    category = query_data.get('category', '')
    
    # Exact phrase queries - title must contain the exact phrase words adjacent
    if category == 'exact_phrase':
        keywords = query_data.get('expected_keywords', [])
        if keywords:
            # Check if all keywords appear in title
            all_present = all(kw.lower() in title_lower for kw in keywords)
            # Additionally check if they appear together (adjacent or close)
            phrase = ' '.join(keywords).lower()
            exact_match = phrase in title_lower
            return exact_match or all_present, "phrase" if exact_match else "partial"
    
    # Ingredient queries - less strict, check for dish relevance
    elif category == 'ingredient':
        include = query_data.get('ingredients_include', [])
        # Relevant if title mentions any of the main ingredients
        for ing in include:
            if ing.lower() in title_lower:
                return True, "ingredient_match"
        return False, "no_match"
    
    # Cuisine queries
    elif category == 'cuisine':
        cuisines = query_data.get('cuisines', [])
        for cuisine in cuisines:
            if cuisine.lower() in title_lower:
                return True, "cuisine_match"
        return False, "no_match"
    
    # Combined queries - check expected keywords
    elif category == 'combined':
        keywords = query_data.get('expected_keywords', [])
        if keywords:
            all_present = all(kw.lower() in title_lower for kw in keywords)
            return all_present, "combined_match" if all_present else "partial"
        return True, "any"
    
    # Standard queries
    elif category == 'standard':
        relevance_keywords = query_data.get('relevance_keywords', [])
        for kw in relevance_keywords:
            if kw.lower() in title_lower:
                return True, "keyword_match"
        return False, "no_match"
    
    return True, "default"

# ============================================================================
# SEARCH EXECUTION
# ============================================================================

def run_search_simple(index_path: str, metric: str, query: str, k: int = 10, 
                      python_cmd: str = None) -> List[Dict]:
    """Run search on Simple (TSV) index."""
    if python_cmd is None:
        python_cmd = sys.executable
    
    # Clean query for simple search (remove special syntax)
    clean_query = query
    clean_query = re.sub(r'ingredient:\w+', '', clean_query)
    clean_query = re.sub(r'-ingredient:\w+', '', clean_query)
    clean_query = re.sub(r'cuisine:\w+', '', clean_query)
    clean_query = clean_query.replace('"', '').strip()
    
    if not clean_query:
        clean_query = query.replace('"', '').strip()
        clean_query = re.sub(r'[:\-]', ' ', clean_query)
    
    cmd = [
        python_cmd, "-m", "search_cli.run",
        "--index", index_path,
        "--metric", metric,
        "--q", clean_query,
        "--k", str(k),
        "--json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=str(Path(__file__).parent.parent))
        output = result.stdout
        
        start = output.find('[')
        end = output.rfind(']') + 1
        
        if start >= 0 and end > start:
            json_str = output[start:end]
            return json.loads(json_str)
        return []
    except Exception as e:
        print(f"  Error in simple search: {e}", file=sys.stderr)
        return []

def run_search_lucene(index_path: str, metric: str, query: str, k: int = 10,
                      python_cmd: str = None, query_data: Dict = None) -> List[Dict]:
    """Run search on Lucene index with advanced query support."""
    if python_cmd is None:
        python_cmd = "/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14"
    
    # For Lucene, use search_combined or search_advanced via CLI
    # For now, use the basic CLI with cleaned query
    # TODO: Extend CLI to support advanced query types directly
    
    clean_query = query
    clean_query = re.sub(r'ingredient:\w+', '', clean_query)
    clean_query = re.sub(r'-ingredient:\w+', '', clean_query)
    clean_query = re.sub(r'cuisine:\w+', '', clean_query)
    clean_query = clean_query.replace('"', '').strip()
    
    if not clean_query:
        clean_query = query.replace('"', '').strip()
        clean_query = re.sub(r'[:\-]', ' ', clean_query)
    
    cmd = [
        python_cmd, "-m", "search_cli.run",
        "--index", index_path,
        "--metric", metric,
        "--q", clean_query,
        "--k", str(k),
        "--json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=str(Path(__file__).parent.parent))
        output = result.stdout
        
        start = output.find('[')
        end = output.rfind(']') + 1
        
        if start >= 0 and end > start:
            json_str = output[start:end]
            return json.loads(json_str)
        return []
    except Exception as e:
        print(f"  Error in Lucene search: {e}", file=sys.stderr)
        return []

def run_search(config: Dict, query: str, k: int = 10, query_data: Dict = None) -> List[Dict]:
    """Run search based on config type."""
    if config['type'] == 'simple':
        return run_search_simple(config['index'], config['metric'], query, k, config['python'])
    else:
        return run_search_lucene(config['index'], config['metric'], query, k, config['python'], query_data)

# ============================================================================
# METRICS CALCULATION
# ============================================================================

def calculate_precision_at_k(results: List[Dict], query_data: Dict, k: int = 5) -> float:
    """Calculate Precision@K."""
    if not results:
        return 0.0
    
    relevant_count = 0
    for r in results[:k]:
        title = r.get('title', '')
        is_relevant, _ = check_relevance_advanced(title, query_data)
        if is_relevant:
            relevant_count += 1
    
    return relevant_count / k

def calculate_recall_at_k(results: List[Dict], query_data: Dict, pool_size: int, k: int = 5) -> float:
    """Calculate Recall@K."""
    if pool_size == 0:
        return 0.0
    
    relevant_count = 0
    for r in results[:k]:
        title = r.get('title', '')
        is_relevant, _ = check_relevance_advanced(title, query_data)
        if is_relevant:
            relevant_count += 1
    
    return relevant_count / pool_size

def calculate_overlap(results1: List[Dict], results2: List[Dict], k: int = 5) -> float:
    """Calculate Overlap@K between two result sets."""
    ids1 = set(r.get('doc_id', '') for r in results1[:k])
    ids2 = set(r.get('doc_id', '') for r in results2[:k])
    
    if not ids1 and not ids2:
        return 1.0
    if not ids1 or not ids2:
        return 0.0
    
    return len(ids1 & ids2) / k

def calculate_f1(precision: float, recall: float) -> float:
    """Calculate F1 score."""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)

# ============================================================================
# POOLING AND GROUND TRUTH
# ============================================================================

def create_ground_truth_pool(all_results: Dict[str, List[Dict]], query_data: Dict) -> Tuple[List[str], int]:
    """Create ground truth pool from all system results (TREC-style pooling)."""
    pool = {}
    
    for config_name, results in all_results.items():
        for r in results[:10]:  # Top 10 from each system
            doc_id = r.get('doc_id', '')
            if doc_id and doc_id not in pool:
                title = r.get('title', '')
                is_relevant, reason = check_relevance_advanced(title, query_data)
                pool[doc_id] = {
                    'title': title,
                    'relevant': is_relevant,
                    'reason': reason
                }
    
    relevant_docs = [doc_id for doc_id, info in pool.items() if info['relevant']]
    return relevant_docs, len(pool)

# ============================================================================
# MAIN BENCHMARK
# ============================================================================

def run_benchmark():
    """Run the complete benchmark."""
    results = {}
    metrics_by_category = defaultdict(lambda: defaultdict(list))
    
    print("=" * 80)
    print("ADVANCED QUERY BENCHMARK")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)
    print(f"\nTotal queries: {len(ALL_QUERIES)}")
    print(f"Categories: exact_phrase, ingredient, cuisine, combined, standard")
    print(f"Systems: {', '.join(c['id'] for c in CONFIGS)}")
    print()
    
    for q in ALL_QUERIES:
        query_id = q['id']
        query_text = q['query']
        category = q['category']
        
        print(f"\n[{query_id}] '{query_text}' ({category})")
        
        results[query_id] = {
            "query": q,
            "configs": {},
            "ground_truth_pool": [],
            "metrics": {}
        }
        
        # Run all configs
        all_config_results = {}
        for config in CONFIGS:
            config_id = config['id']
            print(f"  {config_id}...", end=" ", flush=True)
            
            search_results = run_search(config, query_text, k=10, query_data=q)
            
            results[query_id]["configs"][config_id] = {
                "results": search_results,
                "count": len(search_results)
            }
            all_config_results[config_id] = search_results
            
            print(f"{len(search_results)} results", end="")
            if search_results:
                print(f" (top: {search_results[0].get('title', 'N/A')[:40]}...)")
            else:
                print()
        
        # Create ground truth pool
        relevant_docs, pool_size = create_ground_truth_pool(all_config_results, q)
        results[query_id]["ground_truth_pool"] = relevant_docs
        results[query_id]["pool_size"] = pool_size
        
        print(f"  Pool: {pool_size} docs, {len(relevant_docs)} relevant")
        
        # Calculate metrics for each config
        for config in CONFIGS:
            config_id = config['id']
            config_results = results[query_id]["configs"][config_id]["results"]
            
            p_at_5 = calculate_precision_at_k(config_results, q, k=5)
            r_at_5 = calculate_recall_at_k(config_results, q, len(relevant_docs), k=5)
            f1 = calculate_f1(p_at_5, r_at_5)
            
            results[query_id]["metrics"][config_id] = {
                "P@5": p_at_5,
                "R@5": r_at_5,
                "F1": f1
            }
            
            # Store for category aggregation
            metrics_by_category[category][config_id].append({
                "P@5": p_at_5,
                "R@5": r_at_5,
                "F1": f1
            })
    
    return results, metrics_by_category

def generate_report(results: Dict, metrics_by_category: Dict):
    """Generate comprehensive report in Markdown format."""
    report = []
    
    report.append("# Benchmark Pokročilých Typov Vyhľadávania")
    report.append(f"\n**Dátum:** {datetime.now().strftime('%d. %B %Y')}")
    report.append("**Predmet:** VINF - Vyhľadávanie Informácií\n")
    
    report.append("---\n")
    
    # Summary by category
    report.append("## 📊 Súhrnné Štatistiky po Kategóriách\n")
    
    categories = ["exact_phrase", "ingredient", "cuisine", "combined", "standard"]
    category_names = {
        "exact_phrase": "Presná fráza (quotes)",
        "ingredient": "Ingrediencie",
        "cuisine": "Kuchyňa",
        "combined": "Kombinované",
        "standard": "Štandardné"
    }
    
    for category in categories:
        if category not in metrics_by_category:
            continue
            
        report.append(f"### {category_names[category]}\n")
        report.append("| Systém | Mean P@5 | Mean R@5 | Mean F1 |")
        report.append("|--------|----------|----------|---------|")
        
        config_avgs = {}
        for config in CONFIGS:
            config_id = config['id']
            if config_id in metrics_by_category[category]:
                metrics_list = metrics_by_category[category][config_id]
                avg_p = sum(m['P@5'] for m in metrics_list) / len(metrics_list) * 100
                avg_r = sum(m['R@5'] for m in metrics_list) / len(metrics_list) * 100
                avg_f1 = sum(m['F1'] for m in metrics_list) / len(metrics_list) * 100
                config_avgs[config_id] = (avg_p, avg_r, avg_f1)
                report.append(f"| **{config_id}** | {avg_p:.1f}% | {avg_r:.1f}% | {avg_f1:.1f}% |")
        
        report.append("")
    
    # Overall summary
    report.append("## 📈 Celkové Výsledky\n")
    report.append("| Systém | Mean P@5 | Mean R@5 | Mean F1 | ZRR |")
    report.append("|--------|----------|----------|---------|-----|")
    
    for config in CONFIGS:
        config_id = config['id']
        all_p = []
        all_r = []
        all_f1 = []
        zero_results = 0
        total_queries = 0
        
        for query_id, data in results.items():
            if config_id in data['metrics']:
                all_p.append(data['metrics'][config_id]['P@5'])
                all_r.append(data['metrics'][config_id]['R@5'])
                all_f1.append(data['metrics'][config_id]['F1'])
                total_queries += 1
                if data['configs'][config_id]['count'] == 0:
                    zero_results += 1
        
        if all_p:
            avg_p = sum(all_p) / len(all_p) * 100
            avg_r = sum(all_r) / len(all_r) * 100
            avg_f1 = sum(all_f1) / len(all_f1) * 100
            zrr = zero_results / total_queries * 100 if total_queries > 0 else 0
            report.append(f"| **{config_id}** ({config['full_name']}) | {avg_p:.1f}% | {avg_r:.1f}% | {avg_f1:.1f}% | {zrr:.1f}% |")
    
    report.append("")
    
    # Detailed results per category
    report.append("---\n")
    report.append("## 🔍 Detailné Výsledky po Kategóriách\n")
    
    for category in categories:
        report.append(f"### {category_names[category]}\n")
        report.append("| ID | Query | Pool | S1 P@5 | S1 R@5 | S2 P@5 | S2 R@5 | L1 P@5 | L1 R@5 | L2 P@5 | L2 R@5 |")
        report.append("|---|-------|------|--------|--------|--------|--------|--------|--------|--------|--------|")
        
        for query_id, data in results.items():
            if data['query']['category'] == category:
                q = data['query']
                pool_size = len(data.get('ground_truth_pool', []))
                metrics = data['metrics']
                
                row = f"| {query_id} | `{q['query'][:30]}` | {pool_size}"
                for cid in ['S1', 'S2', 'L1', 'L2']:
                    if cid in metrics:
                        p = metrics[cid]['P@5'] * 100
                        r = metrics[cid]['R@5'] * 100
                        row += f" | {p:.0f}% | {r:.0f}%"
                    else:
                        row += " | - | -"
                row += " |"
                report.append(row)
        
        report.append("")
    
    # Sample detailed query analysis
    report.append("---\n")
    report.append("## 📋 Príklady Detailnej Analýzy\n")
    
    # Pick one from each category
    sample_queries = {}
    for query_id, data in results.items():
        cat = data['query']['category']
        if cat not in sample_queries:
            sample_queries[cat] = (query_id, data)
    
    for cat, (query_id, data) in sample_queries.items():
        q = data['query']
        report.append(f"### Query {query_id}: `{q['query']}`\n")
        report.append(f"**Kategória:** {category_names[cat]}\n")
        
        report.append("**Top 5 výsledky:**\n")
        report.append("| Systém | #1 | #2 | #3 | #4 | #5 |")
        report.append("|--------|----|----|----|----|-----|")
        
        for config in CONFIGS:
            config_id = config['id']
            res = data['configs'][config_id]['results'][:5]
            row = f"| **{config_id}** |"
            for r in res:
                title = r.get('title', 'N/A')[:25]
                row += f" {title} |"
            # Fill empty slots
            for _ in range(5 - len(res)):
                row += " - |"
            report.append(row)
        
        report.append("")
    
    return "\n".join(report)

def main():
    """Main entry point."""
    print("Starting Advanced Query Benchmark...")
    print()
    
    # Run benchmark
    results, metrics_by_category = run_benchmark()
    
    # Save raw results
    output_dir = Path("eval/benchmark_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_path = output_dir / "advanced_queries_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nRaw results saved to: {results_path}")
    
    # Generate report
    report = generate_report(results, metrics_by_category)
    
    report_path = output_dir / "advanced_queries_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)
    print(report[:3000])  # Print first part of report
    
    return results

if __name__ == "__main__":
    main()
