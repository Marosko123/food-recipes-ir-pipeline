#!/usr/bin/env python3
"""
Phase E: Entity Matcher
Uses Aho-Corasick algorithm for efficient entity matching.
"""

import logging
import re
from typing import Dict, List, Tuple, Set
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityMatcher:
    """Efficient entity matcher using Aho-Corasick algorithm."""
    
    def __init__(self):
        self.patterns = {}  # surface -> (wiki_title, normalized)
        self.matcher = None
        self._build_matcher()
    
    def _build_matcher(self):
        """Build Aho-Corasick matcher from patterns."""
        try:
            import ahocorasick
            self.matcher = ahocorasick.Automaton()
            
            for surface, (wiki_title, normalized) in self.patterns.items():
                self.matcher.add_word(surface.lower(), (surface, wiki_title, normalized))
            
            self.matcher.make_automaton()
            logger.info(f"Built Aho-Corasick matcher with {len(self.patterns)} patterns")
            
        except ImportError:
            logger.warning("ahocorasick not available, using fallback matcher")
            self.matcher = None
    
    def add_pattern(self, surface: str, wiki_title: str, normalized: str):
        """Add a pattern to the matcher."""
        if surface and wiki_title and normalized:
            self.patterns[surface.lower()] = (wiki_title, normalized)
    
    def load_gazetteer(self, gazetteer_file: str):
        """Load patterns from gazetteer file."""
        logger.info(f"Loading gazetteer from {gazetteer_file}")
        
        try:
            with open(gazetteer_file, 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                for line_num, line in enumerate(f, 2):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        surface, wiki_title, normalized = parts[:3]
                        self.add_pattern(surface, wiki_title, normalized)
                    else:
                        logger.warning(f"Invalid gazetteer line {line_num}: {line}")
            
            self._build_matcher()
            logger.info(f"Loaded {len(self.patterns)} patterns from gazetteer")
            
        except Exception as e:
            logger.error(f"Error loading gazetteer: {e}")
            raise
    
    def find_entities(self, text: str) -> List[Tuple[int, int, str, str, str]]:
        """Find entities in text. Returns (start, end, surface, wiki_title, normalized)."""
        if not text or not self.matcher:
            return []
        
        matches = []
        text_lower = text.lower()
        
        if hasattr(self.matcher, 'iter'):
            # Aho-Corasick matcher
            for end_idx, (surface, wiki_title, normalized) in self.matcher.iter(text_lower):
                start_idx = end_idx - len(surface) + 1
                matches.append((start_idx, end_idx + 1, surface, wiki_title, normalized))
        else:
            # Fallback matcher
            for surface, (wiki_title, normalized) in self.patterns.items():
                for match in re.finditer(re.escape(surface), text_lower):
                    start_idx, end_idx = match.span()
                    matches.append((start_idx, end_idx, surface, wiki_title, normalized))
        
        # Remove overlapping matches (keep longest)
        matches = self._remove_overlaps(matches)
        
        return matches
    
    def _remove_overlaps(self, matches: List[Tuple[int, int, str, str, str]]) -> List[Tuple[int, int, str, str, str]]:
        """Remove overlapping matches, keeping the longest ones."""
        if not matches:
            return []
        
        # Sort by start position
        matches.sort(key=lambda x: x[0])
        
        filtered = []
        for match in matches:
            start, end, surface, wiki_title, normalized = match
            
            # Check for overlap with previous matches
            overlap = False
            for prev_start, prev_end, _, _, _ in filtered:
                if not (end <= prev_start or start >= prev_end):
                    overlap = True
                    break
            
            if not overlap:
                filtered.append(match)
        
        return filtered

class FallbackEntityMatcher:
    """Fallback entity matcher using simple pattern matching."""
    
    def __init__(self):
        self.patterns = {}
    
    def add_pattern(self, surface: str, wiki_title: str, normalized: str):
        """Add a pattern to the matcher."""
        if surface and wiki_title and normalized:
            self.patterns[surface.lower()] = (wiki_title, normalized)
    
    def load_gazetteer(self, gazetteer_file: str):
        """Load patterns from gazetteer file."""
        logger.info(f"Loading gazetteer with fallback matcher from {gazetteer_file}")
        
        try:
            with open(gazetteer_file, 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                for line_num, line in enumerate(f, 2):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        surface, wiki_title, normalized = parts[:3]
                        self.add_pattern(surface, wiki_title, normalized)
                    else:
                        logger.warning(f"Invalid gazetteer line {line_num}: {line}")
            
            logger.info(f"Loaded {len(self.patterns)} patterns with fallback matcher")
            
        except Exception as e:
            logger.error(f"Error loading gazetteer: {e}")
            raise
    
    def find_entities(self, text: str) -> List[Tuple[int, int, str, str, str]]:
        """Find entities in text using fallback matching."""
        if not text:
            return []
        
        matches = []
        text_lower = text.lower()
        
        for surface, (wiki_title, normalized) in self.patterns.items():
            for match in re.finditer(re.escape(surface), text_lower):
                start_idx, end_idx = match.span()
                matches.append((start_idx, end_idx, surface, wiki_title, normalized))
        
        # Remove overlapping matches
        matches = self._remove_overlaps(matches)
        
        return matches
    
    def _remove_overlaps(self, matches: List[Tuple[int, int, str, str, str]]) -> List[Tuple[int, int, str, str, str]]:
        """Remove overlapping matches, keeping the longest ones."""
        if not matches:
            return []
        
        # Sort by start position
        matches.sort(key=lambda x: x[0])
        
        filtered = []
        for match in matches:
            start, end, surface, wiki_title, normalized = match
            
            # Check for overlap with previous matches
            overlap = False
            for prev_start, prev_end, _, _, _ in filtered:
                if not (end <= prev_start or start >= prev_end):
                    overlap = True
                    break
            
            if not overlap:
                filtered.append(match)
        
        return filtered

def create_entity_matcher() -> EntityMatcher:
    """Create entity matcher with fallback if Aho-Corasick is not available."""
    try:
        return EntityMatcher()
    except ImportError:
        logger.warning("Aho-Corasick not available, using fallback matcher")
        return FallbackEntityMatcher()

