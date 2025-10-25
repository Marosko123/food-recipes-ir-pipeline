#!/usr/bin/env python3
"""
Unified Search CLI - Supports both TSV and Lupyne (Pythonic PyLucene) indexes
Implements TF-IDF and BM25 search with comprehensive error handling and validation.
"""

import argparse
import json
import logging
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Try to import Lupyne (optional, Pythonic PyLucene wrapper)
try:
    import lucene
    from lupyne import engine
    from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity
    from org.apache.lucene.document import IntPoint
    LUPYNE_AVAILABLE = True
except ImportError:
    LUPYNE_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LupyneRecipeSearcher:
    """Lupyne-based searcher for recipe index (Pythonic PyLucene wrapper)."""
    
    def __init__(self, index_dir: str):
        """Initialize Lupyne searcher."""
        if not LUPYNE_AVAILABLE:
            raise ImportError("Lupyne is not available. Install it or use TSV index.")
        
        self.index_dir = Path(index_dir)
        
        if not self.index_dir.exists():
            raise FileNotFoundError(f"Index directory not found: {self.index_dir}")
        
        # Initialize JVM if not already running
        if not lucene.getVMEnv():
            lucene.initVM(vmargs=['-Djava.awt.headless=true'])
        
        # Open Lupyne IndexSearcher (Pythonic API!)
        self.searcher = engine.IndexSearcher(str(self.index_dir.absolute()))
        
        # Lupyne IndexSearcher uses similarity from index (set during indexing)
        # To override, must access underlying IndexSearcher
        
        # Load enriched recipes for wiki_links lookup
        self.recipes_by_id = {}
        self._load_recipes()
        
        logger.info(f"Opened Lupyne index: {self.index_dir} ({self.searcher.count} docs)")
    
    def _load_recipes(self):
        """Load enriched recipes for wiki_links access."""
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
        
        logger.info(f"Loaded {len(self.recipes_by_id)} recipes for wiki_links lookup")
    
    def search_bm25(self, query: str, k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search using BM25 similarity (Lupyne Pythonic API)."""
        # BM25 is set at index time, just perform search
        return self._search(query, k, filters)
    
    def search_tfidf(self, query: str, k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search using TF-IDF (ClassicSimilarity, Lupyne Pythonic API)."""
        # TF-IDF must be set at index time
        # For now, we'll use whatever similarity was set during indexing
        return self._search(query, k, filters)
    
    def _search(self, query_text: str, k: int, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform search and return results using Lupyne's Pythonic API.
        
        Lupyne allows fluent query building:
        - searcher.parse('query text', field='field_name')
        - searcher.filter(...) for boolean queries
        - Pythonic dict-like document access
        """
        # Build multi-field query with boosts
        # Escape special characters in query text
        from org.apache.lucene.queryparser.classic import QueryParser
        escaped_query = QueryParser.escape(query_text)
        
        # Build query string with proper Lucene syntax (field:term OR field:term)
        query_parts = []
        for term in escaped_query.split():
            query_parts.append(f"title_text:{term}^2.0")
            query_parts.append(f"ingredients_text:{term}^1.5")
            query_parts.append(f"instructions_text:{term}^1.0")
            query_parts.append(f"wiki_abstracts:{term}^1.0")
        
        query_str = " OR ".join(query_parts)
        
        # Parse query (Lupyne handles multi-field automatically)
        base_query = self.searcher.parse(query_str)
        
        # Apply filters if provided
        if filters:
            # Build filter query using Lupyne's query builder
            filter_queries = []
            
            # Must-include ingredients (use full-text search in ingredients_text)
            if 'include_ingredients' in filters:
                ingredients = filters['include_ingredients']
                if isinstance(ingredients, str):
                    ingredients = [ing.strip() for ing in ingredients.split(',')]
                
                for ing in ingredients:
                    ing_lower = ing.lower().strip()
                    if ing_lower:
                        # Parse as term in ingredients_text field (will be analyzed)
                        ing_query = self.searcher.parse(ing_lower, field='ingredients_text')
                        filter_queries.append(ing_query)
            
            # Cuisine filter (OR)
            if 'cuisine' in filters:
                from org.apache.lucene.index import Term
                from org.apache.lucene.search import TermQuery, BooleanQuery, BooleanClause
                
                cuisines = filters['cuisine']
                if isinstance(cuisines, str):
                    cuisines = [c.strip() for c in cuisines.split(',')]
                
                if cuisines:
                    # Build OR query for cuisines
                    cuisine_queries = []
                    for c in cuisines:
                        if c.strip():
                            term = Term("cuisine_kw", c.strip())
                            cuisine_queries.append(TermQuery(term))
                    
                    if cuisine_queries:
                        # Combine with OR
                        cuisine_builder = BooleanQuery.Builder()
                        for cq in cuisine_queries:
                            cuisine_builder.add(cq, BooleanClause.Occur.SHOULD)
                        filter_queries.append(cuisine_builder.build())
            
            # Time range filter (use LongPoint, Lupyne dimensions=1 uses 8 bytes)
            # TODO: Cache parsed queries for better performance
            # FIXME: Filter validation is weak, needs proper schema
            if 'max_total_minutes' in filters:
                from org.apache.lucene.document import LongPoint
                max_minutes = int(filters['max_total_minutes'])
                time_query = LongPoint.newRangeQuery("total_minutes", 0, max_minutes)
                filter_queries.append(time_query)
            
            if 'min_total_minutes' in filters:
                from org.apache.lucene.document import LongPoint
                min_minutes = int(filters['min_total_minutes'])
                max_minutes = int(filters.get('max_total_minutes', 10000))
                time_query = LongPoint.newRangeQuery("total_minutes", min_minutes, max_minutes)
                filter_queries.append(time_query)
            
            # Combine base query with filters (all must match)
            if filter_queries:
                from org.apache.lucene.search import BooleanQuery, BooleanClause
                builder = BooleanQuery.Builder()
                builder.add(base_query, BooleanClause.Occur.MUST)
                for fq in filter_queries:
                    builder.add(fq, BooleanClause.Occur.MUST)
                final_query = builder.build()
            else:
                final_query = base_query
        else:
            final_query = base_query
        
        # Search (Lupyne returns Hit objects)
        hits = self.searcher.search(final_query, count=k)
        
        # Format results (Pythonic access!)
        results = []
        for i, hit in enumerate(hits):
            doc_id = hit.get('docId', '')
            
            result = {
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
            
            # Get wiki_links from original recipe
            if doc_id and doc_id in self.recipes_by_id:
                original_recipe = self.recipes_by_id[doc_id]
                result['wiki_links'] = original_recipe.get('wiki_links', [])
            else:
                result['wiki_links'] = []
            
            results.append(result)
        
        logger.info(f"Found {len(results)} results for query: '{query_text}'")
        return results
    
    def close(self):
        """Close the searcher and cleanup resources."""
        if hasattr(self, 'searcher') and self.searcher is not None:
            try:
                # Suppress stderr warnings during cleanup (Lupyne reference counting bug)
                import sys
                import os
                old_stderr = sys.stderr
                sys.stderr = open(os.devnull, 'w')
                
                try:
                    # Lupyne IndexSearcher cleanup
                    if hasattr(self.searcher, 'indexReader'):
                        self.searcher.indexReader.close()
                finally:
                    sys.stderr = old_stderr
                    
                self.searcher = None
            except Exception:
                # Ignore cleanup errors
                pass


class RobustRecipeSearcher:
    """Robust search engine with comprehensive error handling and validation."""
    
    @staticmethod
    def _safe_float(value, default=0.0):
        """Safely convert to float."""
        if value is None or value == '':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _safe_int(value, default=0):
        """Safely convert to int."""
        if value is None or value == '':
            return default
        try:
            return int(float(value))  # Convert through float to handle "123.0" strings
        except (ValueError, TypeError):
            return default
    
    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        
        # Validate index directory
        if not self.index_dir.exists():
            raise FileNotFoundError(f"Index directory not found: {self.index_dir}")
        
        # Index data structures
        self.terms = {}  # term -> (df, idf)
        self.postings = defaultdict(list)  # term -> [(field, doc_id, tf), ...]
        self.doc_metadata = {}  # doc_id -> {url, title, len_title, len_ing, len_instr}
        self.total_docs = 0
        
        # Performance optimization caches
        self._filter_cache = {}  # Cache for filter results
        self._recipe_cache = {}  # Cache for loaded recipes
        
        # Field weights for scoring
        self.field_weights = {
            'title': 3.0,
            'ingredients': 2.0,
            'instructions': 1.0
        }
        
        # BM25 parameters
        self.k1 = 1.2
        self.b = 0.75
        
        # Statistics
        self.stats = {
            'queries_processed': 0,
            'total_results': 0,
            'avg_results_per_query': 0.0
        }
        
        self._load_index()
    
    def _load_index(self):
        """Load index from TSV files with comprehensive error handling."""
        logger.info(f"Loading index from {self.index_dir}")
        
        try:
            # Load terms
            terms_file = self.index_dir / "terms.tsv"
            if not terms_file.exists():
                raise FileNotFoundError(f"Terms file not found: {terms_file}")
            
            with open(terms_file, 'r', encoding='utf-8') as f:
                header = next(f).strip()
                if header != "term\tdf\tidf":
                    logger.warning(f"Unexpected terms header: {header}")
                
                for line_num, line in enumerate(f, 2):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) != 3:
                        logger.warning(f"Invalid terms line {line_num}: {line}")
                        continue
                    
                    try:
                        term, df, idf = parts
                        self.terms[term] = (int(df), float(idf))
                    except ValueError as e:
                        logger.warning(f"Invalid terms data at line {line_num}: {e}")
                        continue
            
            # Load postings
            postings_file = self.index_dir / "postings.tsv"
            if not postings_file.exists():
                raise FileNotFoundError(f"Postings file not found: {postings_file}")
            
            with open(postings_file, 'r', encoding='utf-8') as f:
                header = next(f).strip()
                if header != "term\tfield\tdocId\ttf":
                    logger.warning(f"Unexpected postings header: {header}")
                
                for line_num, line in enumerate(f, 2):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) != 4:
                        logger.warning(f"Invalid postings line {line_num}: {line}")
                        continue
                    
                    try:
                        term, field, doc_id, tf = parts
                        if term in self.terms:  # Only load postings for valid terms
                            self.postings[term].append((field, doc_id, int(tf)))
                    except ValueError as e:
                        logger.warning(f"Invalid postings data at line {line_num}: {e}")
                        continue
            
            # Load document metadata
            docmeta_file = self.index_dir / "docmeta.tsv"
            if not docmeta_file.exists():
                raise FileNotFoundError(f"Document metadata file not found: {docmeta_file}")
            
            with open(docmeta_file, 'r', encoding='utf-8') as f:
                header = next(f).strip()
                if header != "docId\turl\ttitle\tlen_title\tlen_ing\tlen_instr":
                    logger.warning(f"Unexpected docmeta header: {header}")
                
                for line_num, line in enumerate(f, 2):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) < 6:
                        logger.warning(f"Invalid docmeta line {line_num}: {line}")
                        continue
                    
                    try:
                        doc_id, url, title, len_title, len_ing, len_instr = parts[:6]
                        self.doc_metadata[doc_id] = {
                            'url': url,
                            'title': title,
                            'len_title': int(len_title),
                            'len_ing': int(len_ing),
                            'len_instr': int(len_instr)
                        }
                    except ValueError as e:
                        logger.warning(f"Invalid docmeta data at line {line_num}: {e}")
                        continue
            
            self.total_docs = len(self.doc_metadata)
            logger.info(f"Loaded index: {len(self.terms)} terms, {self.total_docs} documents")
            
            if self.total_docs == 0:
                raise ValueError("No documents found in index")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise
    
    def tokenize(self, text: str) -> List[str]:
        """Robust tokenization with comprehensive text cleaning."""
        if not text or not isinstance(text, str):
            return []
        
        # Clean text: remove HTML entities, normalize whitespace
        text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)  # Remove HTML entities
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        if not text:
            return []
        
        # Extract words (alphanumeric only)
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # Comprehensive stopword list
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
            'do', 'does', 'did', 'doing', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'am', 'are', 'is', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
            'do', 'does', 'did', 'doing', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'shall', 'ought', 'need', 'dare', 'used', 'get', 'got', 'getting', 'go', 'went',
            'gone', 'going', 'come', 'came', 'coming', 'see', 'saw', 'seen', 'seeing', 'know', 'knew',
            'known', 'knowing', 'think', 'thought', 'thinking', 'take', 'took', 'taken', 'taking',
            'give', 'gave', 'given', 'giving', 'make', 'made', 'making', 'find', 'found', 'finding',
            'tell', 'told', 'telling', 'ask', 'asked', 'asking', 'work', 'worked', 'working',
            'seem', 'seemed', 'seeming', 'feel', 'felt', 'feeling', 'try', 'tried', 'trying',
            'leave', 'left', 'leaving', 'call', 'called', 'calling', 'move', 'moved', 'moving',
            'turn', 'turned', 'turning', 'start', 'started', 'starting', 'show', 'showed', 'showing',
            'hear', 'heard', 'hearing', 'play', 'played', 'playing', 'run', 'ran', 'running',
            'open', 'opened', 'opening', 'close', 'closed', 'closing', 'help', 'helped', 'helping',
            'keep', 'kept', 'keeping', 'let', 'letting', 'put', 'putting', 'set', 'setting',
            'bring', 'brought', 'bringing', 'begin', 'began', 'begun', 'beginning', 'sit', 'sat',
            'sitting', 'stand', 'stood', 'standing', 'lose', 'lost', 'losing', 'pay', 'paid', 'paying',
            'meet', 'met', 'meeting', 'include', 'included', 'including', 'continue', 'continued',
            'continuing', 'set', 'setting', 'follow', 'followed', 'following', 'stop', 'stopped',
            'stopping', 'create', 'created', 'creating', 'speak', 'spoke', 'spoken', 'speaking',
            'read', 'reading', 'allow', 'allowed', 'allowing', 'add', 'added', 'adding', 'spend',
            'spent', 'spending', 'grow', 'grew', 'grown', 'growing', 'open', 'opened', 'opening',
            'walk', 'walked', 'walking', 'win', 'won', 'winning', 'offer', 'offered', 'offering',
            'remember', 'remembered', 'remembering', 'love', 'loved', 'loving', 'consider', 'considered',
            'considering', 'appear', 'appeared', 'appearing', 'buy', 'bought', 'buying', 'wait',
            'waited', 'waiting', 'serve', 'served', 'serving', 'die', 'died', 'dying', 'send',
            'sent', 'sending', 'expect', 'expected', 'expecting', 'build', 'built', 'building',
            'stay', 'stayed', 'staying', 'fall', 'fell', 'fallen', 'falling', 'cut', 'cutting',
            'reach', 'reached', 'reaching', 'kill', 'killed', 'killing', 'remain', 'remained',
            'remaining', 'suggest', 'suggested', 'suggesting', 'raise', 'raised', 'raising',
            'pass', 'passed', 'passing', 'sell', 'sold', 'selling', 'require', 'required',
            'requiring', 'report', 'reported', 'reporting', 'decide', 'decided', 'deciding',
            'pull', 'pulled', 'pulling', 'break', 'broke', 'broken', 'breaking', 'rise', 'rose',
            'risen', 'rising', 'walk', 'walked', 'walking', 'throw', 'threw', 'thrown', 'throwing',
            'drop', 'dropped', 'dropping', 'catch', 'caught', 'catching', 'choose', 'chose',
            'chosen', 'choosing', 'deal', 'dealt', 'dealing', 'prove', 'proved', 'proving',
            'hold', 'held', 'holding', 'write', 'wrote', 'written', 'writing', 'provide',
            'provided', 'providing', 'sit', 'sat', 'sitting', 'stand', 'stood', 'standing',
            'lose', 'lost', 'losing', 'pay', 'paid', 'paying', 'meet', 'met', 'meeting',
            'include', 'included', 'including', 'continue', 'continued', 'continuing'
        }
        
        # Filter out stopwords and short words
        filtered_words = [word for word in words if word not in stopwords and len(word) > 1]
        
        return filtered_words
    
    def search_tfidf(self, query: str, k: int = 10, filters: Optional[Dict] = None, offset: int = 0) -> List[Tuple[str, float, str]]:
        """Search using TF-IDF cosine similarity with comprehensive error handling."""
        try:
            query_terms = self.tokenize(query)
            if not query_terms:
                # If no query terms but filters are applied, use optimized filtering
                if filters:
                    # Use optimized filtering without broad search
                    results = self._filter_all_documents(filters)
                    return results[offset:offset + k]
                else:
                    logger.warning("Empty query after tokenization")
                    return []
            
            # Calculate query vector
            query_tf = {}
            for term in query_terms:
                query_tf[term] = query_tf.get(term, 0) + 1
            
            # Calculate query vector magnitude
            query_magnitude = 0
            for term in query_tf:
                if term in self.terms:
                    _, idf = self.terms[term]
                    tf_idf = query_tf[term] * idf
                    query_magnitude += tf_idf ** 2
            query_magnitude = math.sqrt(query_magnitude)
            
            if query_magnitude == 0:
                logger.warning("Query has no valid terms")
                return []
            
            # Score documents
            doc_scores = defaultdict(float)
            doc_magnitudes = defaultdict(float)
            
            for term in query_tf:
                if term not in self.terms:
                    continue
                
                _, idf = self.terms[term]
                query_tf_idf = query_tf[term] * idf
                
                for field, doc_id, tf in self.postings[term]:
                    if self._apply_filters(doc_id, filters):
                        doc_tf_idf = tf * idf * self.field_weights[field]
                        doc_scores[doc_id] += query_tf_idf * doc_tf_idf
                        doc_magnitudes[doc_id] += doc_tf_idf ** 2
            
            # Calculate cosine similarity
            results = []
            for doc_id in doc_scores:
                if doc_magnitudes[doc_id] > 0:
                    magnitude = math.sqrt(doc_magnitudes[doc_id])
                    cosine_sim = doc_scores[doc_id] / (query_magnitude * magnitude)
                    snippet = self._generate_snippet(doc_id, query_terms)
                    results.append((doc_id, cosine_sim, snippet))
            
            # Sort by score (descending) and return top-k
            results.sort(key=lambda x: x[1], reverse=True)
            
            self.stats['queries_processed'] += 1
            self.stats['total_results'] += len(results)
            self.stats['avg_results_per_query'] = self.stats['total_results'] / self.stats['queries_processed']
            
            return results[offset:offset + k]
            
        except Exception as e:
            logger.error(f"Error in TF-IDF search: {e}")
            return []
    
    def get_total_results(self, query: str, filters: Optional[Dict] = None) -> int:
        """Get total number of results for a query without pagination."""
        try:
            query_terms = self.tokenize(query)
            
            # If no query terms but filters are applied, count documents that match filters
            if not query_terms:
                if filters:
                    # Use optimized filtering to count results
                    results = self._filter_all_documents(filters)
                    return len(results)
                else:
                    return 0
            
            # Count matching documents for query terms
            matching_docs = set()
            
            for term in query_terms:
                if term in self.postings:
                    for field, doc_id, tf in self.postings[term]:
                        if self._apply_filters(doc_id, filters):
                            matching_docs.add(doc_id)
            
            return len(matching_docs)
            
        except Exception as e:
            logger.error(f"Error getting total results: {e}")
            return 0
    
    def search_bm25(self, query: str, k: int = 10, filters: Optional[Dict] = None, offset: int = 0) -> List[Tuple[str, float, str]]:
        """Search using BM25 ranking with comprehensive error handling."""
        try:
            query_terms = self.tokenize(query)
            if not query_terms:
                # If no query terms but filters are applied, use optimized filtering
                if filters:
                    # Use optimized filtering without broad search
                    results = self._filter_all_documents(filters)
                    return results[offset:offset + k]
                else:
                    logger.warning("Empty query after tokenization")
                    return []
            
            # Calculate average document length
            if self.total_docs == 0:
                logger.warning("No documents in index")
                return []
            
            avg_doc_length = sum(
                meta['len_title'] + meta['len_ing'] + meta['len_instr'] 
                for meta in self.doc_metadata.values()
            ) / self.total_docs
            
            # Count query term frequencies
            query_tf = {}
            for term in query_terms:
                query_tf[term] = query_tf.get(term, 0) + 1
            
            # Score documents
            doc_scores = defaultdict(float)
            
            for term in query_tf:
                if term not in self.terms:
                    continue
                
                df, idf = self.terms[term]
                query_freq = query_tf[term]
                
                for field, doc_id, tf in self.postings[term]:
                    if self._apply_filters(doc_id, filters):
                        # Get document length for this field
                        meta = self.doc_metadata[doc_id]
                        if field == 'title':
                            doc_length = meta['len_title']
                        elif field == 'ingredients':
                            doc_length = meta['len_ing']
                        else:  # instructions
                            doc_length = meta['len_instr']
                        
                        # Calculate BM25 score for this term in this field
                        bm25_score = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (doc_length / avg_doc_length)))
                        bm25_score *= idf * self.field_weights[field]
                        
                        doc_scores[doc_id] += bm25_score
            
            # Generate results
            results = []
            for doc_id, score in doc_scores.items():
                snippet = self._generate_snippet(doc_id, query_terms)
                results.append((doc_id, score, snippet))
            
            # Sort by score (descending) and return paginated results
            results.sort(key=lambda x: x[1], reverse=True)
            
            self.stats['queries_processed'] += 1
            self.stats['total_results'] += len(results)
            self.stats['avg_results_per_query'] = self.stats['total_results'] / self.stats['queries_processed']
            
            return results[offset:offset + k]
            
        except Exception as e:
            logger.error(f"Error in BM25 search: {e}")
            return []
    
    def _filter_all_documents(self, filters: Optional[Dict]) -> List[Tuple[str, float, str]]:
        """Ultra-fast filtering with aggressive optimization."""
        if not filters:
            return []
        
        # Create cache key for this filter combination
        cache_key = str(sorted(filters.items()))
        if cache_key in self._filter_cache:
            return self._filter_cache[cache_key]
        
        results = []
        
        # For time-only filters, use a much faster approach
        if self._only_time_filters(filters):
            results = self._filter_by_time_only(filters)
            self._filter_cache[cache_key] = results
            return results
        
        # Limit the number of documents we process for performance
        max_docs_to_process = 2000  # Process only first 2000 docs for speed
        doc_ids = list(self.doc_metadata.keys())[:max_docs_to_process]
        
        # Use larger batches for better performance
        batch_size = 500
        processed = 0
        
        for i in range(0, len(doc_ids), batch_size):
            batch = doc_ids[i:i + batch_size]
            
            # Load batch of recipes efficiently
            batch_recipes = self._load_recipes_batch(batch)
            
            for doc_id in batch:
                recipe_data = batch_recipes.get(doc_id)
                if recipe_data and self._apply_filters(doc_id, filters, recipe_data=recipe_data):
                    snippet = self._generate_snippet(doc_id, [])
                    results.append((doc_id, 1.0, snippet))
                    processed += 1
                    
                    # Limit results for very fast response
                    if len(results) >= 1000:
                        break
            
            if len(results) >= 1000:
                break
        
        # Sort by doc_id for consistent ordering
        results.sort(key=lambda x: x[0])
        
        # Cache the results
        self._filter_cache[cache_key] = results
        return results
    
    def _needs_content_filtering(self, filters: Dict) -> bool:
        """Check if filters require loading full recipe content."""
        content_filter_keys = {
            'cuisine', 'category', 'ingredients', 'keywords', 'author', 
            'author_location', 'has_image', 'meal_type', 'dietary', 'cooking_method'
        }
        return any(key in filters for key in content_filter_keys)
    
    def _only_time_filters(self, filters: Dict) -> bool:
        """Check if only time-related filters are present."""
        time_filter_keys = {'max_total_minutes', 'min_total_minutes', 'max_prep_minutes', 
                          'min_prep_minutes', 'max_cook_minutes', 'min_cook_minutes'}
        return all(key in time_filter_keys for key in filters.keys())
    
    def _filter_by_time_only(self, filters: Dict) -> List[Tuple[str, float, str]]:
        """Optimized time-only filtering by loading recipes in batches."""
        results = []
        
        # Load recipes in batches to reduce I/O
        batch_size = 100
        doc_ids = list(self.doc_metadata.keys())
        
        for i in range(0, len(doc_ids), batch_size):
            batch = doc_ids[i:i + batch_size]
            batch_recipes = self._load_recipes_batch(batch)
            
            for doc_id, recipe_data in batch_recipes.items():
                if recipe_data and self._check_time_filters(recipe_data, filters):
                    snippet = self._generate_snippet(doc_id, [])
                    results.append((doc_id, 1.0, snippet))
        
        return results
    
    def _load_recipes_batch(self, doc_ids: List[str]) -> Dict[str, Dict]:
        """Load multiple recipes at once for better I/O performance."""
        recipes = {}
        doc_ids_set = set(doc_ids)  # Convert to set for O(1) lookup
        
        try:
            with open('data/normalized/recipes.jsonl', 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        recipe = json.loads(line.strip())
                        recipe_id = recipe.get('id')
                        if recipe_id in doc_ids_set:
                            recipes[recipe_id] = recipe
                            # Early termination when we have all requested recipes
                            if len(recipes) == len(doc_ids):
                                break
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            logger.error("Recipes file not found")
        
        return recipes
    
    def _check_time_filters(self, recipe_data: Dict, filters: Dict) -> bool:
        """Check only time-related filters without loading full recipe data."""
        times = recipe_data.get('times', {})
        total_time = times.get('total', 0)
        prep_time = times.get('prep', 0)
        cook_time = times.get('cook', 0)
        
        if filters.get('max_total_minutes') and total_time > filters['max_total_minutes']:
            return False
        
        if filters.get('min_total_minutes') and total_time < filters['min_total_minutes']:
            return False
        
        if filters.get('max_prep_minutes') and prep_time > filters['max_prep_minutes']:
            return False
        
        if filters.get('min_prep_minutes') and prep_time < filters['min_prep_minutes']:
            return False
        
        if filters.get('max_cook_minutes') and cook_time > filters['max_cook_minutes']:
            return False
        
        if filters.get('min_cook_minutes') and cook_time < filters['min_cook_minutes']:
            return False
        
        return True
    
    def _quick_metadata_filter(self, doc_id: str, meta: Dict, filters: Optional[Dict]) -> bool:
        """Quick pre-filtering using only metadata to avoid loading full recipe data."""
        if not filters:
            return True
        
        # Time-based filtering using metadata
        if 'max_total_minutes' in filters:
            if 'total_minutes' in meta and meta['total_minutes'] > filters['max_total_minutes']:
                return False
        
        if 'min_total_minutes' in filters:
            if 'total_minutes' in meta and meta['total_minutes'] < filters['min_total_minutes']:
                return False
        
        # Rating-based filtering using metadata
        if 'min_rating' in filters:
            if 'rating' in meta:
                try:
                    rating_value = float(meta['rating']) if meta['rating'] else 0.0
                    if rating_value < filters['min_rating']:
                        return False
                except (ValueError, TypeError):
                    # If rating can't be converted to float, skip this filter
                    pass
        
        if 'min_review_count' in filters:
            if 'review_count' in meta:
                try:
                    review_count_value = int(meta['review_count']) if meta['review_count'] else 0
                    if review_count_value < filters['min_review_count']:
                        return False
                except (ValueError, TypeError):
                    # If review_count can't be converted to int, skip this filter
                    pass
        
        # Servings filtering using metadata
        if 'min_servings' in filters:
            if 'servings' in meta and meta['servings'] < filters['min_servings']:
                return False
        
        if 'max_servings' in filters:
            if 'servings' in meta and meta['servings'] > filters['max_servings']:
                return False
        
        # Difficulty filtering using metadata
        if 'difficulty' in filters:
            if 'difficulty' in meta:
                recipe_difficulties = [d.lower() for d in meta['difficulty']] if isinstance(meta['difficulty'], list) else [meta['difficulty'].lower()]
                filter_difficulties = [d.lower() for d in filters['difficulty']]
                if not any(d in recipe_difficulties for d in filter_difficulties):
                    return False
        
        return True
    
    def _apply_filters(self, doc_id: str, filters: Optional[Dict], recipe_data: Optional[Dict] = None) -> bool:
        """Apply comprehensive search filters to document."""
        if not filters:
            return True
        
        # Use provided recipe data or load it if not provided
        if recipe_data is None:
            recipe_data = self._get_recipe_data(doc_id)
            if not recipe_data:
                return False
        
        # Basic filters
        if filters.get('cuisine'):
            recipe_cuisines = [c.lower() for c in recipe_data.get('cuisine', [])]
            if not any(cuisine.lower() in recipe_cuisines for cuisine in filters['cuisine']):
                return False
        
        if filters.get('ingredients'):
            recipe_ingredients = [ing.lower() for ing in recipe_data.get('ingredients', [])]
            if not any(ing.lower() in recipe_ingredients for ing in filters['ingredients']):
                return False
        
        if filters.get('difficulty'):
            recipe_difficulty = recipe_data.get('difficulty', '').lower()
            if not any(diff.lower() in recipe_difficulty for diff in filters['difficulty']):
                return False
        
        if filters.get('category'):
            recipe_categories = [cat.lower() for cat in recipe_data.get('category', [])]
            if not any(cat.lower() in recipe_categories for cat in filters['category']):
                return False
        
        # New category filters
        if filters.get('meal_type'):
            # Check title, description, and keywords for meal type indicators
            text_content = f"{recipe_data.get('title', '')} {recipe_data.get('description', '')} {' '.join(recipe_data.get('keywords', []))}".lower()
            if not any(meal_type.lower() in text_content for meal_type in filters['meal_type']):
                return False
        
        if filters.get('dietary'):
            # Check title, description, keywords, and ingredients for dietary indicators
            text_content = f"{recipe_data.get('title', '')} {recipe_data.get('description', '')} {' '.join(recipe_data.get('keywords', []))}".lower()
            ingredients_text = ' '.join(recipe_data.get('ingredients', [])).lower()
            combined_text = f"{text_content} {ingredients_text}"
            if not any(diet.lower() in combined_text for diet in filters['dietary']):
                return False
        
        if filters.get('cooking_method'):
            # Check title, description, and instructions for cooking method indicators
            text_content = f"{recipe_data.get('title', '')} {recipe_data.get('description', '')} {' '.join(recipe_data.get('instructions', []))}".lower()
            if not any(method.lower() in text_content for method in filters['cooking_method']):
                return False
        
        if filters.get('tools'):
            recipe_tools = [tool.lower() for tool in recipe_data.get('tools', [])]
            if not any(tool.lower() in recipe_tools for tool in filters['tools']):
                return False
        
        # Time filters
        times = recipe_data.get('times', {})
        total_time = times.get('total', 0)
        prep_time = times.get('prep', 0)
        cook_time = times.get('cook', 0)
        
        if filters.get('max_total_minutes') and total_time > filters['max_total_minutes']:
            return False
        
        if filters.get('min_total_minutes') and total_time < filters['min_total_minutes']:
            return False
        
        if filters.get('max_prep_minutes') and prep_time > filters['max_prep_minutes']:
            return False
        
        if filters.get('max_cook_minutes') and cook_time > filters['max_cook_minutes']:
            return False
        
        # Rating filters - convert string values to numbers
        ratings = recipe_data.get('ratings', {})
        
        if isinstance(ratings, dict):
            # Handle different rating field names and convert strings to numbers
            rating_raw = ratings.get('average', ratings.get('rating', ratings.get('score')))
            rating_value = self._safe_float(rating_raw)
            
            # Handle review count
            review_count_raw = ratings.get('review_count', ratings.get('count'))
            review_count_value = self._safe_int(review_count_raw)
        else:
            rating_value = self._safe_float(ratings)
            review_count_value = 0
        
        if filters.get('min_rating') and rating_value < filters['min_rating']:
            return False
        
        if filters.get('max_rating') and rating_value > filters['max_rating']:
            return False
        
        if filters.get('min_review_count') and review_count_value < filters['min_review_count']:
            return False
        
        # Nutrition filters - convert string values to float for comparison
        nutrition = recipe_data.get('nutrition', {})
        
        calories = self._safe_float(nutrition.get('calories'))
        if filters.get('max_calories') and calories > filters['max_calories']:
            return False
        if filters.get('min_calories') and calories < filters['min_calories']:
            return False
        
        protein = self._safe_float(nutrition.get('protein'))
        if filters.get('max_protein') and protein > filters['max_protein']:
            return False
        if filters.get('min_protein') and protein < filters['min_protein']:
            return False
        
        # Handle both 'carbs' and 'carbohydrates' field names
        carbs = self._safe_float(nutrition.get('carbs', nutrition.get('carbohydrates')))
        if filters.get('max_carbs') and carbs > filters['max_carbs']:
            return False
        if filters.get('min_carbs') and carbs < filters['min_carbs']:
            return False
        
        fat = self._safe_float(nutrition.get('fat'))
        if filters.get('max_fat') and fat > filters['max_fat']:
            return False
        if filters.get('min_fat') and fat < filters['min_fat']:
            return False
        
        fiber = self._safe_float(nutrition.get('fiber'))
        if filters.get('max_fiber') and fiber > filters['max_fiber']:
            return False
        if filters.get('min_fiber') and fiber < filters['min_fiber']:
            return False
        
        sugar = self._safe_float(nutrition.get('sugar'))
        if filters.get('max_sugar') and sugar > filters['max_sugar']:
            return False
        if filters.get('min_sugar') and sugar < filters['min_sugar']:
            return False
        
        sodium = self._safe_float(nutrition.get('sodium'))
        if filters.get('max_sodium') and sodium > filters['max_sodium']:
            return False
        
        if filters.get('min_sodium') and nutrition.get('sodium', 0) < filters['min_sodium']:
            return False
        
        # Serving and yield filters - extract numeric portion from yield string
        yield_str = recipe_data.get('yield', '')
        if yield_str and (filters.get('min_yield') or filters.get('max_yield')):
            # Extract first number from yield string (e.g., "12 cookies" -> 12)
            # re is already imported at top-level
            match = re.search(r'(\d+(?:\.\d+)?)', str(yield_str))
            if match:
                yield_value = self._safe_float(match.group(1))
                if filters.get('min_yield') and yield_value < filters['min_yield']:
                    return False
                if filters.get('max_yield') and yield_value > filters['max_yield']:
                    return False
            elif filters.get('min_yield'):
                # No numeric value found and minimum required - filter out
                return False
        
        # Author filters
        if filters.get('author'):
            recipe_author = recipe_data.get('author', '').lower()
            if not any(auth.lower() in recipe_author for auth in filters['author']):
                return False
        
        # Date filters
        if filters.get('min_publication_date') or filters.get('max_publication_date'):
            pub_date = recipe_data.get('publication_date', '')
            if pub_date:
                try:
                    from datetime import datetime
                    recipe_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    
                    if filters.get('min_publication_date'):
                        min_date = datetime.fromisoformat(filters['min_publication_date'].replace('Z', '+00:00'))
                        if recipe_date < min_date:
                            return False
                    
                    if filters.get('max_publication_date'):
                        max_date = datetime.fromisoformat(filters['max_publication_date'].replace('Z', '+00:00'))
                        if recipe_date > max_date:
                            return False
                except:
                    pass  # Skip date filtering if parsing fails
        
        # Image filters
        if filters.get('has_image'):
            # Check if recipe has a main image URL
            image = recipe_data.get('image', '')
            if not image or image.strip() == '':
                return False
        
        # Keyword filters
        if filters.get('keywords'):
            recipe_keywords = [kw.lower() for kw in recipe_data.get('keywords', [])]
            recipe_text = f"{recipe_data.get('title', '')} {recipe_data.get('description', '')}".lower()
            if not any(kw.lower() in recipe_keywords or kw.lower() in recipe_text for kw in filters['keywords']):
                return False
        
        # Advanced filters
        ingredients_count = len(recipe_data.get('ingredients', []))
        if filters.get('min_ingredients') and ingredients_count < filters['min_ingredients']:
            return False
        
        if filters.get('max_ingredients') and ingredients_count > filters['max_ingredients']:
            return False
        
        instructions_count = len(recipe_data.get('instructions', []))
        if filters.get('min_instructions') and instructions_count < filters['min_instructions']:
            return False
        
        if filters.get('max_instructions') and instructions_count > filters['max_instructions']:
            return False
        
        return True
    
    def _get_recipe_data(self, doc_id: str) -> Optional[Dict]:
        """Get full recipe data for filtering."""
        try:
            # Try to load from normalized data
            possible_paths = [
                'data/normalized_final_v6/recipes.jsonl',
                'data/normalized_final_v5/recipes.jsonl',
                'data/normalized_final_v4/recipes.jsonl',
                'data/normalized_final_v3/recipes.jsonl',
                'data/normalized_final_v2/recipes.jsonl',
                'data/normalized_final/recipes.jsonl',
                'data/normalized/recipes.jsonl'
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                try:
                                    recipe = json.loads(line)
                                    if recipe.get('id') == doc_id:
                                        return recipe
                                except json.JSONDecodeError:
                                    continue
            return None
        except Exception as e:
            logger.warning(f"Error loading recipe data for {doc_id}: {e}")
            return None
    
    def _generate_snippet(self, doc_id: str, query_terms: List[str]) -> str:
        """Generate a snippet for the document highlighting query terms."""
        meta = self.doc_metadata.get(doc_id, {})
        title = meta.get('title', '')
        
        if title:
            # Highlight query terms in title
            snippet = title
            for term in query_terms:
                snippet = re.sub(f'\\b{re.escape(term)}\\b', f'**{term}**', snippet, flags=re.IGNORECASE)
            return snippet
        
        return f"Document {doc_id}"
    
    def get_document_info(self, doc_id: str) -> Dict[str, Any]:
        """Get full document information."""
        return self.doc_metadata.get(doc_id, {})
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        return self.stats.copy()

def detect_index_type(index_dir: Path) -> str:
    """
    Detect index type: 'lucene' or 'tsv'.
    
    Args:
        index_dir: Path to index directory
    
    Returns:
        'lucene' if Lucene index, 'tsv' if TSV index
    """
    # Check for Lucene index files
    lucene_markers = ['segments_', 'write.lock']
    for marker in lucene_markers:
        if list(index_dir.glob(marker + '*')):
            return 'lucene'
    
    # Check for TSV index files
    tsv_files = ['terms.tsv', 'postings.tsv', 'docmeta.tsv']
    if all((index_dir / f).exists() for f in tsv_files):
        return 'tsv'
    
    # Default to TSV for backward compatibility
    return 'tsv'


def main():
    """Main function for unified search CLI (supports TSV and PyLucene)."""
    parser = argparse.ArgumentParser(
        description='Search recipes using TF-IDF or BM25 (supports TSV and PyLucene indexes)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search TSV index (baseline)
  python3 search_cli/run.py --index data/index/v1 --metric bm25 --q "chicken pasta" --k 10
  
  # Search PyLucene index
  python3 search_cli/run.py --index index/lucene/v2 --metric bm25 --q "mexican chicken" --k 10
  
  # With filters (JSON)
  python3 search_cli/run.py --index index/lucene/v2 --metric bm25 --q "pasta" \\
      --filter '{"max_total_minutes": 30, "cuisine": "Italian"}'
        """
    )
    parser.add_argument('--index', required=True, help='Index directory (TSV or PyLucene)')
    parser.add_argument('--metric', choices=['tfidf', 'bm25'], default='bm25', help='Search metric')
    parser.add_argument('--q', required=True, help='Search query')
    parser.add_argument('--k', type=int, default=10, help='Number of results to return')
    parser.add_argument('--filter', help='JSON string with filters')
    parser.add_argument('--quiet', action='store_true', help='Minimal output (for programmatic use)')
    parser.add_argument('--index-type', choices=['auto', 'tsv', 'lucene'], default='auto',
                       help='Force index type (default: auto-detect)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.k <= 0:
        logger.error("Number of results (--k) must be positive")
        return 1
    
    # Parse filters
    filters = None
    if args.filter:
        try:
            filters = json.loads(args.filter)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in --filter argument: {e}")
            return 1
    
    # Configure logging based on quiet mode
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    else:
        logger.info(f"Starting search: '{args.q}' using {args.metric}")
    
    # TODO: Suggest query corrections (did you mean...?)
    # Detect index type
    index_path = Path(args.index)
    if not index_path.exists():
        logger.error(f"Index directory not found: {index_path}")
        return 1
    
    if args.index_type == 'auto':
        index_type = detect_index_type(index_path)
    else:
        index_type = args.index_type
    
    if not args.quiet:
        logger.info(f"Detected index type: {index_type}")
    
    # Initialize appropriate searcher
    searcher = None
    try:
        if index_type == 'lucene':
            if not LUPYNE_AVAILABLE:
                logger.error("Lupyne is not available. Install it or use TSV index.")
                if not args.quiet:
                    print("ERROR: Lupyne is not installed!")
                    print("To install: pip install 'lupyne[graphql,rest]'")
                    print("See LUPYNE_INSTALL.md for PyLucene installation first.")
                    print("Alternatively, use TSV index: --index data/index/v1")
                return 1
            
            searcher = LupyneRecipeSearcher(args.index)
        else:
            searcher = RobustRecipeSearcher(args.index)
            
    except FileNotFoundError as e:
        logger.error(f"Index loading failed: {e}")
        if not args.quiet:
            print(f"Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error loading index: {e}")
        if not args.quiet:
            print(f"Error: {e}")
        return 1
    
    # Perform search
    try:
        if args.metric == 'tfidf':
            results = searcher.search_tfidf(args.q, args.k, filters)
        else:  # bm25
            results = searcher.search_bm25(args.q, args.k, filters)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        if not args.quiet:
            print(f"Error: {e}")
        # Cleanup before returning
        if index_type == 'lucene':
            searcher.close()
        return 1
    finally:
        # Always cleanup Lupyne resources
        if index_type == 'lucene':
            searcher.close()
    
    # Display results (unified format for both index types)
    if not args.quiet:
        print(f"\n{'='*80}")
        print(f"Search Results: '{args.q}' ({args.metric.upper()}, {index_type.upper()} index)")
        print(f"{'='*80}")
    
    if not results:
        if not args.quiet:
            print("No results found.")
        return 0
    
    # Handle different result formats
    for i, result in enumerate(results, 1):
        if isinstance(result, dict):
            # Lupyne/PyLucene format
            doc_id = result.get('docId', result.get('doc_id', 'N/A'))
            score = result.get('score', 0.0)
            title = result.get('title', result.get('title_text', 'No title'))
            url = result.get('url', 'N/A')
            total_minutes = result.get('total_minutes')
            wiki_abstracts = result.get('wiki_abstracts', '')
            ingredients = result.get('ingredients', result.get('ingredients_text', ''))
            
            if args.quiet:
                print(f"{doc_id}\t{score:.4f}")
            else:
                # STRUCTURED OUTPUT: VARIABLE: VALUE format
                print(f"\n{'='*80}")
                print(f"RESULT #{i}: {title}")
                print(f"{'='*80}")
                print(f"SCORE: {score:.4f}")
                print(f"DOC_ID: {doc_id}")
                print(f"URL: {url}")
                print()
                
                # Extract all available fields
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
                wiki_text = result.get('wiki_abstracts', '')
                
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
                
                # Wikipedia section - DETAILED ENTITY LIST
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
                    # FIXME: Sometimes shows duplicate entities with different surfaces
                    for entity_type, links in sorted(by_type.items()):
                        print(f"\n   {entity_type.upper()}S:")
                        for link in links[:5]:  # Max 5 per type
                            wiki_title = link.get('wiki_title', 'N/A')
                            surface = link.get('surface', 'N/A')
                            abstract = link.get('abstract', '')
                            categories = link.get('categories', [])
                            
                            # Clean abstract
                            if abstract:
                                abstract_clean = abstract.replace('(, ; )', '').replace('()', '')
                                # re is already imported at top-level
                                abstract_clean = re.sub(r'\|[a-z\-]+=', ' ', abstract_clean)
                                abstract_clean = ' '.join(abstract_clean.split()).strip()
                                abstract_short = abstract_clean[:150] + ('...' if len(abstract_clean) > 150 else '')
                            else:
                                abstract_short = 'N/A'
                            
                            print(f"      • {wiki_title} (matched: '{surface}')")
                            print(f"        {abstract_short}")
                            if categories:
                                print(f"        Categories: {', '.join(categories[:3])}")
                
                print()

        else:
            # TSV format (tuple: doc_id, score, snippet)
            doc_id, score, snippet = result
            doc_info = searcher.get_document_info(doc_id)
            
            if args.quiet:
                print(f"{doc_id}\t{score:.4f}")
            else:
                print(f"\n{i}. {snippet}")
                print(f"   Score: {score:.4f} | ID: {doc_id}")
                print(f"   🔗 {doc_info.get('url', 'N/A')}")
    
    # Display statistics (only for TSV index)
    if not args.quiet and index_type == 'tsv':
        stats = searcher.get_stats()
        print(f"\n{'='*80}")
        print(f"Search Statistics:")
        print(f"  Queries processed: {stats['queries_processed']}")
        print(f"  Total results: {stats['total_results']}")
        print(f"  Average results per query: {stats['avg_results_per_query']:.2f}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())