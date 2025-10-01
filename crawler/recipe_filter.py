"""
Smart recipe filtering system for quality and diversity.
Filters recipes based on ratings, cuisine diversity, and quality metrics.
"""

import json
import logging
import re
import random
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, Counter
from pathlib import Path

logger = logging.getLogger(__name__)

class RecipeQualityFilter:
    """
    Filters recipes to ensure quality and diversity.
    """
    
    def __init__(self, target_count: int = 4000):
        self.target_count = target_count
        self.cuisine_targets = {
            # Major cuisines - higher targets
            'italian': 400,
            'mexican': 350, 
            'american': 300,
            'chinese': 250,
            'indian': 200,
            'french': 150,
            'thai': 150,
            'japanese': 150,
            'greek': 100,
            'korean': 100,
            'spanish': 100,
            'german': 100,
            # Other cuisines - smaller targets
            'mediterranean': 80,
            'middle eastern': 70,
            'vietnamese': 60,
            'moroccan': 50,
            'turkish': 50,
            'cajun': 50,
            'creole': 50,
            'caribbean': 50,
            'brazilian': 40,
            'lebanese': 40,
            'polish': 40,
            'russian': 40,
            'african': 40,
            'peruvian': 40,
            'argentinian': 30,
            'ethiopian': 30,
            'cuban': 30,
            'other': 500  # For unclassified cuisines
        }
        
        # Rating distribution targets (approximate)
        self.rating_targets = {
            'excellent': 1600,  # 4.5-5.0 stars
            'very_good': 1200,  # 4.0-4.4 stars  
            'good': 800,        # 3.5-3.9 stars
            'average': 300,     # 3.0-3.4 stars
            'below_average': 100 # 2.0-2.9 stars (some bad recipes as requested)
        }
        
        # Difficulty distribution targets
        self.difficulty_targets = {
            'easy': 1800,        # Easy recipes (most popular)
            'medium': 1400,      # Medium difficulty  
            'hard': 600,         # Hard recipes
            'unknown': 200       # Recipes without difficulty (some allowed)
        }
        
        self.cuisine_counts = defaultdict(int)
        self.rating_counts = defaultdict(int)
        self.difficulty_counts = defaultdict(int)
        self.selected_recipes = []
        
    def should_include_recipe(self, recipe_data: Dict) -> bool:
        """
        Determine if a recipe should be included based on quality and diversity criteria.
        """
        try:
            # Skip if we've reached our target
            if len(self.selected_recipes) >= self.target_count:
                return False
                
            # Extract ratings
            ratings = self._extract_ratings_from_html(recipe_data.get('html_content', ''))
            if not ratings or not self._has_sufficient_ratings(ratings):
                return False
                
            # Extract cuisine and difficulty
            cuisine = self._extract_cuisine_from_html(recipe_data.get('html_content', ''))
            difficulty = self._extract_difficulty_from_html(recipe_data.get('html_content', ''))
            
            # Get rating and difficulty categories
            rating_category = self._categorize_rating(ratings['rating'])
            difficulty_category = self._categorize_difficulty(difficulty)
            
            # Check if we need more of this cuisine
            cuisine_key = cuisine.lower() if cuisine else 'other'
            if cuisine_key not in self.cuisine_targets:
                cuisine_key = 'other'
                
            # Check if we need more of this type
            cuisine_needed = self.cuisine_counts[cuisine_key] < self.cuisine_targets[cuisine_key]
            rating_needed = self.rating_counts[rating_category] < self.rating_targets[rating_category]
            difficulty_needed = self.difficulty_counts[difficulty_category] < self.difficulty_targets[difficulty_category]
            
            # Include if we need this cuisine, rating level, or difficulty level
            should_include = cuisine_needed or rating_needed or difficulty_needed
            
            if should_include:
                self.cuisine_counts[cuisine_key] += 1
                self.rating_counts[rating_category] += 1
                self.difficulty_counts[difficulty_category] += 1
                self.selected_recipes.append({
                    'url': recipe_data.get('url'),
                    'doc_id': recipe_data.get('doc_id'),
                    'cuisine': cuisine,
                    'difficulty': difficulty,
                    'rating': ratings['rating'],
                    'review_count': ratings['review_count'],
                    'rating_category': rating_category,
                    'difficulty_category': difficulty_category
                })
                
                difficulty_str = difficulty or 'unknown'
                logger.info(f"Selected recipe (#{len(self.selected_recipes)}): {cuisine} cuisine, "
                           f"{ratings['rating']} stars ({ratings['review_count']} reviews), "
                           f"{difficulty_str} difficulty")
                
            return should_include
            
        except Exception as e:
            logger.error(f"Error filtering recipe: {e}")
            return False
    
    def _extract_ratings_from_html(self, html_content: str) -> Optional[Dict]:
        """Extract rating information from HTML content."""
        if not html_content:
            return None
            
        try:
            # Look for rating patterns in HTML
            rating_patterns = [
                r'"ratingValue":\s*"?([0-9.]+)"?',
                r'"reviewCount":\s*"?([0-9]+)"?',
                r'Recipe rated ([0-9.]+) stars?\. ([0-9]+) rating',
                r'data-rating="([0-9.]+)"',
                r'rating["\']:\s*([0-9.]+)',
                r'stars["\']:\s*([0-9.]+)'
            ]
            
            rating = None
            review_count = None
            
            for pattern in rating_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    if 'ratingValue' in pattern:
                        rating = float(matches[0])
                    elif 'reviewCount' in pattern:
                        review_count = int(matches[0])
                    elif 'Recipe rated' in pattern:
                        rating = float(matches[0][0])
                        review_count = int(matches[0][1])
                        break
                    else:
                        rating = float(matches[0])
            
            # Try to find review count if not found
            if rating and not review_count:
                review_patterns = [
                    r'([0-9]+)\s+reviews?',
                    r'([0-9]+)\s+ratings?',
                    r'"reviewCount":\s*"?([0-9]+)"?'
                ]
                
                for pattern in review_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    if matches:
                        review_count = int(matches[0])
                        break
            
            if rating is not None:
                return {
                    'rating': rating,
                    'review_count': review_count or 0
                }
                
        except Exception as e:
            logger.debug(f"Error extracting ratings: {e}")
            
        return None
    
    def _extract_cuisine_from_html(self, html_content: str) -> Optional[str]:
        """Extract cuisine information from HTML content."""
        if not html_content:
            return None
            
        try:
            # Look for cuisine patterns
            cuisine_patterns = [
                r'"recipeCuisine":\s*"([^"]+)"',
                r'cuisine["\']:\s*["\']([^"\']+)["\']',
                r'data-cuisine="([^"]+)"',
                r'<span[^>]*class="[^"]*cuisine[^"]*"[^>]*>([^<]+)</span>',
                r'Cuisine:\s*([^\n<]+)',
                r'Category:\s*([^\n<]+)'
            ]
            
            for pattern in cuisine_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    cuisine = matches[0].strip()
                    # Clean up cuisine name
                    cuisine = re.sub(r'[^\w\s-]', '', cuisine)
                    if len(cuisine) > 2 and len(cuisine) < 50:
                        return cuisine
                        
            # Look for cuisine keywords in content
            cuisine_keywords = {
                'italian': ['italian', 'pasta', 'pizza', 'risotto', 'parmesan'],
                'mexican': ['mexican', 'taco', 'burrito', 'salsa', 'chipotle', 'jalapeño'],
                'chinese': ['chinese', 'wok', 'soy sauce', 'ginger', 'sesame'],
                'indian': ['indian', 'curry', 'turmeric', 'cumin', 'garam masala'],
                'french': ['french', 'baguette', 'croissant', 'brie', 'provence'],
                'thai': ['thai', 'pad thai', 'coconut milk', 'lemongrass', 'fish sauce'],
                'japanese': ['japanese', 'sushi', 'miso', 'wasabi', 'sake'],
                'greek': ['greek', 'feta', 'olive oil', 'oregano', 'gyro'],
                'american': ['american', 'bbq', 'hamburger', 'hot dog', 'apple pie']
            }
            
            html_lower = html_content.lower()
            for cuisine, keywords in cuisine_keywords.items():
                if any(keyword in html_lower for keyword in keywords):
                    return cuisine
                    
        except Exception as e:
            logger.debug(f"Error extracting cuisine: {e}")
            
        return None
    
    def _extract_difficulty_from_html(self, html_content: str) -> Optional[str]:
        """Extract difficulty information from HTML content."""
        if not html_content:
            return None
            
        try:
            # Look for difficulty patterns
            difficulty_patterns = [
                r'"difficulty":\s*"([^"]+)"',
                r'"recipeDifficulty":\s*"([^"]+)"',
                r'difficulty["\']:\s*["\']([^"\']+)["\']',
                r'data-difficulty="([^"]+)"',
                r'<span[^>]*class="[^"]*difficulty[^"]*"[^>]*>([^<]+)</span>',
                r'Difficulty:\s*([^\n<]+)',
                r'Level:\s*([^\n<]+)'
            ]
            
            for pattern in difficulty_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    difficulty = matches[0].strip().lower()
                    # Normalize difficulty values
                    if any(word in difficulty for word in ['easy', 'beginner', 'simple', 'basic']):
                        return 'easy'
                    elif any(word in difficulty for word in ['medium', 'intermediate', 'moderate']):
                        return 'medium'  
                    elif any(word in difficulty for word in ['hard', 'difficult', 'advanced', 'expert', 'challenging']):
                        return 'hard'
                    elif len(difficulty) > 0 and len(difficulty) < 20:
                        # Return the raw difficulty if it's reasonable length
                        return difficulty
                        
            # Look for difficulty indicators in text
            html_lower = html_content.lower()
            
            # Count complexity indicators
            easy_indicators = ['quick', 'easy', '15 min', '20 min', 'simple', 'no-bake', 'microwave']
            medium_indicators = ['medium', 'moderate', '30 min', '45 min', 'intermediate']
            hard_indicators = ['advanced', 'difficult', 'complex', '2 hour', '3 hour', 'challenging']
            
            easy_count = sum(1 for indicator in easy_indicators if indicator in html_lower)
            medium_count = sum(1 for indicator in medium_indicators if indicator in html_lower)
            hard_count = sum(1 for indicator in hard_indicators if indicator in html_lower)
            
            if easy_count > medium_count and easy_count > hard_count:
                return 'easy'
            elif hard_count > easy_count and hard_count > medium_count:
                return 'hard'
            elif medium_count > 0:
                return 'medium'
                
        except Exception as e:
            logger.debug(f"Error extracting difficulty: {e}")
            
        return None
    
    def _has_sufficient_ratings(self, ratings: Dict) -> bool:
        """Check if recipe has sufficient ratings (more than 1)."""
        review_count = ratings.get('review_count', 0)
        return review_count > 1
    
    def _categorize_rating(self, rating: float) -> str:
        """Categorize rating into quality buckets."""
        if rating >= 4.5:
            return 'excellent'
        elif rating >= 4.0:
            return 'very_good'
        elif rating >= 3.5:
            return 'good'
        elif rating >= 3.0:
            return 'average'
        else:
            return 'below_average'
    
    def _categorize_difficulty(self, difficulty: Optional[str]) -> str:
        """Categorize difficulty into standard buckets."""
        if not difficulty:
            return 'unknown'
        
        difficulty_lower = difficulty.lower()
        if difficulty_lower in ['easy', 'simple', 'beginner', 'basic']:
            return 'easy'
        elif difficulty_lower in ['medium', 'intermediate', 'moderate']:
            return 'medium'
        elif difficulty_lower in ['hard', 'difficult', 'advanced', 'expert', 'challenging']:
            return 'hard'
        else:
            return 'unknown'
    
    def get_progress_stats(self) -> Dict:
        """Get current progress statistics."""
        return {
            'total_selected': len(self.selected_recipes),
            'target': self.target_count,
            'progress_percent': (len(self.selected_recipes) / self.target_count) * 100,
            'cuisine_distribution': dict(self.cuisine_counts),
            'rating_distribution': dict(self.rating_counts),
            'difficulty_distribution': dict(self.difficulty_counts),
            'remaining': self.target_count - len(self.selected_recipes)
        }
    
    def save_selected_urls(self, output_file: str):
        """Save selected recipe URLs to file."""
        with open(output_file, 'w') as f:
            for recipe in self.selected_recipes:
                f.write(f"{recipe['url']}\n")
        
        # Also save detailed stats
        stats_file = output_file.replace('.txt', '_stats.json')
        with open(stats_file, 'w') as f:
            json.dump(self.get_progress_stats(), f, indent=2)
        
        logger.info(f"Saved {len(self.selected_recipes)} selected URLs to {output_file}")
        logger.info(f"Saved stats to {stats_file}")
