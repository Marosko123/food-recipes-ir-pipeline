#!/usr/bin/env python3
"""
Lupyne-based recipe searcher (Pythonic PyLucene wrapper).
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Lupyne imports
try:
    import lucene
    from lupyne import engine
    from org.apache.lucene.queryparser.classic import QueryParser
    from org.apache.lucene.index import Term
    from org.apache.lucene.search import TermQuery, BooleanQuery, BooleanClause
    from org.apache.lucene.document import LongPoint
    LUPYNE_AVAILABLE = True
except ImportError:
    LUPYNE_AVAILABLE = False
    logger.warning("Lupyne not available")


class LupyneRecipeSearcher:
    """Lupyne-based searcher for recipe index."""
    
    def __init__(self, index_dir: str):
        """Initialize Lupyne searcher."""
        if not LUPYNE_AVAILABLE:
            raise ImportError("Lupyne not available.")
        
        self.index_dir = Path(index_dir)
        
        if not self.index_dir.exists():
            raise FileNotFoundError(f"Index not found: {self.index_dir}")
        
        # Init JVM
        if not lucene.getVMEnv():
            lucene.initVM(vmargs=['-Djava.awt.headless=true'])
        
        # Open index
        self.searcher = engine.IndexSearcher(str(self.index_dir.absolute()))
        
        # Load recipes for wiki_links
        self.recipes_by_id = {}
        self._load_recipes()
        
        logger.info(f"Opened Lupyne index: {self.index_dir} ({self.searcher.count} docs)")
    
    def _load_recipes(self):
        """Load enriched recipes."""
        recipes_file = Path('data/normalized/recipes_enriched.jsonl')
        if not recipes_file.exists():
            logger.warning(f"Enriched recipes not found: {recipes_file}")
            return
        
        with open(recipes_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    recipe = json.loads(line.strip())
                    recipe_id = recipe.get('id', '')
                    if recipe_id:
                        self.recipes_by_id[recipe_id] = recipe
                except json.JSONDecodeError:
                    continue
        
        logger.info(f"Loaded {len(self.recipes_by_id)} recipes")
    
    def search_bm25(self, query: str, k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search using BM25."""
        return self._search(query, k, filters)
    
    def search_tfidf(self, query: str, k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search using TF-IDF."""
        return self._search(query, k, filters)
    
    def _search(self, query_text: str, k: int, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform search."""
        # Escape query
        escaped_query = QueryParser.escape(query_text)
        
        # Build multi-field query with boosts
        query_parts = []
        for term in escaped_query.split():
            query_parts.append(f"title_text:{term}^2.0")
            query_parts.append(f"ingredients_text:{term}^1.5")
            query_parts.append(f"instructions_text:{term}^1.0")
            query_parts.append(f"wiki_abstracts:{term}^1.0")
        
        query_str = " OR ".join(query_parts)
        base_query = self.searcher.parse(query_str)
        
        # Apply filters
        if filters:
            # TODO: Cache parsed queries for better performance
            # FIXME: Filter validation is weak, needs proper schema
            filter_queries = []
            
            # Ingredient filters
            if 'include_ingredients' in filters:
                ings = filters['include_ingredients']
                if isinstance(ings, str):
                    ings = [ing.strip() for ing in ings.split(',')]
                
                for ing in ings:
                    ing_lower = ing.lower().strip()
                    if ing_lower:
                        ing_query = self.searcher.parse(ing_lower, field='ingredients_text')
                        filter_queries.append(ing_query)
            
            # Cuisine filters
            if 'cuisine' in filters:
                cuisines = filters['cuisine']
                if isinstance(cuisines, str):
                    cuisines = [c.strip() for c in cuisines.split(',')]
                
                if cuisines:
                    cuisine_queries = []
                    for c in cuisines:
                        if c.strip():
                            term = Term("cuisine_kw", c.strip())
                            cuisine_queries.append(TermQuery(term))
                    
                    if cuisine_queries:
                        cuisine_builder = BooleanQuery.Builder()
                        for cq in cuisine_queries:
                            cuisine_builder.add(cq, BooleanClause.Occur.SHOULD)
                        filter_queries.append(cuisine_builder.build())
            
            # Time filters
            if 'max_total_minutes' in filters:
                max_min = int(filters['max_total_minutes'])
                time_query = LongPoint.newRangeQuery("total_minutes", 0, max_min)
                filter_queries.append(time_query)
            
            if 'min_total_minutes' in filters:
                min_min = int(filters['min_total_minutes'])
                max_min = int(filters.get('max_total_minutes', 10000))
                time_query = LongPoint.newRangeQuery("total_minutes", min_min, max_min)
                filter_queries.append(time_query)
            
            # Combine query + filters
            if filter_queries:
                builder = BooleanQuery.Builder()
                builder.add(base_query, BooleanClause.Occur.MUST)
                for fq in filter_queries:
                    builder.add(fq, BooleanClause.Occur.MUST)
                final_query = builder.build()
            else:
                final_query = base_query
        else:
            final_query = base_query
        
        # Search
        hits = self.searcher.search(final_query, count=k)
        
        # Format results
        results = []
        for i, hit in enumerate(hits):
            doc_id = hit.get('docId', '')
            
            res = {
                'rank': i + 1,
                'score': float(hit.score),
                'docId': doc_id,
                'url': hit.get('url', ''),
                'title': hit.get('title_text', ''),
                'title_text': hit.get('title_text', ''),
                'description': hit.get('description', ''),
                'ingredients': hit.get('ingredients_text', ''),
                'ingredients_text': hit.get('ingredients_text', ''),
                'instructions': hit.get('instructions_text', ''),
                'instructions_text': hit.get('instructions_text', ''),
                'wiki_abstracts': hit.get('wiki_abstracts', ''),
                'total_minutes': int(hit.get('total_minutes', 0)) if hit.get('total_minutes') else None,
                'prep_minutes': hit.get('prep_minutes', ''),
                'cook_minutes': hit.get('cook_minutes', ''),
                'cuisine': hit.get('cuisine', ''),
                'category': hit.get('category', ''),
                'tools': hit.get('tools', ''),
                'yield': hit.get('yield', ''),
                'author': hit.get('author', ''),
                'difficulty': hit.get('difficulty', ''),
                'serving_size': hit.get('serving_size', ''),
                'nutrition': hit.get('nutrition', ''),
                'ratings': hit.get('ratings', ''),
                'date_published': hit.get('date_published', ''),
            }
            
            # Add wiki_links
            if doc_id and doc_id in self.recipes_by_id:
                original_recipe = self.recipes_by_id[doc_id]
                res['wiki_links'] = original_recipe.get('wiki_links', [])
            else:
                res['wiki_links'] = []
            
            results.append(res)
        
        logger.info(f"Found {len(results)} results")
        return results
    
    def close(self):
        """Close searcher."""
        if hasattr(self, 'searcher') and self.searcher is not None:
            try:
                import sys
                import os
                old_stderr = sys.stderr
                sys.stderr = open(os.devnull, 'w')
                
                try:
                    if hasattr(self.searcher, 'indexReader'):
                        self.searcher.indexReader.close()
                finally:
                    sys.stderr = old_stderr
                    
                self.searcher = None
            except Exception:
                pass
