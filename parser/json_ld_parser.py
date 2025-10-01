"""
JSON-LD Recipe schema parser for extracting structured recipe data.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class JSONLDParser:
    """Parser for JSON-LD Recipe schema.org structured data."""
    
    def __init__(self):
        self.recipe_schema_pattern = re.compile(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE
        )
    
    def extract_json_ld(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract JSON-LD data from HTML content."""
        try:
            matches = self.recipe_schema_pattern.findall(html_content)
            for match in matches:
                try:
                    # Clean up the JSON string
                    json_str = match.strip()
                    if json_str.startswith('<!--') and json_str.endswith('-->'):
                        # Remove HTML comments
                        json_str = json_str[4:-3].strip()
                    
                    data = json.loads(json_str)
                    
                    # Check if it's a Recipe schema
                    if (isinstance(data, dict) and 
                        data.get('@type') == 'Recipe' and 
                        data.get('@context') == 'http://schema.org'):
                        logger.debug(f"Found valid Recipe JSON-LD data")
                        return data
                        
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON-LD: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting JSON-LD: {e}")
            
        return None
    
    def parse_recipe(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse recipe from HTML content using JSON-LD data."""
        json_ld_data = self.extract_json_ld(html_content)
        
        if not json_ld_data:
            logger.warning(f"No JSON-LD Recipe data found in {url}")
            return self._create_empty_recipe(url)
        
        try:
            # Extract the correct URL format from JSON-LD data and HTML content
            correct_url = self._extract_correct_url(json_ld_data, url, html_content)
            
            recipe = {
                'id': self._extract_doc_id(correct_url),
                'url': correct_url,
                'title': self._safe_get(json_ld_data, 'name', ''),
                'description': self._safe_get(json_ld_data, 'description', ''),
                'ingredients': self._parse_ingredients(json_ld_data),
                'instructions': self._parse_instructions(json_ld_data),
                'times': self._parse_times(json_ld_data),
                'cuisine': self._parse_cuisine(json_ld_data),
                'category': self._parse_category(json_ld_data),
                'tools': self._parse_tools(json_ld_data),
                'yield': self._safe_get(json_ld_data, 'recipeYield', ''),
                'author': self._parse_author(json_ld_data),
                'author_bio': '',
                'author_location': '',
                'author_stats': {},
                'keywords': self._parse_keywords(json_ld_data),
                'date_published': self._safe_get(json_ld_data, 'datePublished', ''),
                'image': self._parse_recipe_image(json_ld_data),
                        'all_images': self._parse_all_recipe_images(json_ld_data, html_content),
                'difficulty': self._parse_difficulty(json_ld_data),
                'serving_size': '',
                'nutrition': self._parse_nutrition(json_ld_data),
                'ratings': self._parse_ratings(json_ld_data)
            }
            
            logger.debug(f"Successfully parsed recipe: {recipe['title']}")
            return recipe
            
        except Exception as e:
            logger.error(f"Error parsing recipe from JSON-LD: {e}")
            return self._create_empty_recipe(url)
    
    def _extract_doc_id(self, url: str) -> str:
        """Extract document ID from URL."""
        # Try new slug format first: /recipe/slug-12345
        match = re.search(r'/recipe/[^/]*-(\d+)', url)
        if match:
            return match.group(1)
        
        # Try old numeric format: /recipe/12345
        match = re.search(r'/recipe/(\d+)', url)
        if match:
            return match.group(1)
        
        return ''
    
    def _extract_correct_url(self, json_ld_data: Dict[str, Any], original_url: str, html_content: str = None) -> str:
        """Extract the correct URL format from JSON-LD data and HTML content."""
        # Try to find the canonical URL in the JSON-LD data
        if 'url' in json_ld_data:
            return json_ld_data['url']
        
        # Try to find it in the mainEntityOfPage
        if 'mainEntityOfPage' in json_ld_data:
            page_data = json_ld_data['mainEntityOfPage']
            if isinstance(page_data, dict) and 'url' in page_data:
                return page_data['url']
            elif isinstance(page_data, str) and page_data != "true":
                return page_data
        
        # If not found in JSON-LD, try to extract from HTML content
        if html_content:
            # Look for the URL in JavaScript data
            url_patterns = [
                r'"url"\s*:\s*"(https://www\.food\.com/recipe/[^"]*)"',  # Look for "url": "https://www.food.com/recipe/..."
                r'canonicalUrl["\']?\s*:\s*["\']([^"\']*)["\']',
                r'currentUrl["\']?\s*:\s*["\']([^"\']*)["\']'
            ]
            
            for pattern in url_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    found_url = match.group(1).strip()
                    if found_url and 'food.com' in found_url and '/recipe/' in found_url:
                        return found_url
        
        return original_url
    
    def _safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely get value from dictionary."""
        return data.get(key, default)
    
    def _parse_ingredients(self, data: Dict[str, Any]) -> List[str]:
        """Parse ingredients list."""
        ingredients = self._safe_get(data, 'recipeIngredient', [])
        if isinstance(ingredients, list):
            return [str(ingredient).strip() for ingredient in ingredients if ingredient]
        return []
    
    def _parse_instructions(self, data: Dict[str, Any]) -> List[str]:
        """Parse cooking instructions."""
        instructions = self._safe_get(data, 'recipeInstructions', [])
        if isinstance(instructions, list):
            result = []
            for instruction in instructions:
                if isinstance(instruction, dict):
                    text = instruction.get('text', '')
                    if text:
                        result.append(str(text).strip())
                elif isinstance(instruction, str):
                    result.append(str(instruction).strip())
            return result
        return []
    
    def _parse_times(self, data: Dict[str, Any]) -> Dict[str, int]:
        """Parse cooking times in minutes."""
        times = {}
        
        # Parse prep time
        prep_time = self._safe_get(data, 'prepTime', '')
        times['prep'] = self._parse_duration_to_minutes(prep_time)
        
        # Parse cook time
        cook_time = self._safe_get(data, 'cookTime', '')
        times['cook'] = self._parse_duration_to_minutes(cook_time)
        
        # Parse total time
        total_time = self._safe_get(data, 'totalTime', '')
        times['total'] = self._parse_duration_to_minutes(total_time)
        
        # If total time is not provided, calculate it
        if not times['total'] and (times['prep'] or times['cook']):
            times['total'] = (times['prep'] or 0) + (times['cook'] or 0)
        
        return times
    
    def _parse_duration_to_minutes(self, duration: str) -> int:
        """Convert ISO 8601 duration to minutes."""
        if not duration:
            return 0
            
        try:
            # Handle PT format (e.g., PT15M, PT1H30M)
            if duration.startswith('PT'):
                duration = duration[2:]  # Remove PT prefix
                
                total_minutes = 0
                
                # Parse hours
                hour_match = re.search(r'(\d+)H', duration)
                if hour_match:
                    total_minutes += int(hour_match.group(1)) * 60
                
                # Parse minutes
                minute_match = re.search(r'(\d+)M', duration)
                if minute_match:
                    total_minutes += int(minute_match.group(1))
                
                return total_minutes
                
        except (ValueError, AttributeError) as e:
            logger.debug(f"Failed to parse duration '{duration}': {e}")
            
        return 0
    
    def _parse_cuisine(self, data: Dict[str, Any]) -> List[str]:
        """Parse cuisine information - only actual cuisines (countries/regions)."""
        # Comprehensive list of ACTUAL cuisines (countries, regions, cultural origins)
        VALID_CUISINES = {
            # North America
            'american', 'canadian', 'mexican', 'tex mex', 'cajun', 'creole',
            'southwestern u.s.', 'native american',
            # South America
            'south american', 'latin', 'caribbean',
            # Europe
            'european', 'italian', 'french', 'spanish', 'greek', 'german',
            'portuguese', 'british', 'irish', 'scandinavian', 'polish',
            # Asia
            'asian', 'chinese', 'japanese', 'korean', 'thai', 'vietnamese',
            'indian', 'filipino', 'indonesian', 'malaysian', 'singaporean',
            # Middle East & Africa
            'mediterranean', 'moroccan', 'ethiopian', 'african', 'middle eastern',
            'lebanese', 'turkish', 'persian',
            # Oceania
            'australian', 'new zealand', 'hawaiian',
            # Cultural/Religious
            'jewish', 'kosher', 'halal'
        }
        
        # Try to extract from keywords
        keywords = self._safe_get(data, 'keywords', '')
        found_cuisines = []
        
        if isinstance(keywords, str):
            keywords_lower = keywords.lower()
            # Split by comma and check each keyword
            for kw in keywords.split(','):
                kw_clean = kw.strip().lower()
                if kw_clean in VALID_CUISINES:
                    found_cuisines.append(kw.strip().title())
        
        return found_cuisines
    
    def _parse_category(self, data: Dict[str, Any]) -> List[str]:
        """Parse recipe category - meal types, courses, and dietary tags."""
        categories = []
        
        # First, get the recipeCategory field (usually the main course type)
        recipe_category = self._safe_get(data, 'recipeCategory', '')
        if recipe_category and isinstance(recipe_category, str):
            categories.append(recipe_category.strip())
        
        # Define what should go into categories (NOT cuisines)
        MEAL_TYPES = {
            'breakfast', 'brunch', 'lunch', 'lunch/snacks', 'dinner', 'dessert',
            'appetizers', 'beverages', 'snacks', 'side dishes'
        }
        
        DIETARY_TAGS = {
            'vegan', 'vegetarian', 'kosher', 'halal', 'gluten-free', 'dairy-free',
            'egg free', 'lactose free', 'no shell fish', 'low cholesterol',
            'low protein', 'high protein', 'high fiber', 'very low carbs',
            'healthy', 'free of...'
        }
        
        DIFFICULTY_TAGS = {
            'beginner cook', 'easy', 'intermediate', 'advanced'
        }
        
        OCCASION_TAGS = {
            'christmas', 'thanksgiving', 'halloween', 'easter', 'birthday',
            'summer', 'winter', 'fall', 'spring', 'weeknight', 'potluck',
            'for large groups', 'kid friendly'
        }
        
        # Parse keywords to extract valid categories
        keywords = self._safe_get(data, 'keywords', '')
        if isinstance(keywords, str):
            for kw in keywords.split(','):
                kw_clean = kw.strip().lower()
                kw_display = kw.strip()
                
                # Check if it's a valid category type
                if (kw_clean in MEAL_TYPES or 
                    kw_clean in DIETARY_TAGS or 
                    kw_clean in DIFFICULTY_TAGS or 
                    kw_clean in OCCASION_TAGS):
                    if kw_display not in categories:
                        categories.append(kw_display)
        
        return categories
    
    def _parse_tools(self, data: Dict[str, Any]) -> List[str]:
        """Parse cooking tools/equipment."""
        # This would need to be extracted from instructions or other fields
        # For now, return empty list as it's not directly available in JSON-LD
        return []
    
    def _parse_author(self, data: Dict[str, Any]) -> str:
        """Parse recipe author."""
        author = self._safe_get(data, 'author', '')
        if isinstance(author, dict):
            return author.get('name', '')
        elif isinstance(author, str):
            return author
        return ''
    
    def _parse_nutrition(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse nutrition information."""
        nutrition = self._safe_get(data, 'nutrition')
        if isinstance(nutrition, dict):
            return {
                'calories': self._safe_get(nutrition, 'calories'),
                'fat': self._safe_get(nutrition, 'fatContent'),
                'saturated_fat': self._safe_get(nutrition, 'saturatedFatContent'),
                'cholesterol': self._safe_get(nutrition, 'cholesterolContent'),
                'sodium': self._safe_get(nutrition, 'sodiumContent'),
                'carbohydrates': self._safe_get(nutrition, 'carbohydrateContent'),
                'fiber': self._safe_get(nutrition, 'fiberContent'),
                'sugar': self._safe_get(nutrition, 'sugarContent'),
                'protein': self._safe_get(nutrition, 'proteinContent')
            }
        return None
    
    def _parse_ratings(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse rating information."""
        aggregate_rating = self._safe_get(data, 'aggregateRating')
        if isinstance(aggregate_rating, dict):
            return {
                'rating': self._safe_get(aggregate_rating, 'ratingValue'),
                'review_count': self._safe_get(aggregate_rating, 'reviewCount')
            }
        return None
    
    def _parse_keywords(self, data: Dict[str, Any]) -> List[str]:
        """Parse keywords/tags from the recipe."""
        keywords = self._safe_get(data, 'keywords', '')
        if isinstance(keywords, str):
            # Split by comma and clean up
            return [kw.strip() for kw in keywords.split(',') if kw.strip()]
        return []
    
    def _parse_recipe_image(self, data: Dict[str, Any]) -> str:
        """Parse recipe image URL, prioritizing actual recipe images over logos."""
        image = self._safe_get(data, 'image', '')
        if isinstance(image, str):
            # Filter out logo images
            if self._is_recipe_image(image):
                return image
        return ''
    
    def _is_recipe_image(self, url: str) -> bool:
        """Check if image URL is likely a recipe image (not logo)."""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Filter out common logo patterns FIRST
        logo_patterns = [
            'logo', 'favicon', 'icon', 'brand', 'avatar', 'profile',
            'fdc-shareGraphic', 'shareGraphic', 'header', 'footer', 'navigation', 'nav', 'banner',
            'static', 'gk-static'
        ]
        for pattern in logo_patterns:
            if pattern in url_lower:
                return False
        
        # Specifically filter out the logo URL
        if 'fdc-sharegraphic.png' in url_lower:
            return False
        
        # Look for recipe image patterns - prioritize these
        recipe_patterns = [
            'img/recipes/', 'img/feed/', 'recipe', 'food', 'dish', 
            'cooking', 'kitchen', 'meal', 'cuisine'
        ]
        for pattern in recipe_patterns:
            if pattern in url_lower:
                return True
        
        # If it's from img.sndimg.com and looks like a recipe image, include it
        if 'img.sndimg.com' in url_lower:
            # Check if it's in the recipes or feed directory
            if '/img/recipes/' in url_lower or '/img/feed/' in url_lower:
                return True
            # Check if it's a default recipe image (not a logo)
            if 'recipe-default-images' in url_lower:
                return True
            # Check if it has typical recipe image dimensions/parameters
            if any(param in url_lower for param in ['ar_5:4', 'ar_3:2', 'c_thumb', 'q_55', 'f_auto', 'w_744', 'w_860']):
                return True
        
        # If it's from food.com and not obviously a logo, include it
        if 'food.com' in url_lower and not any(logo in url_lower for logo in logo_patterns):
            return True
        
        return False
    
    def _parse_all_recipe_images(self, data: Dict[str, Any], html_content: str = None) -> List[str]:
        """Parse all recipe images from JSON-LD data and HTML content."""
        images = []
        seen_urls = set()
        
        # Get the primary image from JSON-LD
        image = self._safe_get(data, 'image', '')
        if isinstance(image, str) and image and self._is_recipe_image(image):
            images.append(image)
            seen_urls.add(image)
        elif isinstance(image, list):
            for img in image:
                if isinstance(img, str) and img and self._is_recipe_image(img):
                    images.append(img)
                    seen_urls.add(img)
        
        # If HTML content is provided, also extract images from HTML
        if html_content:
            from lxml import html
            doc = html.fromstring(html_content)
            
            # Extract additional images from HTML, prioritizing higher quality versions
            # Primary images - get the highest quality version
            primary_images = doc.xpath('//div[contains(@class, "primary-image")]//img[@src]')
            for img in primary_images:
                src = img.get('src', '')
                if src and self._is_recipe_image(src):
                    # Extract base URL without size parameters for deduplication
                    base_url = self._extract_base_image_url(src)
                    if base_url not in seen_urls:
                        images.append(src)
                        seen_urls.add(base_url)
            
            # Other images - get the highest quality version
            other_images = doc.xpath('//div[contains(@class, "other-images")]//img[@src]')
            for img in other_images:
                src = img.get('src', '')
                if src and self._is_recipe_image(src):
                    # Extract base URL without size parameters for deduplication
                    base_url = self._extract_base_image_url(src)
                    if base_url not in seen_urls:
                        images.append(src)
                        seen_urls.add(base_url)
        
        return images
    
    def _extract_base_image_url(self, url: str) -> str:
        """Extract base URL without size parameters for deduplication."""
        import re
        
        # For img.sndimg.com URLs, extract the base path before the transformation parameters
        if 'img.sndimg.com' in url:
            # Extract the path before the transformation parameters
            # e.g., /food/image/upload/f_auto,c_thumb,q_55,w_744,ar_5:4/v1/img/recipes/39/08/7/VPeSMiYHRce4BWsyj7Nl_0S9A5582.jpg
            # becomes /food/image/upload/v1/img/recipes/39/08/7/VPeSMiYHRce4BWsyj7Nl_0S9A5582.jpg
            match = re.search(r'(/food/image/upload/)[^/]+(/v\d+/.*\.jpg)', url)
            if match:
                return match.group(1) + match.group(2)
        
        # For other URLs, remove common size parameters
        base_url = re.sub(r'[?&](w_\d+|ar_\d+:\d+|c_thumb|q_\d+|f_auto)', '', url)
        base_url = re.sub(r'[,&]+$', '', base_url)
        return base_url
    
    def _parse_difficulty(self, data: Dict[str, Any]) -> str:
        """Parse difficulty level from keywords."""
        keywords = self._safe_get(data, 'keywords', '')
        if isinstance(keywords, str):
            keywords_lower = keywords.lower()
            if 'easy' in keywords_lower:
                return 'easy'
            elif 'intermediate' in keywords_lower or 'medium' in keywords_lower:
                return 'intermediate'
            elif 'hard' in keywords_lower or 'difficult' in keywords_lower or 'advanced' in keywords_lower:
                return 'hard'
        return ''
    
    def _create_empty_recipe(self, url: str) -> Dict[str, Any]:
        """Create empty recipe structure."""
        return {
            'id': self._extract_doc_id(url),
            'url': url,
            'title': '',
            'description': '',
            'ingredients': [],
            'instructions': [],
            'times': {'prep': 0, 'cook': 0, 'total': 0},
            'cuisine': [],
            'category': [],
            'tools': [],
            'yield': '',
            'author': '',
            'author_bio': '',
            'author_location': '',
            'author_stats': {},
            'keywords': [],
            'date_published': '',
            'image': '',
            'all_images': [],
            'difficulty': '',
            'serving_size': '',
            'nutrition': None,
            'ratings': None
        }
