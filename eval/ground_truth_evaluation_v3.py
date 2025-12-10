#!/usr/bin/env python3
"""
Ground Truth Evaluation v3 - S korektnými query ID
==================================================

10 vybraných queries z benchmarku (správne ID z JSON):
  1: italian sausage soup
  6: mexican beef tacos  
  7: thai peanut noodles
  14: keto friendly meatballs
  3: creamy garlic shrimp pasta
  11: low carb cheesecake
  19: pan fried pork chops
  13: vegan chocolate mousse
  12: gluten free brownies
  17: grilled vegetables marinade
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import re

# Správne mapovanie query ID z JSON súboru
SELECTED_QUERIES = {
    1: "italian sausage soup",
    6: "mexican beef tacos",
    7: "thai peanut noodles",
    14: "keto friendly meatballs",
    3: "creamy garlic shrimp pasta",
    11: "low carb cheesecake",
    19: "pan fried pork chops",
    13: "vegan chocolate mousse",
    12: "gluten free brownies",
    17: "grilled vegetables marinade",
}

# Sémantické kritériá - dokument je relevantný ak názov obsahuje pattern
SEMANTIC_CRITERIA = {
    1: [r'sausage'],  # italian sausage soup - akýkoľvek sausage recept
    6: [r'taco', r'fajita', r'burrito', r'enchilada', r'mexican.*beef', r'beef.*mexican'],  # mexican beef tacos
    7: [r'thai', r'peanut.*noodle', r'noodle.*peanut', r'pad\s*thai'],  # thai peanut noodles
    14: [r'meatball'],  # keto friendly meatballs
    3: [r'shrimp', r'garlic.*shrimp', r'shrimp.*garlic', r'scampi'],  # creamy garlic shrimp pasta
    11: [r'cheesecake', r'cheese\s*cake'],  # low carb cheesecake
    19: [r'pork.*chop', r'chop.*pork'],  # pan fried pork chops
    13: [r'mousse', r'chocolate.*mousse', r'vegan.*chocolate'],  # vegan chocolate mousse
    12: [r'brownie'],  # gluten free brownies
    17: [r'marinade', r'grill.*vegetable', r'vegetable.*grill'],  # grilled vegetables marinade
}


def check_relevance(doc: Dict, query_id: int) -> Tuple[bool, str]:
    """Skontroluje relevanciu pomocou sémantických kritérií."""
    title = doc.get('title', '').lower()
    patterns = SEMANTIC_CRITERIA.get(query_id, [])
    
    for pattern in patterns:
        if re.search(pattern, title, re.IGNORECASE):
            return True, f"match: {pattern}"
    
    return False, "no match"


def load_results(results_file: Path) -> Dict:
    """Načíta výsledky."""
    with open(results_file, 'r') as f:
        return json.load(f)


def create_pooled_documents(results: Dict, query_ids: List[int], top_k: int = 10) -> Dict[int, Dict[str, Dict]]:
    """Vytvorí pooled set dokumentov pre vybrané queries."""
    pools = defaultdict(dict)
    
    for query_id in query_ids:
        query_id_str = str(query_id)
        if query_id_str not in results:
            continue
            
        query_data = results[query_id_str]
        configs = query_data.get('configs', {})
        
        for config_name, config_data in configs.items():
            for doc in config_data.get('results', [])[:top_k]:
                doc_id = doc.get('doc_id')
                if doc_id and doc_id not in pools[query_id]:
                    pools[query_id][doc_id] = {
                        'doc_id': doc_id,
                        'title': doc.get('title', ''),
                        'description': doc.get('description', ''),
                        'ingredients': doc.get('ingredients', ''),
                        'url': doc.get('url', ''),
                        'found_by': [config_name]
                    }
                elif doc_id:
                    pools[query_id][doc_id]['found_by'].append(config_name)
    
    return pools


def annotate_relevance(pools: Dict[int, Dict[str, Dict]]) -> Tuple[Dict, Dict]:
    """Anotuje relevanciu."""
    annotations = {}
    details = {}
    
    for query_id, docs in pools.items():
        annotations[query_id] = {}
        details[query_id] = {}
        
        for doc_id, doc in docs.items():
            is_relevant, reason = check_relevance(doc, query_id)
            annotations[query_id][doc_id] = is_relevant
            details[query_id][doc_id] = {
                'title': doc['title'],
                'relevant': is_relevant,
                'reason': reason,
                'found_by': doc['found_by']
            }
    
    return annotations, details


def calculate_metrics(results: Dict, annotations: Dict[int, Dict[str, bool]], query_ids: List[int], top_k: int = 5) -> Dict:
    """Vypočíta Precision@K a Recall@K."""
    metrics = {}
    systems = ['Simple_BM25', 'Simple_TFIDF', 'Lucene_BM25', 'Lucene_TFIDF']
    
    for query_id in query_ids:
        query_id_str = str(query_id)
        if query_id_str not in results:
            continue
            
        query_data = results[query_id_str]
        total_relevant = sum(1 for is_rel in annotations.get(query_id, {}).values() if is_rel)
        
        metrics[query_id] = {
            'query': SELECTED_QUERIES[query_id],
            'total_relevant_in_pool': total_relevant,
            'systems': {}
        }
        
        for system in systems:
            config_data = query_data.get('configs', {}).get(system, {})
            results_list = config_data.get('results', [])[:top_k]
            
            relevant_in_top_k = 0
            top_k_docs = []
            
            for doc in results_list:
                doc_id = doc.get('doc_id')
                is_relevant = annotations.get(query_id, {}).get(doc_id, False)
                if is_relevant:
                    relevant_in_top_k += 1
                top_k_docs.append({
                    'rank': doc.get('rank', 0),
                    'title': doc.get('title', ''),
                    'relevant': is_relevant
                })
            
            # Precision@K = relevantné v top K / K
            precision = relevant_in_top_k / top_k if top_k > 0 else 0
            
            # Recall@K = relevantné v top K / celkový počet relevantných
            recall = relevant_in_top_k / total_relevant if total_relevant > 0 else 0
            
            metrics[query_id]['systems'][system] = {
                'precision_at_k': precision,
                'recall_at_k': recall,
                'relevant_in_top_k': relevant_in_top_k,
                'top_k_docs': top_k_docs
            }
    
    return metrics


def print_detailed_report(metrics: Dict, details: Dict, query_ids: List[int]):
    """Vypíše detailný report."""
    print("\n" + "="*100)
    print("GROUND TRUTH EVALUATION - 10 VYBRANÝCH QUERIES")
    print("="*100)
    
    systems = ['Simple_BM25', 'Simple_TFIDF', 'Lucene_BM25', 'Lucene_TFIDF']
    short_names = {'Simple_BM25': 'S1', 'Simple_TFIDF': 'S2', 'Lucene_BM25': 'L1', 'Lucene_TFIDF': 'L2'}
    
    for idx, query_id in enumerate(query_ids, 1):
        if query_id not in metrics:
            continue
            
        qm = metrics[query_id]
        print(f"\n{'─'*100}")
        print(f"#{idx} (ID={query_id}): \"{qm['query']}\"")
        print(f"Relevantných v poole: {qm['total_relevant_in_pool']}")
        
        # Detaily relevantných
        print("\n  Ground Truth - Relevantné dokumenty:")
        rel_count = 0
        for doc_id, detail in details.get(query_id, {}).items():
            if detail['relevant']:
                rel_count += 1
                print(f"    ✓ {detail['title'][:70]}")
                if rel_count >= 8:
                    remaining = qm['total_relevant_in_pool'] - 8
                    if remaining > 0:
                        print(f"    ... a ďalších {remaining}")
                    break
        
        print(f"\n  {'System':<15} {'P@5':<10} {'R@5':<10} {'Rel/5':<8} Top 5 dokumenty")
        print("  " + "-"*85)
        
        for system in systems:
            sm = qm['systems'].get(system, {})
            p = sm.get('precision_at_k', 0)
            r = sm.get('recall_at_k', 0)
            rel = sm.get('relevant_in_top_k', 0)
            
            # Top 5 docs s označením relevancie
            top5_str = []
            for d in sm.get('top_k_docs', [])[:5]:
                mark = "✓" if d['relevant'] else "✗"
                top5_str.append(f"{mark}{d['title'][:15]}")
            
            print(f"  {short_names[system]:<15} {p:.0%}       {r:.0%}       {rel}/5     {', '.join(top5_str[:3])}")
    
    # Celkový súhrn
    print(f"\n{'='*100}")
    print("CELKOVÝ SÚHRN - MEAN PRECISION@5 a MEAN RECALL@5")
    print(f"{'='*100}")
    
    avg_p = {s: [] for s in systems}
    avg_r = {s: [] for s in systems}
    
    for query_id in query_ids:
        if query_id not in metrics:
            continue
        for system in systems:
            sm = metrics[query_id]['systems'].get(system, {})
            avg_p[system].append(sm.get('precision_at_k', 0))
            avg_r[system].append(sm.get('recall_at_k', 0))
    
    print(f"\n{'System':<25} {'Mean P@5':<15} {'Mean R@5':<15} {'F1-Score':<15}")
    print("-"*70)
    
    results_summary = []
    for system in systems:
        mean_p = sum(avg_p[system]) / len(avg_p[system]) if avg_p[system] else 0
        mean_r = sum(avg_r[system]) / len(avg_r[system]) if avg_r[system] else 0
        f1 = 2 * mean_p * mean_r / (mean_p + mean_r) if (mean_p + mean_r) > 0 else 0
        results_summary.append((short_names[system], mean_p, mean_r, f1))
        print(f"{short_names[system]:<25} {mean_p:.1%}          {mean_r:.1%}          {f1:.1%}")
    
    # Markdown tabuľka
    print(f"\n{'='*100}")
    print("MARKDOWN TABUĽKA PRE DOKUMENT")
    print(f"{'='*100}")
    
    print("\n### Ground Truth Evaluation - Precision@5 a Recall@5\n")
    print("| # | Query | Pool | S1 P@5 | S1 R@5 | S2 P@5 | S2 R@5 | L1 P@5 | L1 R@5 | L2 P@5 | L2 R@5 |")
    print("|---|-------|------|--------|--------|--------|--------|--------|--------|--------|--------|")
    
    for idx, query_id in enumerate(query_ids, 1):
        if query_id not in metrics:
            continue
        qm = metrics[query_id]
        row = [str(idx), f"`{qm['query'][:22]}`", str(qm['total_relevant_in_pool'])]
        for system in systems:
            sm = qm['systems'].get(system, {})
            row.append(f"{sm.get('precision_at_k', 0):.0%}")
            row.append(f"{sm.get('recall_at_k', 0):.0%}")
        print("| " + " | ".join(row) + " |")
    
    # Priemery
    print("|---|-------|------|--------|--------|--------|--------|--------|--------|--------|--------|")
    row = ["", "**PRIEMER**", ""]
    for system in systems:
        mean_p = sum(avg_p[system]) / len(avg_p[system]) if avg_p[system] else 0
        mean_r = sum(avg_r[system]) / len(avg_r[system]) if avg_r[system] else 0
        row.append(f"**{mean_p:.0%}**")
        row.append(f"**{mean_r:.0%}**")
    print("| " + " | ".join(row) + " |")
    
    return results_summary


def main():
    base_dir = Path(__file__).parent.parent
    results_file = base_dir / "eval" / "benchmark_results" / "specific_queries_results.json"
    
    print("Loading results...")
    results = load_results(results_file)
    
    query_ids = list(SELECTED_QUERIES.keys())
    
    print(f"\nVybrané queries ({len(query_ids)}):")
    for qid in query_ids:
        print(f"  ID {qid}: {SELECTED_QUERIES[qid]}")
    
    print("\nCreating pooled documents...")
    pools = create_pooled_documents(results, query_ids, top_k=10)
    
    print("\nPool sizes:")
    for qid in query_ids:
        print(f"  Query {qid} ({SELECTED_QUERIES[qid][:25]}): {len(pools.get(qid, {}))} docs")
    
    print("\nAnnotating relevance...")
    annotations, details = annotate_relevance(pools)
    
    print("\nCalculating metrics (K=5)...")
    metrics = calculate_metrics(results, annotations, query_ids, top_k=5)
    
    results_summary = print_detailed_report(metrics, details, query_ids)
    
    # Export
    export_dir = base_dir / "eval" / "ground_truth"
    export_dir.mkdir(exist_ok=True)
    
    export_data = {
        'queries': SELECTED_QUERIES,
        'criteria': {k: [str(p) for p in v] for k, v in SEMANTIC_CRITERIA.items()},
        'annotations': {str(k): v for k, v in details.items()},
        'metrics': {str(k): v for k, v in metrics.items()},
        'summary': {
            s[0]: {'mean_precision': s[1], 'mean_recall': s[2], 'f1': s[3]}
            for s in results_summary
        }
    }
    
    with open(export_dir / "ground_truth_final.json", 'w') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n\nExported to {export_dir}/ground_truth_final.json")


if __name__ == "__main__":
    main()
