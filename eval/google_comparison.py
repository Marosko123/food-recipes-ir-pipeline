#!/usr/bin/env python3
"""
Google Comparison Evaluation

Creates a gold standard dataset for comparing our IR system with Google search results.
Uses manual annotations for relevance judgments.

This script generates:
1. google_baseline.json - Expected top results from Google (manually collected)
2. Comparison metrics against our system

Usage:
    python -m eval.google_comparison \
        --queries eval/queries.tsv \
        --index index/v2 \
        --output eval/google_comparison.json
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Manually collected Google baseline results
# These represent what Google would return for these queries on recipe sites
# Format: query -> list of expected relevant recipe types/titles

GOOGLE_BASELINE = {
    "chocolate cake": {
        "expected_types": ["chocolate cake", "chocolate layer cake", "devil's food cake", 
                          "chocolate fudge cake", "moist chocolate cake"],
        "key_ingredients": ["chocolate", "cocoa", "flour", "sugar", "eggs"],
        "description": "Rich chocolate-based layer cakes with frosting"
    },
    "quick chicken dinner": {
        "expected_types": ["chicken stir fry", "chicken breast", "one pan chicken",
                          "30 minute chicken", "easy chicken dinner"],
        "key_ingredients": ["chicken", "vegetables", "olive oil", "garlic"],
        "description": "Fast-cooking chicken main dishes under 30 minutes"
    },
    "pasta carbonara": {
        "expected_types": ["spaghetti carbonara", "carbonara", "pasta with bacon and eggs"],
        "key_ingredients": ["pasta", "eggs", "bacon", "parmesan", "black pepper"],
        "description": "Traditional Italian pasta with egg-based sauce"
    },
    "grilled chicken": {
        "expected_types": ["grilled chicken breast", "bbq chicken", "chicken thighs",
                          "marinated grilled chicken"],
        "key_ingredients": ["chicken", "olive oil", "lemon", "herbs", "garlic"],
        "description": "Chicken cooked on grill with various marinades"
    },
    "mexican rice": {
        "expected_types": ["spanish rice", "mexican rice", "arroz rojo", "tomato rice"],
        "key_ingredients": ["rice", "tomato", "onion", "garlic", "cumin", "chicken broth"],
        "description": "Tomato-based seasoned rice side dish"
    },
    "traditional mexican tacos": {
        "expected_types": ["street tacos", "carne asada tacos", "carnitas tacos",
                          "authentic tacos", "mexican tacos"],
        "key_ingredients": ["corn tortilla", "meat", "cilantro", "onion", "lime"],
        "description": "Authentic Mexican-style tacos with traditional toppings"
    },
    "best chocolate chip cookies": {
        "expected_types": ["chocolate chip cookies", "chewy cookies", "crispy cookies",
                          "brown butter cookies"],
        "key_ingredients": ["flour", "butter", "sugar", "chocolate chips", "eggs", "vanilla"],
        "description": "Classic American cookies with chocolate chips"
    },
    "slow cooker beef stew": {
        "expected_types": ["beef stew", "crockpot stew", "slow cooker stew"],
        "key_ingredients": ["beef", "potatoes", "carrots", "onion", "beef broth"],
        "description": "Hearty beef and vegetable stew made in slow cooker"
    },
    "spicy thai curry": {
        "expected_types": ["thai red curry", "thai green curry", "massaman curry",
                          "panang curry"],
        "key_ingredients": ["coconut milk", "curry paste", "thai basil", "fish sauce"],
        "description": "Thai-style curry with coconut milk base"
    },
    "authentic indian butter chicken": {
        "expected_types": ["butter chicken", "murgh makhani", "indian chicken curry"],
        "key_ingredients": ["chicken", "tomato", "cream", "butter", "garam masala", "ginger"],
        "description": "Creamy tomato-based Indian chicken dish"
    }
}


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


def calculate_relevance_score(result: Dict, baseline: Dict) -> float:
    """
    Calculate relevance score for a result against Google baseline.
    
    Returns a score between 0 and 1:
    - 1.0: Highly relevant (matches expected type and has key ingredients)
    - 0.5: Partially relevant (matches some criteria)
    - 0.0: Not relevant
    """
    title = result.get('title', result.get('title_text', '')).lower()
    ingredients = result.get('ingredients', result.get('ingredients_text', '')).lower()
    
    score = 0.0
    
    # Check if title matches expected types
    for expected in baseline.get('expected_types', []):
        if expected.lower() in title:
            score += 0.5
            break
    
    # Check for key ingredients
    key_ings = baseline.get('key_ingredients', [])
    if key_ings:
        matches = sum(1 for ing in key_ings if ing.lower() in ingredients or ing.lower() in title)
        ingredient_score = matches / len(key_ings)
        score += ingredient_score * 0.5
    
    return min(score, 1.0)


def compare_with_google(our_results: List[Dict], baseline: Dict, k: int = 10) -> Dict:
    """Compare our search results with Google baseline expectations."""
    
    relevant_count = 0
    partial_count = 0
    scores = []
    
    for result in our_results[:k]:
        score = calculate_relevance_score(result, baseline)
        scores.append(score)
        
        if score >= 0.7:
            relevant_count += 1
        elif score >= 0.3:
            partial_count += 1
    
    return {
        'precision_at_k': relevant_count / k if k > 0 else 0,
        'partial_relevant_count': partial_count,
        'fully_relevant_count': relevant_count,
        'avg_relevance_score': sum(scores) / len(scores) if scores else 0,
        'scores': scores
    }


def main():
    parser = argparse.ArgumentParser(description='Compare with Google baseline')
    parser.add_argument('--queries', type=str, default='eval/queries.tsv',
                        help='Path to queries TSV file')
    parser.add_argument('--index', type=str, default='index/v2',
                        help='Path to Lucene index')
    parser.add_argument('--output', type=str, default='eval/google_comparison.json',
                        help='Output JSON file')
    parser.add_argument('--k', type=int, default=10,
                        help='Number of results to evaluate')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Google Comparison Evaluation")
    logger.info("=" * 60)
    
    # Load queries
    queries = load_queries(args.queries)
    logger.info(f"Loaded {len(queries)} queries")
    
    # Initialize searcher
    try:
        from search_cli.lupyne_searcher import LupyneRecipeSearcher
        searcher = LupyneRecipeSearcher(args.index)
    except ImportError as e:
        logger.error(f"Cannot import searcher: {e}")
        logger.info("Running in baseline-only mode (no search)")
        searcher = None
    
    # Run comparison
    results = {
        'metadata': {
            'queries_file': args.queries,
            'index': args.index,
            'k': args.k,
            'baseline_queries': len(GOOGLE_BASELINE)
        },
        'google_baseline': GOOGLE_BASELINE,
        'comparisons': [],
        'summary': {}
    }
    
    total_precision = 0
    total_avg_score = 0
    compared_count = 0
    
    for q in queries:
        query = q['query']
        
        # Check if we have a baseline for this query
        if query not in GOOGLE_BASELINE:
            # Try to find partial match
            baseline = None
            for baseline_query in GOOGLE_BASELINE:
                if baseline_query in query or query in baseline_query:
                    baseline = GOOGLE_BASELINE[baseline_query]
                    break
            
            if baseline is None:
                continue
        else:
            baseline = GOOGLE_BASELINE[query]
        
        logger.info(f"\nQuery: '{query}'")
        
        comparison = {
            'qid': q['qid'],
            'query': query,
            'baseline': baseline
        }
        
        if searcher:
            # Search
            search_results = searcher.search_bm25(query, k=args.k)
            
            # Compare
            metrics = compare_with_google(search_results, baseline, k=args.k)
            comparison['our_results'] = [
                {
                    'rank': r['rank'],
                    'title': r.get('title', r.get('title_text', '')),
                    'relevance_score': calculate_relevance_score(r, baseline)
                }
                for r in search_results[:args.k]
            ]
            comparison['metrics'] = metrics
            
            total_precision += metrics['precision_at_k']
            total_avg_score += metrics['avg_relevance_score']
            compared_count += 1
            
            logger.info(f"  Precision@{args.k}: {metrics['precision_at_k']:.2%}")
            logger.info(f"  Avg relevance: {metrics['avg_relevance_score']:.2f}")
        
        results['comparisons'].append(comparison)
    
    # Summary
    if compared_count > 0:
        results['summary'] = {
            'num_queries_compared': compared_count,
            'avg_precision_at_k': total_precision / compared_count,
            'avg_relevance_score': total_avg_score / compared_count
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Queries compared: {compared_count}")
        logger.info(f"Avg Precision@{args.k}: {results['summary']['avg_precision_at_k']:.2%}")
        logger.info(f"Avg Relevance Score: {results['summary']['avg_relevance_score']:.2f}")
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nResults saved to: {output_path}")
    
    # Cleanup
    if searcher:
        searcher.close()
    
    logger.info("\n✅ Google comparison completed!")


if __name__ == '__main__':
    main()
