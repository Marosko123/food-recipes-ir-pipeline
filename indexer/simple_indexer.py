#!/usr/bin/env python3
"""
Simple Inverted Index - Pure Python Implementation (No PyLucene)

This is a custom inverted index implementation using only allowed libraries:
- re, json, math, argparse, pathlib, logging, gzip, hashlib

Supports:
- TF-IDF scoring with field-specific boosts
- BM25 scoring (k1=1.2, b=0.75)
- Multi-field indexing (title, ingredients, instructions)
- Boolean filters (cuisine, time range)

Output format: TSV files (terms.tsv, postings.tsv, docmeta.tsv)

Usage:
    # Build index
    python -m indexer.simple_indexer --mode build \
        --input data/normalized/recipes_enriched.jsonl \
        --output index/v1

    # Search
    python -m indexer.simple_indexer --mode search \
        --index index/v1 \
        --query "chocolate cake" \
        --metric bm25 \
        --k 10
"""

import argparse
import gzip
import hashlib
import json
import logging
import math
import re
import sys
import time
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# STOPWORDS
# ============================================================================

STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
    'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 
    'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would', 
    'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 
    'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 
    'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'am', 'into',
    'from', 'up', 'down', 'out', 'about', 'just', 'also', 'very', 'so', 'too',
    'only', 'own', 'same', 'than', 'then', 'now', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'not', 'only', 'own', 'same',
    'as', 'until', 'while', 'during', 'before', 'after', 'above', 'below',
    'between', 'under', 'again', 'further', 'once', 'any', 'if',
}


# ============================================================================
# STEMMER (Simple Porter Stemmer implementation)
# ============================================================================

def porter_stem(word: str) -> str:
    """
    Simple Porter Stemmer implementation.
    
    Applies common English suffix stripping rules:
    - ING endings (running -> runn -> run)
    - ED endings (cooked -> cook)
    - TION endings (creation -> creat)
    - NESS endings (happiness -> happi)
    - LY endings (quickly -> quick)
    - S/ES endings (cooks -> cook)
    """
    if len(word) <= 2:
        return word
    
    # Step 1: Plural/Verb endings
    if word.endswith('sses'):
        word = word[:-2]
    elif word.endswith('ies'):
        word = word[:-2]
    elif word.endswith('ss'):
        pass  # keep as is (boss, mass)
    elif word.endswith('s') and len(word) > 3:
        word = word[:-1]
    
    # Step 2: Past tense and gerund (-ed, -ing)
    if word.endswith('eed'):
        if len(word) > 4:
            word = word[:-1]  # agreed -> agree
    elif word.endswith('ed'):
        if len(word) > 4:
            word = word[:-2]  # cooked -> cook
            # Handle doubling (stopped -> stop)
            if word.endswith('pp') or word.endswith('dd') or word.endswith('tt'):
                word = word[:-1]
    elif word.endswith('ing'):
        if len(word) > 5:
            word = word[:-3]  # cooking -> cook
            # Handle doubling
            if word.endswith('pp') or word.endswith('dd') or word.endswith('tt'):
                word = word[:-1]
    
    # Step 3: -tion, -sion endings
    if word.endswith('tion') and len(word) > 5:
        word = word[:-3] + 'e'  # creation -> create
    elif word.endswith('sion') and len(word) > 5:
        word = word[:-3] + 'e'  # revision -> revise
    
    # Step 4: -ness, -ment, -ful endings
    if word.endswith('ness') and len(word) > 5:
        word = word[:-4]  # happiness -> happi
    elif word.endswith('ment') and len(word) > 5:
        word = word[:-4]  # government -> govern
    elif word.endswith('ful') and len(word) > 4:
        word = word[:-3]  # beautiful -> beauti
    
    # Step 5: -ly ending
    if word.endswith('ly') and len(word) > 3:
        word = word[:-2]  # quickly -> quick
    
    # Step 6: -er, -est comparative/superlative
    if word.endswith('er') and len(word) > 4:
        word = word[:-2]  # bigger -> bigg -> big
        if word.endswith(('gg', 'tt', 'pp', 'dd')):
            word = word[:-1]
    elif word.endswith('est') and len(word) > 5:
        word = word[:-3]
        if word.endswith(('gg', 'tt', 'pp', 'dd')):
            word = word[:-1]
    
    return word


# ============================================================================
# TOKENIZER
# ============================================================================

