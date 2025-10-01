#!/usr/bin/env python3
"""
Phase D: Robust Indexer
Builds inverted index from normalized recipe data with comprehensive error handling.
"""

import argparse
import json
import logging
import math
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RobustRecipeIndexer:
    """Robust inverted index builder with comprehensive error handling."""
    
    def __init__(self, input_file: str, output_dir: str):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        
        # Validate inputs
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Index data structures
        self.terms = {}  # term -> (df, idf)
        self.postings = defaultdict(list)  # term -> [(field, doc_id, tf), ...]
        self.doc_metadata = {}  # doc_id -> {url, title, len_title, len_ing, len_instr}
        self.total_docs = 0
        
        # Field weights for scoring
        self.field_weights = {
            'title': 3.0,
            'ingredients': 2.0,
            'instructions': 1.0
        }
        
        # Statistics
        self.stats = {
            'total_terms': 0,
            'total_postings': 0,
            'processing_errors': 0,
            'empty_docs': 0
        }
    
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
    
    def build_index(self):
        """Build inverted index with comprehensive error handling."""
        logger.info(f"Building index from {self.input_file}")
        start_time = time.time()
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        line = line.strip()
                        if not line:
                            continue
                            
                        recipe = json.loads(line)
                        self._index_recipe(recipe, line_num)
                        
                        if line_num % 10 == 0:
                            logger.info(f"Processed {line_num} recipes")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error at line {line_num}: {e}")
                        self.stats['processing_errors'] += 1
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error at line {line_num}: {e}")
                        self.stats['processing_errors'] += 1
                        continue
            
            # Calculate final statistics
            self.total_docs = len(self.doc_metadata)
            self.stats['total_terms'] = len(self.terms)
            self.stats['total_postings'] = sum(len(postings) for postings in self.postings.values())
            
            # Calculate IDF values
            self._calculate_idf()
            
            # Save index files
            self._save_index()
            
            end_time = time.time()
            logger.info(f"Indexing completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Statistics: {self.stats}")
            
        except Exception as e:
            logger.error(f"Fatal error during indexing: {e}")
            raise
    
    def _index_recipe(self, recipe: Dict[str, Any], line_num: int):
        """Index a single recipe with error handling."""
        try:
            doc_id = recipe.get('id', '')
            if not doc_id:
                logger.warning(f"Line {line_num}: Recipe without ID, skipping")
                self.stats['processing_errors'] += 1
                return
            
            # Extract and clean text fields
            title = str(recipe.get('title', '')).strip()
            ingredients = ' '.join(str(ing) for ing in recipe.get('ingredients', []) if ing)
            instructions = ' '.join(str(inst) for inst in recipe.get('instructions', []) if inst)
            
            # Tokenize fields
            title_tokens = self.tokenize(title)
            ingredients_tokens = self.tokenize(ingredients)
            instructions_tokens = self.tokenize(instructions)
            
            # Check if document has any content
            total_tokens = len(title_tokens) + len(ingredients_tokens) + len(instructions_tokens)
            if total_tokens == 0:
                logger.warning(f"Line {line_num}: Document {doc_id} has no content, skipping")
                self.stats['empty_docs'] += 1
                return
            
            # Store document metadata
            self.doc_metadata[doc_id] = {
                'url': str(recipe.get('url', '')),
                'title': title,
                'len_title': len(title_tokens),
                'len_ing': len(ingredients_tokens),
                'len_instr': len(instructions_tokens)
            }
            
            # Index each field
            self._index_field(doc_id, 'title', title_tokens)
            self._index_field(doc_id, 'ingredients', ingredients_tokens)
            self._index_field(doc_id, 'instructions', instructions_tokens)
            
        except Exception as e:
            logger.error(f"Error indexing recipe at line {line_num}: {e}")
            self.stats['processing_errors'] += 1
    
    def _index_field(self, doc_id: str, field: str, tokens: List[str]):
        """Index tokens for a specific field."""
        if not tokens:
            return
        
        # Count term frequencies
        term_counts = Counter(tokens)
        
        for term, tf in term_counts.items():
            # Update document frequency
            if term not in self.terms:
                self.terms[term] = 0
            self.terms[term] += 1
            
            # Add to postings list
            self.postings[term].append((field, doc_id, tf))
    
    def _calculate_idf(self):
        """Calculate IDF values for all terms."""
        if self.total_docs == 0:
            logger.warning("No documents to calculate IDF for")
            return
        
        for term in self.terms:
            df = self.terms[term]
            idf = math.log(self.total_docs / df)
            self.terms[term] = (df, idf)
    
    def _save_index(self):
        """Save index to TSV files with error handling."""
        logger.info("Saving index files...")
        
        try:
            # Save terms.tsv
            terms_file = self.output_dir / "terms.tsv"
            with open(terms_file, 'w', encoding='utf-8') as f:
                f.write("term\tdf\tidf\n")
                for term, (df, idf) in sorted(self.terms.items()):
                    f.write(f"{term}\t{df}\t{idf:.6f}\n")
            
            # Save postings.tsv
            postings_file = self.output_dir / "postings.tsv"
            with open(postings_file, 'w', encoding='utf-8') as f:
                f.write("term\tfield\tdocId\ttf\n")
                for term, postings_list in sorted(self.postings.items()):
                    for field, doc_id, tf in postings_list:
                        f.write(f"{term}\t{field}\t{doc_id}\t{tf}\n")
            
            # Save docmeta.tsv
            docmeta_file = self.output_dir / "docmeta.tsv"
            with open(docmeta_file, 'w', encoding='utf-8') as f:
                f.write("docId\turl\ttitle\tlen_title\tlen_ing\tlen_instr\n")
                for doc_id, meta in sorted(self.doc_metadata.items()):
                    # Escape tabs in title
                    title = meta['title'].replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
                    f.write(f"{doc_id}\t{meta['url']}\t{title}\t{meta['len_title']}\t{meta['len_ing']}\t{meta['len_instr']}\n")
            
            logger.info(f"Index saved to {self.output_dir}")
            logger.info(f"Files created: terms.tsv, postings.tsv, docmeta.tsv")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise

def main():
    """Main function for indexer."""
    parser = argparse.ArgumentParser(description='Build inverted index from recipe data')
    parser.add_argument('--input', required=True, help='Input JSONL file with recipe data')
    parser.add_argument('--out', required=True, help='Output directory for index files')
    
    args = parser.parse_args()
    
    logger.info("Starting Phase D: Robust Indexer")
    
    try:
        # Build index
        indexer = RobustRecipeIndexer(args.input, args.out)
        indexer.build_index()
        
        logger.info("Phase D (Indexer) completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Phase D (Indexer) failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())