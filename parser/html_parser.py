"""
HTML fallback parser for extracting recipe data when JSON-LD is not available.
Uses heuristics and HTML structure analysis.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import lxml.html
from lxml import etree

logger = logging.getLogger(__name__)

class HTMLParser:
    """Fallback HTML parser using heuristics and structure analysis."""
    
    def __init__(self):
        self.time_patterns = [
            r'(\d+)\s*(?:hour|hr|h)\s*(?:and\s*)?(\d+)?\s*(?:minute|min|m)?',
            r'(\d+)\s*(?:minute|min|m)',
            r'(\d+)\s*(?:hour|hr|h)',
            r'ready\s*in\s*(\d+)\s*(?:minute|min|m|hour|hr|h)',
            r'prep\s*time[:\s]*(\d+)\s*(?:minute|min|m|hour|hr|h)',
            r'cook\s*time[:\s]*(\d+)\s*(?:minute|min|m|hour|hr|h)',
            r'total\s*time[:\s]*(\d+)\s*(?:minute|min|m|hour|hr|h)'
        ]
        
        # Comprehensive list of ACTUAL cuisines (countries/regions)
        self.cuisine_keywords = [
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
        ]
    
    def parse_recipe(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse recipe from HTML content using heuristics."""
        try:
            # Parse HTML
            doc = lxml.html.fromstring(html_content)
            
            # Extract the correct URL format from HTML content
            correct_url = self._extract_correct_url(doc, url, html_content)
            
            recipe = {
                'id': self._extract_doc_id(correct_url),
                'url': correct_url,
                'title': self._extract_title(doc),
                'description': self._extract_description(doc, html_content),
                'ingredients': self._extract_ingredients(doc),
                'instructions': self._extract_instructions(doc),
                'times': self._extract_times(doc, html_content),
                'cuisine': self._extract_cuisine(doc, html_content),
                'category': self._extract_category(doc),
                'tools': self._extract_tools(doc),
                'yield': self._extract_yield(doc, html_content),
                'author': self._extract_author(doc, html_content),
                'author_bio': self._extract_author_bio(doc, html_content),
                'author_location': self._extract_author_location(doc, html_content),
                'author_stats': self._extract_author_stats(doc, html_content),
                'keywords': self._extract_keywords(doc, html_content),
                'date_published': self._extract_date_published(doc, html_content),
                        'image': self._extract_recipe_image(doc, html_content),
                        'all_images': self._extract_all_recipe_images(doc, html_content),
                'difficulty': self._extract_difficulty(doc, html_content),
                'serving_size': self._extract_serving_size(doc, html_content),
                'nutrition': self._extract_enhanced_nutrition(doc, html_content),
                'ratings': self._extract_ratings(doc)
            }
            
            logger.debug(f"Successfully parsed recipe using HTML heuristics: {recipe['title']}")
            return recipe
            
        except Exception as e:
            logger.error(f"Error parsing recipe from HTML: {e}")
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
    
    def _extract_correct_url(self, doc: etree.Element, original_url: str, html_content: str) -> str:
        """Extract the correct URL format from HTML content."""
        # Try to find the canonical URL or current URL in meta tags
        canonical_url = doc.xpath('//link[@rel="canonical"]/@href')
        if canonical_url:
            return canonical_url[0].strip()
        
        # Try to find the current URL in script data - look for the recipe data object
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
        
        # If we can't find a better URL, return the original
        return original_url
    
    def _extract_title(self, doc: etree.Element) -> str:
        """Extract recipe title."""
        # Try different selectors for title
        selectors = [
            'h1',
            '.recipe-title',
            '.title',
            '[data-testid="recipe-title"]',
            'title'
        ]
        
        for selector in selectors:
            elements = doc.cssselect(selector)
            if elements:
                title = elements[0].text_content().strip()
                if title and len(title) > 3:  # Basic validation
                    return title
        
        return ''
    
    def _extract_ingredients(self, doc: etree.Element) -> List[str]:
        """Extract ingredients list."""
        ingredients = []
        
        # Try different selectors for ingredients
        selectors = [
            '.ingredient',
            '.ingredients li',
            '.ingredient-list li',
            '[data-testid="ingredient"]',
            '.recipe-ingredient',
            'li[class*="ingredient"]'
        ]
        
        for selector in selectors:
            elements = doc.cssselect(selector)
            if elements:
                for element in elements:
                    text = element.text_content().strip()
                    if text and len(text) > 2:
                        ingredients.append(text)
                if ingredients:
                    break
        
        # If no ingredients found, try to find any list that might contain ingredients
        if not ingredients:
            lists = doc.cssselect('ul, ol')
            for ul in lists:
                items = ul.cssselect('li')
                if len(items) >= 3:  # Likely ingredients list
                    for item in items:
                        text = item.text_content().strip()
                        if text and len(text) > 2:
                            ingredients.append(text)
                    if ingredients:
                        break
        
        return ingredients
    
    def _extract_instructions(self, doc: etree.Element) -> List[str]:
        """Extract cooking instructions."""
        instructions = []
        
        # Try different selectors for instructions
        selectors = [
            '.instruction',
            '.directions li',
            '.recipe-instruction',
            '.step',
            '[data-testid="instruction"]',
            '.cooking-instruction',
            'li[class*="instruction"]',
            'li[class*="step"]',
            'li[class*="direction"]'
        ]
        
        for selector in selectors:
            elements = doc.cssselect(selector)
            if elements:
                for element in elements:
                    text = element.text_content().strip()
                    if text and len(text) > 10:  # Instructions should be longer
                        instructions.append(text)
                if instructions:
                    break
        
        # If no instructions found, try to find numbered lists
        if not instructions:
            numbered_lists = doc.cssselect('ol')
            for ol in numbered_lists:
                items = ol.cssselect('li')
                if len(items) >= 2:  # Likely instructions
                    for item in items:
                        text = item.text_content().strip()
                        if text and len(text) > 10:
                            instructions.append(text)
                    if instructions:
                        break
        
        return instructions
    
    def _extract_times(self, doc: etree.Element, html_content: str) -> Dict[str, int]:
        """Extract cooking times."""
        times = {'prep': 0, 'cook': 0, 'total': 0}
        
        # Look for time patterns in the HTML content
        time_text = html_content.lower()
        
        for pattern in self.time_patterns:
            matches = re.finditer(pattern, time_text, re.IGNORECASE)
            for match in matches:
                if 'prep' in match.group(0):
                    times['prep'] = self._parse_time_match(match)
                elif 'cook' in match.group(0):
                    times['cook'] = self._parse_time_match(match)
                elif 'total' in match.group(0) or 'ready' in match.group(0):
                    times['total'] = self._parse_time_match(match)
        
        # If total time is not found, calculate it
        if not times['total'] and (times['prep'] or times['cook']):
            times['total'] = (times['prep'] or 0) + (times['cook'] or 0)
        
        return times
    
    def _parse_time_match(self, match) -> int:
        """Parse time from regex match."""
        try:
            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2)) if match.group(2) else 0
            
            if 'hour' in match.group(0) or 'hr' in match.group(0) or 'h' in match.group(0):
                return hours * 60 + minutes
            else:
                return hours + minutes
        except (ValueError, IndexError):
            return 0
    
    def _extract_cuisine(self, doc: etree.Element, html_content: str) -> List[str]:
        """Extract cuisine information - only actual cuisines (countries/regions)."""
        cuisines = []
        
        # Look in meta keywords
        meta_keywords = doc.cssselect('meta[name="keywords"]')
        if meta_keywords:
            keywords_content = meta_keywords[0].get('content', '')
            # Split by comma and check each one
            for kw in keywords_content.split(','):
                kw_clean = kw.strip().lower()
                if kw_clean in self.cuisine_keywords:
                    cuisine_title = kw.strip().title()
                    if cuisine_title not in cuisines:
                        cuisines.append(cuisine_title)
        
        # Look in breadcrumbs or navigation
        breadcrumbs = doc.cssselect('.breadcrumb, .breadcrumbs, nav')
        for breadcrumb in breadcrumbs:
            text = breadcrumb.text_content().lower()
            for cuisine in self.cuisine_keywords:
                cuisine_title = cuisine.title()
                if cuisine in text and cuisine_title not in cuisines:
                    cuisines.append(cuisine_title)
        
        return cuisines
    
    def _extract_category(self, doc: etree.Element) -> List[str]:
        """Extract recipe category - meal types, courses, and dietary tags."""
        categories = []
        
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
        
        # Look for category in breadcrumbs
        breadcrumbs = doc.cssselect('.breadcrumb, .breadcrumbs, nav')
        for breadcrumb in breadcrumbs:
            links = breadcrumb.cssselect('a')
            for link in links:
                text = link.text_content().strip()
                text_lower = text.lower()
                if (text and len(text) > 2 and 
                    text_lower not in ['home', 'recipes', 'recipe'] and
                    (text_lower in MEAL_TYPES or text_lower in DIETARY_TAGS)):
                    categories.append(text)
        
        # Also check meta keywords for categories
        meta_keywords = doc.cssselect('meta[name="keywords"]')
        if meta_keywords:
            keywords_content = meta_keywords[0].get('content', '')
            for kw in keywords_content.split(','):
                kw_clean = kw.strip().lower()
                kw_display = kw.strip()
                if ((kw_clean in MEAL_TYPES or kw_clean in DIETARY_TAGS) and
                    kw_display not in categories):
                    categories.append(kw_display)
        
        return categories
    
    def _extract_tools(self, doc: etree.Element) -> List[str]:
        """Extract cooking tools/equipment."""
        tools = []
        
        # Look for tool mentions in instructions
        instructions = self._extract_instructions(doc)
        tool_keywords = [
            'oven', 'stove', 'pan', 'pot', 'skillet', 'grill', 'microwave',
            'blender', 'mixer', 'food processor', 'knife', 'cutting board',
            'baking sheet', 'casserole dish', 'slow cooker', 'pressure cooker'
        ]
        
        for instruction in instructions:
            instruction_lower = instruction.lower()
            for tool in tool_keywords:
                if tool in instruction_lower and tool not in tools:
                    tools.append(tool)
        
        return tools
    
    def _extract_yield(self, doc: etree.Element, html_content: str) -> str:
        """Extract recipe yield/servings."""
        # Look for yield patterns
        yield_patterns = [
            r'serves?\s*(\d+)',
            r'yield[s]?\s*(\d+)',
            r'makes?\s*(\d+)',
            r'(\d+)\s*serving[s]?',
            r'(\d+)\s*portion[s]?'
        ]
        
        content_lower = html_content.lower()
        for pattern in yield_patterns:
            match = re.search(pattern, content_lower)
            if match:
                return match.group(1)
        
        return ''
    
    def _extract_author(self, doc: etree.Element, html_content: str) -> str:
        """Extract recipe author."""
        # Look for author patterns
        author_patterns = [
            r'submitted\s+by\s+([^,\n]+)',
            r'by\s+([^,\n]+)',
            r'author[:\s]+([^,\n]+)'
        ]
        
        content_lower = html_content.lower()
        for pattern in author_patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_nutrition(self, doc: etree.Element) -> Optional[Dict[str, Any]]:
        """Extract nutrition information."""
        nutrition = {}
        
        # Look for nutrition table or data
        nutrition_tables = doc.cssselect('.nutrition, .nutrition-info, table.nutrition')
        for table in nutrition_tables:
            rows = table.cssselect('tr')
            for row in rows:
                cells = row.cssselect('td, th')
                if len(cells) >= 2:
                    key = cells[0].text_content().strip().lower()
                    value = cells[1].text_content().strip()
                    
                    # Map common nutrition terms
                    if 'calorie' in key:
                        nutrition['calories'] = value
                    elif 'fat' in key and 'saturated' not in key:
                        nutrition['fat'] = value
                    elif 'saturated' in key:
                        nutrition['saturated_fat'] = value
                    elif 'cholesterol' in key:
                        nutrition['cholesterol'] = value
                    elif 'sodium' in key:
                        nutrition['sodium'] = value
                    elif 'carbohydrate' in key:
                        nutrition['carbohydrates'] = value
                    elif 'fiber' in key:
                        nutrition['fiber'] = value
                    elif 'sugar' in key:
                        nutrition['sugar'] = value
                    elif 'protein' in key:
                        nutrition['protein'] = value
        
        return nutrition if nutrition else None
    
    def _extract_ratings(self, doc: etree.Element) -> Optional[Dict[str, Any]]:
        """Extract rating information."""
        ratings = {}
        
        # Look for rating elements
        rating_elements = doc.cssselect('.rating, .stars, .score, [data-rating]')
        for element in rating_elements:
            text = element.text_content().strip()
            # Try to extract rating number
            rating_match = re.search(r'(\d+(?:\.\d+)?)', text)
            if rating_match:
                ratings['rating'] = float(rating_match.group(1))
                break
        
        # Look for review count
        review_elements = doc.cssselect('.reviews, .review-count, [data-reviews]')
        for element in review_elements:
            text = element.text_content().strip()
            review_match = re.search(r'(\d+)', text)
            if review_match:
                ratings['review_count'] = int(review_match.group(1))
                break
        
        return ratings if ratings else None
    
    def _extract_description(self, doc: etree.Element, html_content: str) -> str:
        """Extract recipe description from meta tags or content."""
        # Try meta description first
        meta_desc = doc.xpath('//meta[@name="description"]/@content')
        if meta_desc:
            return meta_desc[0].strip()
        
        # Try og:description
        og_desc = doc.xpath('//meta[@property="og:description"]/@content')
        if og_desc:
            return og_desc[0].strip()
        
        # Try to find description in content
        desc_patterns = [
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']',
            r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']*)["\']'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_keywords(self, doc: etree.Element, html_content: str) -> List[str]:
        """Extract keywords from meta tags or content."""
        # Try meta keywords
        meta_keywords = doc.xpath('//meta[@name="keywords"]/@content')
        if meta_keywords:
            keywords = meta_keywords[0].split(',')
            return [kw.strip() for kw in keywords if kw.strip()]
        
        # Try to extract from script data
        script_pattern = r'keywords["\']?\s*:\s*["\']([^"\']*)["\']'
        match = re.search(script_pattern, html_content, re.IGNORECASE)
        if match:
            keywords = match.group(1).split(',')
            return [kw.strip() for kw in keywords if kw.strip()]
        
        return []
    
    def _extract_date_published(self, doc: etree.Element, html_content: str) -> str:
        """Extract publication date from meta tags or content."""
        # Try meta datePublished
        meta_date = doc.xpath('//meta[@name="datePublished"]/@content')
        if meta_date:
            return meta_date[0].strip()
        
        # Try to extract from script data
        date_patterns = [
            r'datePublished["\']?\s*:\s*["\']([^"\']*)["\']',
            r'OrigPubDate["\']?\s*:\s*["\']([^"\']*)["\']'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_recipe_image(self, doc: etree.Element, html_content: str) -> str:
        """Extract primary recipe image URL, prioritizing actual food images over logos."""
        # First, try to find the primary recipe image in the media section
        primary_image = doc.xpath('//div[contains(@class, "primary-image")]//img[@src]')
        if primary_image:
            src = primary_image[0].get('src', '')
            if src and self._is_recipe_image(src):
                return src
        
        # Try to find images in the media section (both primary and other images)
        media_images = doc.xpath('//div[contains(@class, "media")]//img[@src]')
        for img in media_images:
            src = img.get('src', '')
            if src and self._is_recipe_image(src):
                return src
        
        # Try meta og:image as fallback
        og_image = doc.xpath('//meta[@property="og:image"]/@content')
        if og_image:
            image_url = og_image[0].strip()
            if self._is_recipe_image(image_url):
                return image_url
        
        # Try to find any recipe-related images in content
        img_elements = doc.xpath('//img[@src]')
        for img in img_elements:
            src = img.get('src', '')
            if src and self._is_recipe_image(src):
                return src
        
        return ''
    
    def _extract_all_recipe_images(self, doc: etree.Element, html_content: str) -> List[str]:
        """Extract all recipe images (primary + additional) as a list."""
        images = []
        
        # Extract primary image
        primary_image = doc.xpath('//div[contains(@class, "primary-image")]//img[@src]')
        if primary_image:
            src = primary_image[0].get('src', '')
            if src and self._is_recipe_image(src):
                images.append(src)
        
        # Extract additional images from other-images section
        other_images = doc.xpath('//div[contains(@class, "other-images")]//img[@src]')
        for img in other_images:
            src = img.get('src', '')
            if src and self._is_recipe_image(src) and src not in images:
                images.append(src)
        
        # If no images found in media sections, try other locations
        if not images:
            # Try meta og:image as fallback
            og_image = doc.xpath('//meta[@property="og:image"]/@content')
            if og_image:
                image_url = og_image[0].strip()
                if self._is_recipe_image(image_url):
                    images.append(image_url)
            
            # Try to find any recipe-related images in content
            img_elements = doc.xpath('//img[@src]')
            for img in img_elements:
                src = img.get('src', '')
                if src and self._is_recipe_image(src) and src not in images:
                    images.append(src)
        
        return images
    
    def _is_recipe_image(self, url: str) -> bool:
        """Check if image URL is likely a recipe image (not logo)."""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Filter out common logo patterns FIRST
        logo_patterns = [
            'logo', 'favicon', 'icon', 'brand', 'avatar', 'profile',
            'fdc-shareGraphic', 'shareGraphic', 'header', 'footer', 'navigation', 'nav', 'banner'
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
    
    def _extract_difficulty(self, doc: etree.Element, html_content: str) -> str:
        """Extract difficulty level from keywords or content."""
        # Look for difficulty keywords in content
        difficulty_keywords = {
            'easy': ['easy', 'simple', 'quick', 'basic', 'beginner'],
            'intermediate': ['intermediate', 'medium', 'moderate'],
            'hard': ['hard', 'difficult', 'advanced', 'complex', 'challenging']
        }
        
        content_lower = html_content.lower()
        
        for level, keywords in difficulty_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return level
        
        return ''
    
    def _extract_serving_size(self, doc: etree.Element, html_content: str) -> str:
        """Extract detailed serving size information."""
        # Try to find serving size in nutrition data
        serving_patterns = [
            r'servingSize["\']?\s*:\s*["\']([^"\']*)["\']',
            r'serving\s*size[:\s]*([^<\n]+)',
            r'per\s*serving[:\s]*([^<\n]+)'
        ]
        
        for pattern in serving_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_author_bio(self, doc: etree.Element, html_content: str) -> str:
        """Extract author biography."""
        # Try to find author bio in script data
        bio_patterns = [
            r'bio["\']?\s*:\s*["\']([^"\']*)["\']',
            r'biography["\']?\s*:\s*["\']([^"\']*)["\']'
        ]
        
        for pattern in bio_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                bio = match.group(1).strip()
                # Clean up HTML tags
                bio = re.sub(r'<[^>]+>', '', bio)
                bio = re.sub(r'&[^;]+;', ' ', bio)
                return bio
        
        return ''
    
    def _extract_author_location(self, doc: etree.Element, html_content: str) -> str:
        """Extract author location."""
        # Try to find location in script data
        location_patterns = [
            r'location["\']?\s*:\s*["\']([^"\']*)["\']',
            r'address["\']?\s*:\s*["\']([^"\']*)["\']'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_author_stats(self, doc: etree.Element, html_content: str) -> Dict[str, Any]:
        """Extract author statistics."""
        stats = {}
        
        # Try to find recipe count
        recipe_count_pattern = r'recipesCount["\']?\s*:\s*(\d+)'
        match = re.search(recipe_count_pattern, html_content, re.IGNORECASE)
        if match:
            stats['recipes'] = int(match.group(1))
        
        # Try to find follower count
        follower_pattern = r'followMeCount["\']?\s*:\s*(\d+)'
        match = re.search(follower_pattern, html_content, re.IGNORECASE)
        if match:
            stats['followers'] = int(match.group(1))
        
        return stats
    
    def _extract_enhanced_nutrition(self, doc: etree.Element, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract enhanced nutrition information."""
        nutrition = {}
        
        # Enhanced nutrition patterns
        nutrition_patterns = {
            'serving_size': r'servingSize["\']?\s*:\s*["\']([^"\']*)["\']',
            'calories_from_fat': r'caloriesFromFat["\']?\s*:\s*["\']([^"\']*)["\']',
            'calories_from_fat_pct': r'caloriesFromFatPctDailyValue["\']?\s*:\s*["\']([^"\']*)["\']',
            'total_fat_pct': r'totalFatPctDailyValue["\']?\s*:\s*["\']([^"\']*)["\']',
            'saturated_fat_pct': r'saturatedFatPctDailyValue["\']?\s*:\s*["\']([^"\']*)["\']',
            'cholesterol_pct': r'cholesterolPctDailyValue["\']?\s*:\s*["\']([^"\']*)["\']',
            'sodium_pct': r'sodiumPctDailyValue["\']?\s*:\s*["\']([^"\']*)["\']',
            'carbohydrate_pct': r'totalCarbohydratePctDailyValue["\']?\s*:\s*["\']([^"\']*)["\']',
            'fiber_pct': r'dietaryFiberPctDailyValue["\']?\s*:\s*["\']([^"\']*)["\']',
            'sugar_pct': r'sugarsPctDailyValue["\']?\s*:\s*["\']([^"\']*)["\']',
            'protein_pct': r'proteinPctDailyValue["\']?\s*:\s*["\']([^"\']*)["\']'
        }
        
        for key, pattern in nutrition_patterns.items():
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                nutrition[key] = match.group(1).strip()
        
        # Also get basic nutrition data
        basic_nutrition = self._extract_nutrition(doc)
        if basic_nutrition:
            nutrition.update(basic_nutrition)
        
        return nutrition if nutrition else None
    
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
