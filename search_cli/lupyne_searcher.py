#!/usr/bin/env python3
"""
Lupyne-based recipe searcher (Pythonic PyLucene wrapper).

Supports:
- BM25 and TF-IDF similarity
- Fuzzy search (typo tolerance)
- Phrase/exact match search ("chocolate cake")
- Ingredient-based search
- Cuisine filtering
- Origin country/region filtering
- Time range filtering
- Boolean queries (AND, OR, NOT)
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# Lupyne imports
try:
    import lucene
    from lupyne import engine
    from org.apache.lucene.queryparser.classic import QueryParser
    from org.apache.lucene.index import Term
    from org.apache.lucene.search import (
        TermQuery, BooleanQuery, BooleanClause, FuzzyQuery,
        PhraseQuery, WildcardQuery, BoostQuery
    )
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
        # Prioritize the standard output filename
        possible_files = [
            Path('data/normalized/recipes_enriched.jsonl'),
            Path('data/normalized/recipes_enriched_v2.jsonl')
        ]
        
        recipes_file = None
        for p in possible_files:
            if p.exists():
                recipes_file = p
                break
        
        if not recipes_file:
            logger.warning(f"Enriched recipes not found in: {[str(p) for p in possible_files]}")
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
        
        logger.info(f"Loaded {len(self.recipes_by_id)} recipes from {recipes_file}")
    
    def search_bm25(self, query: str, k: int = 10, filters: Optional[Dict[str, Any]] = None, 
                    fuzzy: bool = False, fuzzy_distance: int = 2) -> List[Dict[str, Any]]:
        """Search using BM25.
        
        Args:
            query: Search query string
            k: Number of results to return
            filters: Optional filters dict
            fuzzy: Enable fuzzy matching for typo tolerance
            fuzzy_distance: Max edit distance for fuzzy matching (1 or 2)
        """
        from org.apache.lucene.search.similarities import BM25Similarity
        self.searcher.setSimilarity(BM25Similarity())
        return self._search(query, k, filters, fuzzy=fuzzy, fuzzy_distance=fuzzy_distance)
    
    def search_tfidf(self, query: str, k: int = 10, filters: Optional[Dict[str, Any]] = None,
                     fuzzy: bool = False, fuzzy_distance: int = 2) -> List[Dict[str, Any]]:
        """Search using TF-IDF.
        
        Args:
            query: Search query string
            k: Number of results to return
            filters: Optional filters dict
            fuzzy: Enable fuzzy matching for typo tolerance
            fuzzy_distance: Max edit distance for fuzzy matching (1 or 2)
        """
        from org.apache.lucene.search.similarities import ClassicSimilarity
        self.searcher.setSimilarity(ClassicSimilarity())
        return self._search(query, k, filters, fuzzy=fuzzy, fuzzy_distance=fuzzy_distance)
    
    def search_fuzzy(self, query: str, k: int = 10, filters: Optional[Dict[str, Any]] = None,
                     max_edits: int = 2) -> List[Dict[str, Any]]:
        """Fuzzy search with typo tolerance.
        
        Examples:
            - "chickn" -> finds "chicken"
            - "spagetti" -> finds "spaghetti"
            - "tomatoe" -> finds "tomato"
        
        Args:
            query: Search query (can contain typos)
            k: Number of results
            filters: Optional filters
            max_edits: Maximum edit distance (1 or 2, Lucene limit)
        """
        from org.apache.lucene.search.similarities import BM25Similarity
        self.searcher.setSimilarity(BM25Similarity())
        return self._search(query, k, filters, fuzzy=True, fuzzy_distance=min(max_edits, 2))
    
    def search_keyword(self, field: str, value: str, k: int = 10) -> List[Dict[str, Any]]:
        """Exact keyword search on a specific field.
        
        Args:
            field: Field to search (e.g., 'cuisine_kw', 'ingredients_kw')
            value: Exact value to match
            k: Number of results
        """
        term = Term(field, value.lower().strip())
        query = TermQuery(term)
        
        hits = self.searcher.search(query, count=k)
        return self._format_results(hits)
    
    def search_combined(self, query_text: str, keyword_filters: Dict[str, str] = None,
                        k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Combined full-text + keyword search.
        
        Example:
            search_combined("quick dinner", keyword_filters={"cuisine_kw": "mexican"})
        
        Args:
            query_text: Full-text search query
            keyword_filters: Dict of field -> exact value for keyword matching
            k: Number of results
            filters: Additional range/boolean filters
        """
        from org.apache.lucene.search.similarities import BM25Similarity
        self.searcher.setSimilarity(BM25Similarity())
        
        # Build base text query
        escaped_query = QueryParser.escape(query_text)
        query_parts = []
        for term in escaped_query.split():
            query_parts.append(f"title_text:{term}^2.0")
            query_parts.append(f"ingredients_text:{term}^1.5")
            query_parts.append(f"instructions_text:{term}^1.0")
        
        query_str = " OR ".join(query_parts)
        base_query = self.searcher.parse(query_str)
        
        # Build combined query
        builder = BooleanQuery.Builder()
        builder.add(base_query, BooleanClause.Occur.MUST)
        
        # Add keyword filters
        if keyword_filters:
            for field, value in keyword_filters.items():
                term = Term(field, value.lower().strip())
                builder.add(TermQuery(term), BooleanClause.Occur.MUST)
        
        # Add range filters
        if filters and 'max_total_minutes' in filters:
            max_min = int(filters['max_total_minutes'])
            time_query = LongPoint.newRangeQuery("total_minutes", 0, max_min)
            builder.add(time_query, BooleanClause.Occur.MUST)
        
        final_query = builder.build()
        hits = self.searcher.search(final_query, count=k)
        return self._format_results(hits)

    # =========================================================================
    # ADVANCED SEARCH METHODS
    # =========================================================================

    def search_phrase(self, phrase: str, k: int = 10, field: str = "title_text",
                      slop: int = 0) -> List[Dict[str, Any]]:
        """Exact phrase search using PhraseQuery.
        
        Searches for exact phrase match. Use quotes in query for phrase search.
        
        Examples:
            - search_phrase("chocolate cake") -> finds "chocolate cake" as exact phrase
            - search_phrase("chicken parmesan", slop=1) -> allows 1 word between terms
        
        Args:
            phrase: Exact phrase to search for
            k: Number of results
            field: Field to search in (default: title_text)
            slop: Maximum number of positions between terms (0 = exact adjacent)
        
        Returns:
            List of matching recipes
        """
        from org.apache.lucene.search.similarities import BM25Similarity
        self.searcher.setSimilarity(BM25Similarity())
        
        # Clean phrase
        phrase = phrase.strip().strip('"').strip("'").lower()
        terms = phrase.split()
        
        if not terms:
            return []
        
        if len(terms) == 1:
            # Single term - use regular term query
            term = Term(field, terms[0])
            query = TermQuery(term)
        else:
            # Multiple terms - build phrase query
            builder = PhraseQuery.Builder()
            builder.setSlop(slop)
            for i, word in enumerate(terms):
                builder.add(Term(field, word), i)
            query = builder.build()
        
        hits = self.searcher.search(query, count=k)
        return self._format_results(hits)

    def search_exact_match(self, query_text: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search with exact phrase matching for quoted terms.
        
        Parses query for quoted phrases and regular terms:
        - "chocolate cake" -> exact phrase match
        - chicken -> regular term match
        - "italian pasta" chicken -> phrase AND term
        
        Examples:
            - '"chocolate cake"' -> exact phrase in any field
            - '"grilled chicken" salad' -> phrase + term
            - '"quick dinner" -dessert' -> phrase, exclude dessert
        
        Args:
            query_text: Query with optional quoted phrases
            k: Number of results
        
        Returns:
            List of matching recipes
        """
        from org.apache.lucene.search.similarities import BM25Similarity
        self.searcher.setSimilarity(BM25Similarity())
        
        # Parse quoted phrases and regular terms
        phrases, regular_terms, exclude_terms = self._parse_advanced_query(query_text)
        
        builder = BooleanQuery.Builder()
        fields = [
            ('title_text', 2.0),
            ('ingredients_text', 1.5),
            ('instructions_text', 1.0),
            ('wiki_abstracts', 1.0)
        ]
        
        # Add phrase queries (exact match)
        for phrase in phrases:
            phrase_builder = BooleanQuery.Builder()
            for field_name, boost in fields:
                phrase_terms = phrase.lower().split()
                if len(phrase_terms) == 1:
                    term_q = TermQuery(Term(field_name, phrase_terms[0]))
                else:
                    pq_builder = PhraseQuery.Builder()
                    for i, word in enumerate(phrase_terms):
                        pq_builder.add(Term(field_name, word), i)
                    term_q = BoostQuery(pq_builder.build(), boost)
                phrase_builder.add(term_q, BooleanClause.Occur.SHOULD)
            builder.add(phrase_builder.build(), BooleanClause.Occur.MUST)
        
        # Add regular term queries
        for term_str in regular_terms:
            term_builder = BooleanQuery.Builder()
            for field_name, boost in fields:
                term_q = TermQuery(Term(field_name, term_str.lower()))
                boosted_q = BoostQuery(term_q, boost)
                term_builder.add(boosted_q, BooleanClause.Occur.SHOULD)
            builder.add(term_builder.build(), BooleanClause.Occur.MUST)
        
        # Add exclusion terms (NOT)
        for term_str in exclude_terms:
            for field_name, _ in fields:
                term_q = TermQuery(Term(field_name, term_str.lower()))
                builder.add(term_q, BooleanClause.Occur.MUST_NOT)
        
        # Handle empty query
        if not phrases and not regular_terms:
            return []
        
        query = builder.build()
        hits = self.searcher.search(query, count=k)
        return self._format_results(hits)

    def search_by_ingredients(self, include: List[str] = None, exclude: List[str] = None,
                               match_all: bool = True, k: int = 10) -> List[Dict[str, Any]]:
        """Search recipes by ingredients.
        
        Find recipes that include or exclude specific ingredients.
        
        Examples:
            - search_by_ingredients(include=["chicken", "garlic"])
            - search_by_ingredients(include=["pasta"], exclude=["meat"])
            - search_by_ingredients(include=["egg", "flour", "sugar"], match_all=False)
        
        Args:
            include: List of ingredients that must be present
            exclude: List of ingredients that must NOT be present
            match_all: If True, all included ingredients must match (AND)
                       If False, any included ingredient can match (OR)
            k: Number of results
        
        Returns:
            List of matching recipes
        """
        from org.apache.lucene.search.similarities import BM25Similarity
        self.searcher.setSimilarity(BM25Similarity())
        
        builder = BooleanQuery.Builder()
        
        # Add included ingredients
        if include:
            if match_all:
                # AND - all ingredients must be present
                for ing in include:
                    ing_lower = ing.lower().strip()
                    if ing_lower:
                        # Search in both text and keyword fields
                        ing_builder = BooleanQuery.Builder()
                        ing_builder.add(TermQuery(Term("ingredients_text", ing_lower)), 
                                       BooleanClause.Occur.SHOULD)
                        ing_builder.add(TermQuery(Term("ingredients_kw", ing_lower)), 
                                       BooleanClause.Occur.SHOULD)
                        builder.add(ing_builder.build(), BooleanClause.Occur.MUST)
            else:
                # OR - any ingredient can match
                ing_builder = BooleanQuery.Builder()
                for ing in include:
                    ing_lower = ing.lower().strip()
                    if ing_lower:
                        ing_builder.add(TermQuery(Term("ingredients_text", ing_lower)), 
                                       BooleanClause.Occur.SHOULD)
                        ing_builder.add(TermQuery(Term("ingredients_kw", ing_lower)), 
                                       BooleanClause.Occur.SHOULD)
                if include:
                    builder.add(ing_builder.build(), BooleanClause.Occur.MUST)
        
        # Add excluded ingredients
        if exclude:
            for ing in exclude:
                ing_lower = ing.lower().strip()
                if ing_lower:
                    builder.add(TermQuery(Term("ingredients_text", ing_lower)), 
                               BooleanClause.Occur.MUST_NOT)
                    builder.add(TermQuery(Term("ingredients_kw", ing_lower)), 
                               BooleanClause.Occur.MUST_NOT)
        
        # If no include specified, match all
        if not include:
            # Need at least one positive clause, use wildcard for ingredients field
            builder.add(WildcardQuery(Term("ingredients_text", "*")), BooleanClause.Occur.MUST)
        
        query = builder.build()
        hits = self.searcher.search(query, count=k)
        return self._format_results(hits)

    def search_by_cuisine(self, cuisines: List[str], match_any: bool = True, 
                          k: int = 10) -> List[Dict[str, Any]]:
        """Search recipes by cuisine type.
        
        Examples:
            - search_by_cuisine(["Italian"]) -> Italian recipes
            - search_by_cuisine(["Mexican", "Spanish"], match_any=True) -> Mexican OR Spanish
            - search_by_cuisine(["Asian", "Vegetarian"], match_any=False) -> Asian AND Vegetarian
        
        Args:
            cuisines: List of cuisine types to search for
            match_any: If True, match any cuisine (OR). If False, match all (AND)
            k: Number of results
        
        Returns:
            List of matching recipes
        """
        from org.apache.lucene.search.similarities import BM25Similarity
        self.searcher.setSimilarity(BM25Similarity())
        
        if not cuisines:
            return []
        
        builder = BooleanQuery.Builder()
        
        if match_any:
            # OR - any cuisine matches
            for cuisine in cuisines:
                cuisine_lower = cuisine.lower().strip()
                if cuisine_lower:
                    builder.add(TermQuery(Term("cuisine_kw", cuisine_lower)), 
                               BooleanClause.Occur.SHOULD)
        else:
            # AND - all cuisines must match
            for cuisine in cuisines:
                cuisine_lower = cuisine.lower().strip()
                if cuisine_lower:
                    builder.add(TermQuery(Term("cuisine_kw", cuisine_lower)), 
                               BooleanClause.Occur.MUST)
        
        query = builder.build()
        hits = self.searcher.search(query, count=k)
        return self._format_results(hits)

    def search_by_origin(self, country: str = None, region: str = None,
                         k: int = 10) -> List[Dict[str, Any]]:
        """Search recipes by country or region of origin.
        
        Searches wiki_links origin_country and origin_region fields, 
        as well as ingredient_origins data.
        
        Examples:
            - search_by_origin(country="France") -> French origin recipes
            - search_by_origin(region="Caribbean") -> Caribbean recipes
            - search_by_origin(country="Italy", region="Mediterranean")
        
        Args:
            country: Country of origin to filter by
            region: Region of origin to filter by
            k: Number of results
        
        Returns:
            List of matching recipes
        """
        from org.apache.lucene.search.similarities import BM25Similarity
        self.searcher.setSimilarity(BM25Similarity())
        
        if not country and not region:
            return []
        
        builder = BooleanQuery.Builder()
        
        # Search in origin fields (if indexed)
        if country:
            country_lower = country.lower().strip()
            # Try both exact keyword field and text search
            country_builder = BooleanQuery.Builder()
            country_builder.add(TermQuery(Term("origin_country_kw", country_lower)), 
                               BooleanClause.Occur.SHOULD)
            # Also search in wiki_abstracts for country mentions
            country_builder.add(TermQuery(Term("wiki_abstracts", country_lower)), 
                               BooleanClause.Occur.SHOULD)
            builder.add(country_builder.build(), BooleanClause.Occur.MUST)
        
        if region:
            region_lower = region.lower().strip()
            region_builder = BooleanQuery.Builder()
            region_builder.add(TermQuery(Term("origin_region_kw", region_lower)), 
                              BooleanClause.Occur.SHOULD)
            region_builder.add(TermQuery(Term("wiki_abstracts", region_lower)), 
                              BooleanClause.Occur.SHOULD)
            builder.add(region_builder.build(), BooleanClause.Occur.MUST)
        
        query = builder.build()
        hits = self.searcher.search(query, count=k)
        return self._format_results(hits)

    def search_advanced(self, query_text: str = "", 
                        ingredients_include: List[str] = None,
                        ingredients_exclude: List[str] = None,
                        cuisines: List[str] = None,
                        origin_country: str = None,
                        origin_region: str = None,
                        max_time: int = None,
                        min_time: int = None,
                        difficulty: str = None,
                        fuzzy: bool = False,
                        k: int = 10) -> List[Dict[str, Any]]:
        """Advanced search with multiple filter criteria.
        
        Combines text search with various filters for powerful querying.
        
        Examples:
            - search_advanced("pasta", cuisines=["Italian"], max_time=30)
            - search_advanced(ingredients_include=["chicken", "garlic"], 
                            cuisines=["Asian"], difficulty="easy")
            - search_advanced("\"chocolate cake\"", max_time=60)
        
        Args:
            query_text: Text query (supports quoted phrases)
            ingredients_include: Required ingredients
            ingredients_exclude: Excluded ingredients
            cuisines: Cuisine types to filter by
            origin_country: Filter by country of origin
            origin_region: Filter by region of origin
            max_time: Maximum total time in minutes
            min_time: Minimum total time in minutes
            difficulty: Difficulty level (easy, medium, hard)
            fuzzy: Enable fuzzy matching for typo tolerance
            k: Number of results
        
        Returns:
            List of matching recipes
        """
        from org.apache.lucene.search.similarities import BM25Similarity
        self.searcher.setSimilarity(BM25Similarity())
        
        builder = BooleanQuery.Builder()
        has_query = False
        
        # Text query with phrase support
        if query_text and query_text.strip():
            phrases, regular_terms, exclude_terms = self._parse_advanced_query(query_text)
            
            fields = [
                ('title_text', 2.0),
                ('ingredients_text', 1.5),
                ('instructions_text', 1.0),
                ('wiki_abstracts', 1.0)
            ]
            
            # Phrase queries
            for phrase in phrases:
                phrase_builder = BooleanQuery.Builder()
                for field_name, boost in fields:
                    phrase_terms = phrase.lower().split()
                    if len(phrase_terms) == 1:
                        term_q = TermQuery(Term(field_name, phrase_terms[0]))
                    else:
                        pq_builder = PhraseQuery.Builder()
                        for i, word in enumerate(phrase_terms):
                            pq_builder.add(Term(field_name, word), i)
                        term_q = BoostQuery(pq_builder.build(), boost)
                    phrase_builder.add(term_q, BooleanClause.Occur.SHOULD)
                builder.add(phrase_builder.build(), BooleanClause.Occur.MUST)
                has_query = True
            
            # Regular terms
            for term_str in regular_terms:
                term_builder = BooleanQuery.Builder()
                for field_name, boost in fields:
                    if fuzzy and len(term_str) >= 3:
                        term_q = FuzzyQuery(Term(field_name, term_str.lower()), 2, 2)
                    else:
                        term_q = TermQuery(Term(field_name, term_str.lower()))
                    boosted_q = BoostQuery(term_q, boost)
                    term_builder.add(boosted_q, BooleanClause.Occur.SHOULD)
                builder.add(term_builder.build(), BooleanClause.Occur.MUST)
                has_query = True
            
            # Exclusion terms
            for term_str in exclude_terms:
                for field_name, _ in fields:
                    term_q = TermQuery(Term(field_name, term_str.lower()))
                    builder.add(term_q, BooleanClause.Occur.MUST_NOT)
        
        # Ingredient filters
        if ingredients_include:
            for ing in ingredients_include:
                ing_lower = ing.lower().strip()
                if ing_lower:
                    ing_builder = BooleanQuery.Builder()
                    ing_builder.add(TermQuery(Term("ingredients_text", ing_lower)), 
                                   BooleanClause.Occur.SHOULD)
                    ing_builder.add(TermQuery(Term("ingredients_kw", ing_lower)), 
                                   BooleanClause.Occur.SHOULD)
                    builder.add(ing_builder.build(), BooleanClause.Occur.MUST)
                    has_query = True
        
        if ingredients_exclude:
            for ing in ingredients_exclude:
                ing_lower = ing.lower().strip()
                if ing_lower:
                    builder.add(TermQuery(Term("ingredients_text", ing_lower)), 
                               BooleanClause.Occur.MUST_NOT)
        
        # Cuisine filter
        if cuisines:
            cuisine_builder = BooleanQuery.Builder()
            for cuisine in cuisines:
                cuisine_lower = cuisine.lower().strip()
                if cuisine_lower:
                    cuisine_builder.add(TermQuery(Term("cuisine_kw", cuisine_lower)), 
                                       BooleanClause.Occur.SHOULD)
            builder.add(cuisine_builder.build(), BooleanClause.Occur.MUST)
            has_query = True
        
        # Origin filters
        if origin_country:
            country_builder = BooleanQuery.Builder()
            country_lower = origin_country.lower().strip()
            country_builder.add(TermQuery(Term("origin_country_kw", country_lower)), 
                               BooleanClause.Occur.SHOULD)
            country_builder.add(TermQuery(Term("wiki_abstracts", country_lower)), 
                               BooleanClause.Occur.SHOULD)
            builder.add(country_builder.build(), BooleanClause.Occur.MUST)
            has_query = True
        
        if origin_region:
            region_builder = BooleanQuery.Builder()
            region_lower = origin_region.lower().strip()
            region_builder.add(TermQuery(Term("origin_region_kw", region_lower)), 
                              BooleanClause.Occur.SHOULD)
            region_builder.add(TermQuery(Term("wiki_abstracts", region_lower)), 
                              BooleanClause.Occur.SHOULD)
            builder.add(region_builder.build(), BooleanClause.Occur.MUST)
            has_query = True
        
        # Time filters
        if max_time is not None:
            min_val = min_time if min_time is not None else 0
            time_query = LongPoint.newRangeQuery("total_minutes", min_val, max_time)
            builder.add(time_query, BooleanClause.Occur.MUST)
        elif min_time is not None:
            time_query = LongPoint.newRangeQuery("total_minutes", min_time, 10000)
            builder.add(time_query, BooleanClause.Occur.MUST)
        
        # Difficulty filter
        if difficulty:
            difficulty_lower = difficulty.lower().strip()
            builder.add(TermQuery(Term("difficulty", difficulty_lower)), 
                       BooleanClause.Occur.MUST)
            has_query = True
        
        # If no query specified, match all
        if not has_query:
            builder.add(WildcardQuery(Term("title_text", "*")), BooleanClause.Occur.MUST)
        
        query = builder.build()
        hits = self.searcher.search(query, count=k)
        return self._format_results(hits)

    def _parse_advanced_query(self, query_text: str) -> Tuple[List[str], List[str], List[str]]:
        """Parse query for phrases, regular terms, and exclusions.
        
        Args:
            query_text: Raw query text
        
        Returns:
            Tuple of (phrases, regular_terms, exclude_terms)
        """
        phrases = []
        regular_terms = []
        exclude_terms = []
        
        # Extract quoted phrases
        phrase_pattern = r'"([^"]+)"'
        for match in re.finditer(phrase_pattern, query_text):
            phrases.append(match.group(1).strip())
        
        # Remove phrases from query
        remaining = re.sub(phrase_pattern, '', query_text)
        
        # Parse remaining terms
        for term in remaining.split():
            term = term.strip()
            if not term:
                continue
            if term.startswith('-') or term.startswith('NOT '):
                # Exclusion term
                clean_term = term.lstrip('-').replace('NOT ', '')
                if clean_term:
                    exclude_terms.append(clean_term)
            elif term.upper() in ('AND', 'OR', 'NOT'):
                # Skip boolean operators
                continue
            else:
                regular_terms.append(term)
        
        return phrases, regular_terms, exclude_terms

    def _search(self, query_text: str, k: int, filters: Optional[Dict[str, Any]],
                fuzzy: bool = False, fuzzy_distance: int = 2) -> List[Dict[str, Any]]:
        """Perform search.
        
        Args:
            query_text: Search query
            k: Number of results
            filters: Optional filters
            fuzzy: Enable fuzzy matching
            fuzzy_distance: Max edit distance (1 or 2)
        """
        # Escape query
        escaped_query = QueryParser.escape(query_text)
        
        # Build query based on fuzzy flag
        if fuzzy:
            # Build fuzzy query using FuzzyQuery for each term
            builder = BooleanQuery.Builder()
            fields = [
                ('title_text', 2.0),
                ('ingredients_text', 1.5),
                ('instructions_text', 1.0),
                ('wiki_abstracts', 1.0)
            ]
            
            for term_str in escaped_query.split():
                term_str = term_str.lower().strip()
                if len(term_str) < 3:
                    continue  # Skip very short terms for fuzzy
                
                # Create fuzzy query for each field
                term_builder = BooleanQuery.Builder()
                for field_name, boost in fields:
                    term = Term(field_name, term_str)
                    # FuzzyQuery with maxEdits (1 or 2), prefixLength=2
                    fuzzy_q = FuzzyQuery(term, min(fuzzy_distance, 2), 2)
                    term_builder.add(fuzzy_q, BooleanClause.Occur.SHOULD)
                
                builder.add(term_builder.build(), BooleanClause.Occur.SHOULD)
            
            base_query = builder.build()
        else:
            # Standard query parsing with boosts
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
    
    def _format_results(self, hits) -> List[Dict[str, Any]]:
        """Format search hits into result dicts."""
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
                'ingredients': hit.get('ingredients_text', ''),
                'total_minutes': int(hit.get('total_minutes', 0)) if hit.get('total_minutes') else None,
                'cuisine': hit.get('cuisine', ''),
            }
            
            # Add wiki_links if available
            if doc_id and doc_id in self.recipes_by_id:
                original_recipe = self.recipes_by_id[doc_id]
                res['wiki_links'] = original_recipe.get('wiki_links', [])
            else:
                res['wiki_links'] = []
            
            results.append(res)
        
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