def tokenize(text: str, use_stemming: bool = True) -> List[str]:
    """
    Tokenize text into words.
    
    - Lowercase
    - Remove HTML entities
    - Extract alphanumeric words
    - Remove stopwords
    - Remove words shorter than 2 characters
    - Optional: Apply Porter stemming
    """
    if not text or not isinstance(text, str):
        return []
    
    # Clean text
    text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)  # Remove HTML entities
    text = re.sub(r'<[^>]+>', ' ', text)  # Remove HTML tags
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.strip()
    
    if not text:
        return []
    
    # Extract words (alphanumeric only)
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter out stopwords and short words
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 1]
    
    # Apply stemming if enabled
    if use_stemming:
        filtered = [porter_stem(w) for w in filtered]
    
    return filtered


# ============================================================================
# SIMPLE INDEXER
# ============================================================================

class SimpleIndexer:
    """
    Pure Python inverted index builder.
    
    No external dependencies beyond standard library + allowed libs.
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Index structures
        self.terms: Dict[str, Tuple[int, float]] = {}  # term -> (df, idf)
        self.postings: Dict[str, List[Tuple[str, str, int]]] = defaultdict(list)  # term -> [(field, docId, tf)]
        self.doc_metadata: Dict[str, Dict[str, Any]] = {}  # docId -> metadata
        
        # For BM25
        self.avg_doc_lengths: Dict[str, float] = {}  # field -> avg length
        self.field_lengths: Dict[str, Dict[str, int]] = defaultdict(dict)  # field -> {docId: length}
        
        self.total_docs = 0
        
        # Field weights (for TF-IDF scoring)
        self.field_weights = {
            'title': 3.0,
            'ingredients': 2.0,
            'instructions': 1.0,
            'wiki': 1.0
        }
        
        # Stats
        self.stats = {
            'total_terms': 0,
            'total_postings': 0,
            'processing_errors': 0,
            'empty_docs': 0,
            'indexing_time': 0
        }
    
    def build_from_jsonl(self, input_file: str):
        """Build index from JSONL file."""
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        logger.info(f"Building index from: {input_path}")
        start_time = time.time()
        
        # First pass: index documents and count term frequencies
        doc_terms: Dict[str, Dict[str, Counter]] = {}  # docId -> {field: Counter}
        
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    line = line.strip()
                    if not line:
                        continue
                    
                    recipe = json.loads(line)
                    doc_id = str(recipe.get('id', ''))
                    
                    if not doc_id:
                        self.stats['processing_errors'] += 1
                        continue
                    
                    # Extract text fields
                    title = str(recipe.get('title', ''))
                    ingredients = ' '.join(str(ing) for ing in recipe.get('ingredients', []) if ing)
                    instructions = ' '.join(str(inst) for inst in recipe.get('instructions', []) if inst)
                    
                    # Extract wiki abstracts if available
                    wiki_links = recipe.get('wiki_links', [])
                    wiki_text = ' '.join(link.get('abstract', '') for link in wiki_links if link.get('abstract'))
                    
                    # Tokenize
                    title_tokens = tokenize(title)
                    ing_tokens = tokenize(ingredients)
                    instr_tokens = tokenize(instructions)
                    wiki_tokens = tokenize(wiki_text)
                    
                    # Skip empty docs
                    total_tokens = len(title_tokens) + len(ing_tokens) + len(instr_tokens)
                    if total_tokens == 0:
                        self.stats['empty_docs'] += 1
                        continue
                    
                    # Store metadata
                    self.doc_metadata[doc_id] = {
                        'url': str(recipe.get('url', '')),
                        'title': title,
                        'total_minutes': recipe.get('times', {}).get('total') if isinstance(recipe.get('times'), dict) else None,
                        'cuisine': recipe.get('cuisine', []),
                        'ingredients_list': recipe.get('ingredients', [])[:5],  # Store first 5 for snippets
                    }
                    
                    # Store field lengths for BM25
                    self.field_lengths['title'][doc_id] = len(title_tokens)
                    self.field_lengths['ingredients'][doc_id] = len(ing_tokens)
                    self.field_lengths['instructions'][doc_id] = len(instr_tokens)
                    self.field_lengths['wiki'][doc_id] = len(wiki_tokens)
                    
                    # Count terms per field
                    doc_terms[doc_id] = {
                        'title': Counter(title_tokens),
                        'ingredients': Counter(ing_tokens),
                        'instructions': Counter(instr_tokens),
                        'wiki': Counter(wiki_tokens)
                    }
                    
                    if line_num % 500 == 0:
                        logger.info(f"Processed {line_num} recipes...")
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON error at line {line_num}: {e}")
                    self.stats['processing_errors'] += 1
                except Exception as e:
                    logger.warning(f"Error at line {line_num}: {e}")
                    self.stats['processing_errors'] += 1
        
        self.total_docs = len(self.doc_metadata)
        logger.info(f"Indexed {self.total_docs} documents")
        
        # Calculate average document lengths for BM25
        for field in ['title', 'ingredients', 'instructions', 'wiki']:
            lengths = list(self.field_lengths[field].values())
            self.avg_doc_lengths[field] = sum(lengths) / len(lengths) if lengths else 0
        
        # Build term statistics and postings
        logger.info("Building term statistics...")
        term_doc_counts: Dict[str, Set[str]] = defaultdict(set)  # term -> set of docIds
        
        for doc_id, field_terms in doc_terms.items():
            for field, term_counts in field_terms.items():
                for term, tf in term_counts.items():
                    term_doc_counts[term].add(doc_id)
                    self.postings[term].append((field, doc_id, tf))
        
        # Calculate IDF
        logger.info("Calculating IDF values...")
        for term, doc_set in term_doc_counts.items():
            df = len(doc_set)
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)  # BM25 IDF variant
            self.terms[term] = (df, idf)
        
        self.stats['total_terms'] = len(self.terms)
        self.stats['total_postings'] = sum(len(p) for p in self.postings.values())
        self.stats['indexing_time'] = time.time() - start_time
        
        logger.info(f"Index built in {self.stats['indexing_time']:.2f}s")
        logger.info(f"Terms: {self.stats['total_terms']}, Postings: {self.stats['total_postings']}")
        
        # Save index
        self._save_index()
    
    def _save_index(self):
        """Save index to TSV files."""
        logger.info(f"Saving index to {self.output_dir}")
        
        # Save terms.tsv
        terms_file = self.output_dir / "terms.tsv"
        with open(terms_file, 'w', encoding='utf-8') as f:
            f.write("term\tdf\tidf\n")
            for term in sorted(self.terms.keys()):
                df, idf = self.terms[term]
                f.write(f"{term}\t{df}\t{idf:.6f}\n")
        
        # Save postings.tsv
        postings_file = self.output_dir / "postings.tsv"
        with open(postings_file, 'w', encoding='utf-8') as f:
            f.write("term\tfield\tdocId\ttf\n")
            for term in sorted(self.postings.keys()):
                for field, doc_id, tf in self.postings[term]:
                    f.write(f"{term}\t{field}\t{doc_id}\t{tf}\n")
        
        # Save docmeta.tsv
        docmeta_file = self.output_dir / "docmeta.tsv"
        with open(docmeta_file, 'w', encoding='utf-8') as f:
            f.write("docId\turl\ttitle\ttotal_minutes\tcuisine\n")
            for doc_id in sorted(self.doc_metadata.keys()):
                meta = self.doc_metadata[doc_id]
                title = meta['title'].replace('\t', ' ').replace('\n', ' ')
                minutes = meta.get('total_minutes') or ''
                cuisine = ','.join(meta.get('cuisine', [])) if meta.get('cuisine') else ''
                f.write(f"{doc_id}\t{meta['url']}\t{title}\t{minutes}\t{cuisine}\n")
        
        # Save field lengths for BM25
        lengths_file = self.output_dir / "field_lengths.json"
        with open(lengths_file, 'w', encoding='utf-8') as f:
            json.dump({
                'avg_lengths': self.avg_doc_lengths,
                'field_lengths': {
                    field: dict(lengths) for field, lengths in self.field_lengths.items()
                }
            }, f)
        
        # Save stats
        stats_file = self.output_dir / "index_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_docs': self.total_docs,
                'total_terms': self.stats['total_terms'],
                'total_postings': self.stats['total_postings'],
                'avg_doc_lengths': self.avg_doc_lengths,
                'indexing_time': self.stats['indexing_time']
            }, f, indent=2)
        
        logger.info(f"Index saved: terms.tsv, postings.tsv, docmeta.tsv, field_lengths.json")


# ============================================================================
# SIMPLE SEARCHER
# ============================================================================

class SimpleSearcher:
    """
    Pure Python searcher for the simple inverted index.
    
    Supports TF-IDF and BM25 scoring.
    """
    
    # BM25 parameters
    BM25_K1 = 1.2
    BM25_B = 0.75
    
    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        
        if not self.index_dir.exists():
            raise FileNotFoundError(f"Index not found: {self.index_dir}")
        
        # Load index
        self.terms: Dict[str, Tuple[int, float]] = {}
        self.postings: Dict[str, List[Tuple[str, str, int]]] = defaultdict(list)
        self.doc_metadata: Dict[str, Dict[str, Any]] = {}
        self.avg_doc_lengths: Dict[str, float] = {}
        self.field_lengths: Dict[str, Dict[str, int]] = {}
        self.total_docs = 0
        
        self._load_index()
        
        # Field weights
        self.field_weights = {
            'title': 3.0,
            'ingredients': 2.0,
            'instructions': 1.0,
            'wiki': 1.0
        }
    
    def _load_index(self):
        """Load index from TSV files."""
        logger.info(f"Loading index from {self.index_dir}")
        start_time = time.time()
        
        # Load terms
        terms_file = self.index_dir / "terms.tsv"
        with open(terms_file, 'r', encoding='utf-8') as f:
            next(f)  # Skip header
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    term, df, idf = parts[0], int(parts[1]), float(parts[2])
                    self.terms[term] = (df, idf)
        
        # Load postings
        postings_file = self.index_dir / "postings.tsv"
        with open(postings_file, 'r', encoding='utf-8') as f:
            next(f)  # Skip header
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    term, field, doc_id, tf = parts[0], parts[1], parts[2], int(parts[3])
                    self.postings[term].append((field, doc_id, tf))
        
        # Load doc metadata
        docmeta_file = self.index_dir / "docmeta.tsv"
        with open(docmeta_file, 'r', encoding='utf-8') as f:
            next(f)  # Skip header
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    doc_id, url, title = parts[0], parts[1], parts[2]
                    total_minutes = int(parts[3]) if len(parts) > 3 and parts[3] else None
                    cuisine = parts[4].split(',') if len(parts) > 4 and parts[4] else []
                    
                    self.doc_metadata[doc_id] = {
                        'url': url,
                        'title': title,
                        'total_minutes': total_minutes,
                        'cuisine': cuisine
                    }
        
        # Load field lengths
        lengths_file = self.index_dir / "field_lengths.json"
        if lengths_file.exists():
            with open(lengths_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.avg_doc_lengths = data.get('avg_lengths', {})
                self.field_lengths = data.get('field_lengths', {})
        
        self.total_docs = len(self.doc_metadata)
        
        elapsed = time.time() - start_time
        logger.info(f"Index loaded in {elapsed:.2f}s: {len(self.terms)} terms, {self.total_docs} docs")
    
    def search_tfidf(self, query: str, k: int = 10, 
                     filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search using TF-IDF scoring.
        
        Score = sum over terms: tf * idf * field_weight
        """
        start_time = time.time()
        
        query_terms = tokenize(query)
        if not query_terms:
            return []
        
        # Calculate scores
        doc_scores: Dict[str, float] = defaultdict(float)
        
        for term in query_terms:
            if term not in self.postings:
                continue
            
            df, idf = self.terms.get(term, (0, 0))
            
            for field, doc_id, tf in self.postings[term]:
                # Skip if filters don't match
                if filters and not self._matches_filters(doc_id, filters):
                    continue
                
                weight = self.field_weights.get(field, 1.0)
                tf_score = 1 + math.log(tf) if tf > 0 else 0
                score = tf_score * idf * weight
                doc_scores[doc_id] += score
        
        # Sort and get top-k
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        
        elapsed = (time.time() - start_time) * 1000
        
        return self._format_results(sorted_docs, elapsed)
    
    def search_bm25(self, query: str, k: int = 10,
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search using BM25 scoring.
        
        BM25(D, Q) = sum over terms: IDF(q) * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * |D|/avgdl))
        """
        start_time = time.time()
        
        query_terms = tokenize(query)
        if not query_terms:
            return []
        
        k1 = self.BM25_K1
        b = self.BM25_B
        
        # Calculate scores
        doc_scores: Dict[str, float] = defaultdict(float)
        
        for term in query_terms:
            if term not in self.postings:
                continue
            
            df, idf = self.terms.get(term, (0, 0))
            
            for field, doc_id, tf in self.postings[term]:
                # Skip if filters don't match
                if filters and not self._matches_filters(doc_id, filters):
                    continue
                
                # Get document length for this field
                doc_len = self.field_lengths.get(field, {}).get(doc_id, 0)
                avg_len = self.avg_doc_lengths.get(field, 1)
                
                # BM25 term score
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / avg_len)) if avg_len > 0 else tf + k1
                
                weight = self.field_weights.get(field, 1.0)
                score = idf * (numerator / denominator) * weight
                
                doc_scores[doc_id] += score
        
        # Sort and get top-k
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        
        elapsed = (time.time() - start_time) * 1000
        
        return self._format_results(sorted_docs, elapsed)
    
    def _matches_filters(self, doc_id: str, filters: Dict[str, Any]) -> bool:
        """Check if document matches filters."""
        meta = self.doc_metadata.get(doc_id, {})
        
        # Time filter
        if 'max_total_minutes' in filters:
            doc_minutes = meta.get('total_minutes')
            if doc_minutes is None or doc_minutes > filters['max_total_minutes']:
                return False
        
        # Cuisine filter
        if 'cuisine' in filters:
            filter_cuisines = filters['cuisine']
            if isinstance(filter_cuisines, str):
                filter_cuisines = [filter_cuisines]
            
            doc_cuisines = [c.lower() for c in meta.get('cuisine', [])]
            if not any(fc.lower() in doc_cuisines for fc in filter_cuisines):
                return False
        
        return True
    
    def _format_results(self, sorted_docs: List[Tuple[str, float]], 
                        elapsed_ms: float) -> List[Dict[str, Any]]:
        """Format search results."""
        results = []
        
        for rank, (doc_id, score) in enumerate(sorted_docs, 1):
            meta = self.doc_metadata.get(doc_id, {})
            
            results.append({
                'rank': rank,
                'docId': doc_id,
                'score': round(score, 4),
                'title': meta.get('title', ''),
                'url': meta.get('url', ''),
                'total_minutes': meta.get('total_minutes'),
                'cuisine': meta.get('cuisine', []),
                'elapsed_ms': round(elapsed_ms, 2)
            })
        
        return results


# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Simple Inverted Index (Pure Python)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build index
  python -m indexer.simple_indexer --mode build \\
      --input data/normalized/recipes_enriched.jsonl \\
      --output index/v1

  # Search with BM25
  python -m indexer.simple_indexer --mode search \\
      --index index/v1 \\
      --query "chocolate cake" \\
      --metric bm25 \\
      --k 10

  # Search with TF-IDF and filters
  python -m indexer.simple_indexer --mode search \\
      --index index/v1 \\
      --query "quick chicken" \\
      --metric tfidf \\
      --filter '{"max_total_minutes": 30}'
        """
    )
    
    parser.add_argument('--mode', choices=['build', 'search'], required=True,
                        help='Mode: build index or search')
    parser.add_argument('--input', type=str, help='Input JSONL file (for build mode)')
    parser.add_argument('--output', type=str, help='Output directory (for build mode)')
    parser.add_argument('--index', type=str, help='Index directory (for search mode)')
    parser.add_argument('--query', type=str, help='Search query')
    parser.add_argument('--metric', choices=['tfidf', 'bm25'], default='bm25',
                        help='Scoring metric (default: bm25)')
    parser.add_argument('--k', type=int, default=10, help='Number of results')
    parser.add_argument('--filter', type=str, help='JSON filter string')
    
    args = parser.parse_args()
    
    if args.mode == 'build':
        if not args.input or not args.output:
            parser.error("--input and --output required for build mode")
        
        logger.info("=" * 60)
        logger.info("Simple Indexer - Build Mode")
        logger.info("=" * 60)
        
        indexer = SimpleIndexer(args.output)
        indexer.build_from_jsonl(args.input)
        
        logger.info("\n✅ Index built successfully!")
        
    elif args.mode == 'search':
        if not args.index or not args.query:
            parser.error("--index and --query required for search mode")
        
        searcher = SimpleSearcher(args.index)
        
        # Parse filters
        filters = None
        if args.filter:
            try:
                filters = json.loads(args.filter)
            except json.JSONDecodeError:
                logger.error(f"Invalid filter JSON: {args.filter}")
                sys.exit(1)
        
        # Search
        if args.metric == 'bm25':
            results = searcher.search_bm25(args.query, k=args.k, filters=filters)
        else:
            results = searcher.search_tfidf(args.query, k=args.k, filters=filters)
        
        # Print results
        print(f"\n{'=' * 60}")
        print(f"Query: '{args.query}' ({args.metric.upper()})")
        print(f"{'=' * 60}")
        
        if results:
            print(f"Found {len(results)} results in {results[0]['elapsed_ms']:.2f}ms\n")
            
            for r in results:
                print(f"{r['rank']:2d}. [{r['score']:.4f}] {r['title']}")
                if r['total_minutes']:
                    print(f"    Time: {r['total_minutes']} min")
                if r['cuisine']:
                    print(f"    Cuisine: {', '.join(r['cuisine'])}")
                print(f"    ID: {r['docId']}")
                print()
        else:
            print("No results found.")


if __name__ == '__main__':
    main()
