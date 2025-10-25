#!/usr/bin/env python3
"""
Output formatters for recipe search results.
"""

import re
from typing import Dict, List, Any


def clean_wiki_abstract(abstract: str, max_len: int = 150) -> str:
    """Clean Wikipedia abstract text."""
    if not abstract:
        return 'N/A'
    
    # Remove artifacts
    clean = abstract.replace('(, ; )', '').replace('()', '')
    clean = re.sub(r'\|[a-z\-]+=', ' ', clean)
    clean = ' '.join(clean.split()).strip()
    
    # Truncate if needed
    if len(clean) > max_len:
        return clean[:max_len] + '...'
    return clean


def print_result_dict(result: Dict[str, Any], rank: int):
    """Print a result in dictionary format (Lucene/Lupyne)."""
    doc_id = result.get('docId', result.get('doc_id', 'N/A'))
    score = result.get('score', 0.0)
    title = result.get('title', result.get('title_text', 'No title'))
    url = result.get('url', 'N/A')
    total_minutes = result.get('total_minutes')
    
    print(f"\n{'='*80}")
    print(f"RESULT #{rank}: {title}")
    print(f"{'='*80}")
    print(f"SCORE: {score:.4f}")
    print(f"DOC_ID: {doc_id}")
    print(f"URL: {url}")
    print()
    
    # Extract fields
    desc = result.get('description', '')
    ings = result.get('ingredients', '')
    instr = result.get('instructions', '')
    prep_minutes = result.get('prep_minutes', '')
    cook_minutes = result.get('cook_minutes', '')
    cuisine = result.get('cuisine', '')
    category = result.get('category', '')
    tools = result.get('tools', '')
    yield_info = result.get('yield', '')
    author = result.get('author', '')
    difficulty = result.get('difficulty', '')
    serving_size = result.get('serving_size', '')
    nutrition = result.get('nutrition', '')
    ratings = result.get('ratings', '')
    date_published = result.get('date_published', '')
    
    # food.com section
    print(f"📖 FROM food.com:")
    print(f"   DESCRIPTION: {desc if desc else 'N/A'}")
    print(f"   TOTAL_TIME: {total_minutes} min" if total_minutes else "   TOTAL_TIME: N/A")
    print(f"   PREP_TIME: {prep_minutes} min" if prep_minutes else "   PREP_TIME: N/A")
    print(f"   COOK_TIME: {cook_minutes} min" if cook_minutes else "   COOK_TIME: N/A")
    print(f"   CUISINE: {cuisine if cuisine else 'N/A'}")
    print(f"   CATEGORY: {category if category else 'N/A'}")
    print(f"   DIFFICULTY: {difficulty if difficulty else 'N/A'}")
    print(f"   YIELD: {yield_info if yield_info else 'N/A'}")
    print(f"   SERVING_SIZE: {serving_size if serving_size else 'N/A'}")
    print(f"   AUTHOR: {author if author else 'N/A'}")
    print(f"   DATE_PUBLISHED: {date_published if date_published else 'N/A'}")
    print(f"   RATINGS: {ratings if ratings else 'N/A'}")
    print(f"   NUTRITION: {nutrition if nutrition else 'N/A'}")
    print(f"   TOOLS: {tools if tools else 'N/A'}")
    print(f"   INGREDIENTS:")
    if ings:
        print(f"      {ings}")
    else:
        print(f"      N/A")
    print(f"   INSTRUCTIONS:")
    if instr:
        print(f"      {instr}")
    else:
        print(f"      N/A")
    
    # Wikipedia section
    wiki_links = result.get('wiki_links', [])
    if wiki_links:
        print()
        print(f"📚 FROM WIKIPEDIA ({len(wiki_links)} entities):")
        print(f"   {'─'*76}")
        
        # Group by type
        by_type = {}
        for link in wiki_links:
            entity_type = link.get('type', 'unknown')
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(link)
        
        # Display each type
        for entity_type, links in sorted(by_type.items()):
            print(f"\n   {entity_type.upper()}S:")
            for link in links[:5]:  # Max 5 per type
                wiki_title = link.get('wiki_title', 'N/A')
                surface = link.get('surface', 'N/A')
                abstract = link.get('abstract', '')
                categories = link.get('categories', [])
                
                abstract_short = clean_wiki_abstract(abstract)
                
                print(f"      • {wiki_title} (matched: '{surface}')")
                print(f"        {abstract_short}")
                if categories:
                    print(f"        Categories: {', '.join(categories[:3])}")
    
    print()


def print_result_tuple(result: tuple, rank: int):
    """Print a result in tuple format (TSV)."""
    doc_id, score, snippet = result
    
    print(f"\n{'='*80}")
    print(f"RESULT #{rank}")
    print(f"{'='*80}")
    print(f"SCORE: {score:.4f}")
    print(f"DOC_ID: {doc_id}")
    print(f"SNIPPET: {snippet}")
    print()


def print_quiet(result: Any):
    """Print result in quiet mode (doc_id + score only)."""
    if isinstance(result, dict):
        doc_id = result.get('docId', result.get('doc_id', 'N/A'))
        score = result.get('score', 0.0)
    else:
        # TSV tuple format
        doc_id, score, _ = result
    
    print(f"{doc_id}\t{score:.4f}")
