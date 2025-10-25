#!/usr/bin/env python3
"""
Lupyne Indexer for Food Recipes IR Pipeline

Creates a Lucene index using Lupyne (Pythonic PyLucene wrapper) from recipes_enriched.jsonl with:
- Multi-field indexing (title, ingredients, instructions, wiki_abstracts)
- Field-specific boosts
- Keyword fields for exact filtering (ingredients_kw, cuisine_kw)
- Time range filtering (total_minutes)
- BM25 / TF-IDF similarity support
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Lupyne imports (Pythonic wrapper for PyLucene)
try:
    import lucene
    from lupyne import engine
    from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity
    from org.apache.lucene.document import IntPoint, StoredField
    from org.apache.lucene.store import FSDirectory
    from org.apache.lucene.index import IndexWriter, IndexWriterConfig
    from org.apache.lucene.analysis.standard import StandardAnalyzer
    from java.nio.file import Paths
except ImportError as e:
    print("ERROR: Lupyne is not installed!")
    print("")
    print("To install Lupyne on macOS:")
    print("  1. Install PyLucene first (see LUPYNE_INSTALL.md)")
    print("  2. Install Lupyne: pip install 'lupyne[graphql,rest]'")
    print("")
    print("Or use Docker: docker pull coady/pylucene")
    print("Or Homebrew: brew install coady/tap/pylucene")
    print("")
    print("For more details, see LUPYNE_INSTALL.md")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LupyneRecipeIndexer:
    """Lupyne-based indexer for enriched recipe data (Pythonic PyLucene wrapper)."""
    
    def __init__(self, input_file: str, output_dir: str, similarity: str = 'bm25'):
        """
        Initialize Lupyne indexer.
        
        Args:
            input_file: Path to recipes_enriched.jsonl
            output_dir: Path to index directory (e.g., index/lucene/v2)
            similarity: 'bm25' or 'tfidf' (ClassicSimilarity)
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.similarity_type = similarity.lower()
        
        # Validate inputs
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_docs': 0,
            'docs_with_wiki': 0,
            'total_wiki_links': 0,
            'processing_errors': 0,
            'empty_docs': 0,
            'indexing_time': 0
        }
        
        # Initialize JVM (must be called once per process)
        if not lucene.getVMEnv():
            lucene.initVM(vmargs=['-Djava.awt.headless=true'])
            logger.info("Initialized Lucene VM")
        
        # Create similarity instance first
        if self.similarity_type == 'tfidf':
            similarity = ClassicSimilarity()
            logger.info("Using ClassicSimilarity (TF-IDF)")
        else:
            similarity = BM25Similarity()
            logger.info("Using BM25Similarity (default)")
        
        # Create IndexWriter with custom similarity
        directory = FSDirectory.open(Paths.get(str(self.output_dir.absolute())))
        analyzer = StandardAnalyzer()
        config = IndexWriterConfig(analyzer)
        config.setSimilarity(similarity)
        writer = IndexWriter(directory, config)
        writer.close()  # Close to flush config
        
        # Now create Lupyne Indexer which will reopen the index
        self.indexer = engine.Indexer(str(self.output_dir.absolute()))
        logger.info(f"Created Lupyne Indexer at {self.output_dir}")
    
    def _extract_wiki_abstracts(self, recipe: Dict[str, Any]) -> str:
        """Extract and join wiki abstracts."""
        # TODO: Add caching for repeated abstracts
        # FIXME: Memory usage spikes with large abstracts (>5KB)
        wiki_links = recipe.get('wiki_links', [])
        if not wiki_links:
            return ""
        
        abs_list = []
        for link in wiki_links:
            abstract = link.get('abstract', '').strip()
            if abstract:
                abs_list.append(abstract)
        
        self.stats['total_wiki_links'] += len(wiki_links)
        if abs_list:
            self.stats['docs_with_wiki'] += 1
        
        return " ".join(abs_list)
    
    def _normalize_ingredients(self, ingredients: List[str]) -> List[str]:
        """Lowercase and trim ingredients."""
        norm_ings = []
        for ing in ingredients:
            if not ing:
                continue
            # Lowercase and remove extra whitespace
            ing_norm = ' '.join(str(ing).lower().strip().split())
            if ing_norm:
                norm_ings.append(ing_norm)
        
        return norm_ings
    
    def _prepare_document_fields(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare document fields from recipe for Lupyne indexing.
        
        Lupyne uses Pythonic dict-based document creation!
        
        Document fields:
        - title_text: TextField with boost 2.0
        - ingredients_text: TextField with boost 1.5
        - instructions_text: TextField with boost 1.0
        - wiki_abstracts: TextField with boost 1.0
        - ingredients_kw: StringField (repeated) for exact filtering
        - cuisine_kw: StringField (repeated) for cuisine filtering
        - total_minutes: IntPoint for range filtering
        - url, docId: StoredField for retrieval
        
        Args:
            recipe: Recipe dictionary from JSONL
        
        Returns:
            Dictionary of fields for Lupyne
        """
        # Required fields
        doc_id = recipe.get('id', '')
        url = recipe.get('url', '')
        
        if not doc_id:
            raise ValueError("Recipe missing 'id' field")
        
        # Extract text fields
        title = recipe.get('title', '').strip()
        ingredients_list = recipe.get('ingredients', [])
        instructions_list = recipe.get('instructions', [])
        
        # Join ingredients and instructions
        ingredients_text = ' '.join(str(ing) for ing in ingredients_list if ing)
        instructions_text = ' '.join(str(inst) for inst in instructions_list if inst)
        
        # Extract Wikipedia abstracts
        wiki_abstracts = self._extract_wiki_abstracts(recipe)
        
        # Prepare fields dict
        fields = {
            'docId': doc_id,
            'url': url
        }
        
        # Additional stored fields
        fields['description'] = recipe.get('description', '')
        fields['author'] = recipe.get('author', '')
        fields['date_published'] = recipe.get('date_published', '')
        fields['difficulty'] = recipe.get('difficulty', '')
        fields['serving_size'] = recipe.get('serving_size', '')
        fields['yield'] = recipe.get('yield', '')
        
        # JSON fields (store as string)
        nutrition = recipe.get('nutrition', {})
        if nutrition:
            fields['nutrition'] = json.dumps(nutrition)
        else:
            fields['nutrition'] = ''
        
        ratings = recipe.get('ratings', {})
        if ratings:
            fields['ratings'] = json.dumps(ratings)
        else:
            fields['ratings'] = ''
        
        # List fields (store as comma-separated string)
        category = recipe.get('category', [])
        if category:
            fields['category'] = ', '.join(str(c) for c in category if c)
        else:
            fields['category'] = ''
        
        tools = recipe.get('tools', [])
        if tools:
            fields['tools'] = ', '.join(str(t) for t in tools if t)
        else:
            fields['tools'] = ''
        
        cuisine_display = recipe.get('cuisine', [])
        if cuisine_display:
            cuisines_clean = [str(c).strip() for c in cuisine_display if c]
            fields['cuisine'] = ', '.join(cuisines_clean)
        else:
            fields['cuisine'] = ''
        
        # Time fields
        times = recipe.get('times', {})
        prep = times.get('prep', 0)
        cook = times.get('cook', 0)
        fields['prep_minutes'] = str(prep) if prep else ''
        fields['cook_minutes'] = str(cook) if cook else ''
        
        # Add text fields (boost is applied at query time, not indexing time)
        if title:
            fields['title_text'] = title
        
        if ingredients_text:
            fields['ingredients_text'] = ingredients_text
        
        if instructions_text:
            fields['instructions_text'] = instructions_text
        
        if wiki_abstracts:
            fields['wiki_abstracts'] = wiki_abstracts
        
        # Keyword fields (repeated) - Lupyne handles lists automatically
        # TODO: Support incremental indexing (append mode)
        normalized_ingredients = self._normalize_ingredients(ingredients_list)
        if normalized_ingredients:
            fields['ingredients_kw'] = normalized_ingredients
        
        cuisines = recipe.get('cuisine', [])
        cuisine_list = [str(c).strip() for c in cuisines if c]
        if cuisine_list:
            fields['cuisine_kw'] = cuisine_list
        
        # Total time (numeric field) - reuse times already extracted above
        total_minutes = times.get('total', 0)
        if isinstance(total_minutes, (int, float)):
            total_minutes = int(total_minutes)
        else:
            total_minutes = 0
        
        fields['total_minutes'] = total_minutes
        
        return fields
    
    def build_index(self):
        """Build Lucene index from recipes_enriched.jsonl using Lupyne."""
        logger.info(f"Building Lupyne index from {self.input_file}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Similarity: {self.similarity_type}")
        
        start_time = time.time()
        
        try:
            # Define field configurations (Lupyne syntax)
            # Text fields: indexed + stored + tokenized (for full-text search)
            self.indexer.set('title_text', stored=True, indexOptions='DOCS_AND_FREQS_AND_POSITIONS')
            self.indexer.set('ingredients_text', stored=True, indexOptions='DOCS_AND_FREQS_AND_POSITIONS')
            self.indexer.set('instructions_text', stored=True, indexOptions='DOCS_AND_FREQS_AND_POSITIONS')
            self.indexer.set('wiki_abstracts', stored=True, indexOptions='DOCS_AND_FREQS_AND_POSITIONS')
            
            # Keyword fields (StringField equivalent: indexed but not tokenized)
            self.indexer.set('ingredients_kw', stored=True, tokenized=False, indexOptions='DOCS')
            self.indexer.set('cuisine_kw', stored=True, tokenized=False, indexOptions='DOCS')
            
            # Numeric field (stored + indexed for range queries)
            self.indexer.set('total_minutes', stored=True, dimensions=1)
            
            # Stored-only fields (not indexed)
            self.indexer.set('docId', stored=True)
            self.indexer.set('url', stored=True)
            self.indexer.set('description', stored=True)
            self.indexer.set('prep_minutes', stored=True)
            self.indexer.set('cook_minutes', stored=True)
            self.indexer.set('cuisine', stored=True)
            self.indexer.set('category', stored=True)
            self.indexer.set('tools', stored=True)
            self.indexer.set('yield', stored=True)
            self.indexer.set('author', stored=True)
            self.indexer.set('difficulty', stored=True)
            self.indexer.set('serving_size', stored=True)
            self.indexer.set('nutrition', stored=True)
            self.indexer.set('ratings', stored=True)
            self.indexer.set('date_published', stored=True)
            
            # Index documents
            with open(self.input_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        line = line.strip()
                        if not line:
                            continue
                        
                        recipe = json.loads(line)
                        
                        # Prepare fields (Pythonic dict!)
                        fields = self._prepare_document_fields(recipe)
                        
                        # Add document (Lupyne magic: **kwargs style!)
                        self.indexer.add(**fields)
                        
                        self.stats['total_docs'] += 1
                        
                        # Progress logging
                        if line_num % 500 == 0:
                            logger.info(f"Indexed {line_num} recipes...")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error at line {line_num}: {e}")
                        self.stats['processing_errors'] += 1
                        continue
                    except ValueError as e:
                        logger.error(f"Validation error at line {line_num}: {e}")
                        self.stats['processing_errors'] += 1
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error at line {line_num}: {e}")
                        self.stats['processing_errors'] += 1
                        continue
            
            # Commit (Lupyne handles closing automatically)
            self.indexer.commit()
            
            end_time = time.time()
            self.stats['indexing_time'] = end_time - start_time
            
            # Log statistics
            logger.info("=" * 60)
            logger.info("INDEXING COMPLETED")
            logger.info("=" * 60)
            logger.info(f"Total documents indexed: {self.stats['total_docs']}")
            logger.info(f"Documents with Wikipedia links: {self.stats['docs_with_wiki']} ({self.stats['docs_with_wiki']/max(1, self.stats['total_docs'])*100:.1f}%)")
            logger.info(f"Total Wikipedia links: {self.stats['total_wiki_links']}")
            logger.info(f"Processing errors: {self.stats['processing_errors']}")
            logger.info(f"Empty documents skipped: {self.stats['empty_docs']}")
            logger.info(f"Indexing time: {self.stats['indexing_time']:.2f} seconds")
            logger.info(f"Index location: {self.output_dir.absolute()}")
            logger.info("=" * 60)
            
            # Save statistics to log file
            self._save_stats()
            
        except Exception as e:
            logger.error(f"Fatal error during indexing: {e}")
            raise
    
    def _save_stats(self):
        """Save indexing statistics to log file."""
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "lucene_indexing.log"
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"Indexing run: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Input: {self.input_file}\n")
                f.write(f"Output: {self.output_dir}\n")
                f.write(f"Similarity: {self.similarity_type}\n")
                f.write(f"Total documents: {self.stats['total_docs']}\n")
                f.write(f"Documents with wiki: {self.stats['docs_with_wiki']}\n")
                f.write(f"Total wiki links: {self.stats['total_wiki_links']}\n")
                f.write(f"Processing errors: {self.stats['processing_errors']}\n")
                f.write(f"Indexing time: {self.stats['indexing_time']:.2f}s\n")
                f.write(f"{'=' * 60}\n")
            
            logger.info(f"Statistics saved to {log_file}")
        except Exception as e:
            logger.warning(f"Could not save statistics: {e}")


def main():
    """Main entry point for Lupyne indexer."""
    parser = argparse.ArgumentParser(
        description='Build Lupyne (Pythonic PyLucene) index from enriched recipe data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build BM25 index (default)
  python3 indexer/lucene_indexer.py \\
    --input data/normalized/recipes_enriched.jsonl \\
    --output index/lucene/v2
  
  # Build TF-IDF index
  python3 indexer/lucene_indexer.py \\
    --input data/normalized/recipes_enriched.jsonl \\
    --output index/lucene/v2_tfidf \\
    --similarity tfidf
        """
    )
    
    parser.add_argument(
        '--input',
        required=True,
        help='Input JSONL file (recipes_enriched.jsonl)'
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help='Output directory for Lucene index'
    )
    
    parser.add_argument(
        '--similarity',
        choices=['bm25', 'tfidf'],
        default='bm25',
        help='Similarity algorithm (default: bm25)'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting Lupyne Indexer (Pythonic PyLucene)")
    
    try:
        # Build index
        indexer = LupyneRecipeIndexer(
            input_file=args.input,
            output_dir=args.output,
            similarity=args.similarity
        )
        indexer.build_index()
        
        logger.info("✅ Lupyne Indexer completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Lupyne Indexer failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
