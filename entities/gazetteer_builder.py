#!/usr/bin/env python3
"""
Phase E: Gazetteer Builder
Builds entity gazetteer from Wikipedia data or creates a simple one for testing.
"""

import logging
from pathlib import Path
from typing import Dict, List, Set

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GazetteerBuilder:
    """Builds entity gazetteer for ingredient recognition."""
    
    def __init__(self):
        self.entities = {}  # surface -> (wiki_title, normalized)
    
    def add_entity(self, surface: str, wiki_title: str, normalized: str):
        """Add an entity to the gazetteer."""
        if surface and wiki_title and normalized:
            self.entities[surface.lower()] = (wiki_title, normalized)
    
    def build_simple_gazetteer(self) -> Dict[str, tuple]:
        """Build a simple gazetteer for testing with common ingredients."""
        logger.info("Building simple gazetteer for testing")
        
        # Common ingredients and their Wikipedia links
        ingredients = [
            # Proteins
            ("chicken", "Chicken", "chicken"),
            ("beef", "Beef", "beef"),
            ("pork", "Pork", "pork"),
            ("fish", "Fish", "fish"),
            ("salmon", "Salmon", "salmon"),
            ("turkey", "Turkey (bird)", "turkey"),
            ("lamb", "Lamb and mutton", "lamb"),
            ("shrimp", "Shrimp", "shrimp"),
            ("crab", "Crab", "crab"),
            ("lobster", "Lobster", "lobster"),
            
            # Vegetables
            ("onion", "Onion", "onion"),
            ("garlic", "Garlic", "garlic"),
            ("tomato", "Tomato", "tomato"),
            ("potato", "Potato", "potato"),
            ("carrot", "Carrot", "carrot"),
            ("celery", "Celery", "celery"),
            ("pepper", "Bell pepper", "bell pepper"),
            ("mushroom", "Mushroom", "mushroom"),
            ("spinach", "Spinach", "spinach"),
            ("lettuce", "Lettuce", "lettuce"),
            ("broccoli", "Broccoli", "broccoli"),
            ("cauliflower", "Cauliflower", "cauliflower"),
            ("cabbage", "Cabbage", "cabbage"),
            ("cucumber", "Cucumber", "cucumber"),
            ("zucchini", "Zucchini", "zucchini"),
            ("eggplant", "Eggplant", "eggplant"),
            ("asparagus", "Asparagus", "asparagus"),
            ("artichoke", "Artichoke", "artichoke"),
            
            # Fruits
            ("apple", "Apple", "apple"),
            ("banana", "Banana", "banana"),
            ("orange", "Orange (fruit)", "orange"),
            ("lemon", "Lemon", "lemon"),
            ("lime", "Lime (fruit)", "lime"),
            ("strawberry", "Strawberry", "strawberry"),
            ("blueberry", "Blueberry", "blueberry"),
            ("raspberry", "Raspberry", "raspberry"),
            ("grape", "Grape", "grape"),
            ("cherry", "Cherry", "cherry"),
            ("peach", "Peach", "peach"),
            ("pear", "Pear", "pear"),
            ("plum", "Plum", "plum"),
            ("mango", "Mango", "mango"),
            ("pineapple", "Pineapple", "pineapple"),
            ("watermelon", "Watermelon", "watermelon"),
            ("cantaloupe", "Cantaloupe", "cantaloupe"),
            
            # Dairy
            ("milk", "Milk", "milk"),
            ("cheese", "Cheese", "cheese"),
            ("butter", "Butter", "butter"),
            ("cream", "Cream", "cream"),
            ("yogurt", "Yogurt", "yogurt"),
            ("sour cream", "Sour cream", "sour cream"),
            ("cottage cheese", "Cottage cheese", "cottage cheese"),
            ("ricotta", "Ricotta", "ricotta"),
            ("mozzarella", "Mozzarella", "mozzarella"),
            ("cheddar", "Cheddar cheese", "cheddar cheese"),
            ("parmesan", "Parmesan cheese", "parmesan cheese"),
            ("feta", "Feta", "feta cheese"),
            ("goat cheese", "Goat cheese", "goat cheese"),
            ("blue cheese", "Blue cheese", "blue cheese"),
            ("swiss cheese", "Swiss cheese", "swiss cheese"),
            
            # Grains and starches
            ("rice", "Rice", "rice"),
            ("pasta", "Pasta", "pasta"),
            ("bread", "Bread", "bread"),
            ("flour", "Flour", "flour"),
            ("oats", "Oat", "oats"),
            ("quinoa", "Quinoa", "quinoa"),
            ("barley", "Barley", "barley"),
            ("wheat", "Wheat", "wheat"),
            ("corn", "Maize", "corn"),
            ("potato", "Potato", "potato"),
            ("sweet potato", "Sweet potato", "sweet potato"),
            ("yam", "Yam (vegetable)", "yam"),
            
            # Nuts and seeds
            ("almond", "Almond", "almond"),
            ("walnut", "Walnut", "walnut"),
            ("pecan", "Pecan", "pecan"),
            ("cashew", "Cashew", "cashew"),
            ("pistachio", "Pistachio", "pistachio"),
            ("hazelnut", "Hazelnut", "hazelnut"),
            ("peanut", "Peanut", "peanut"),
            ("sunflower seed", "Sunflower seed", "sunflower seed"),
            ("sesame seed", "Sesame", "sesame seed"),
            ("chia seed", "Chia seed", "chia seed"),
            ("flax seed", "Flax", "flax seed"),
            
            # Herbs and spices
            ("basil", "Basil", "basil"),
            ("oregano", "Oregano", "oregano"),
            ("thyme", "Thyme", "thyme"),
            ("rosemary", "Rosemary", "rosemary"),
            ("sage", "Sage", "sage"),
            ("parsley", "Parsley", "parsley"),
            ("cilantro", "Coriander", "cilantro"),
            ("dill", "Dill", "dill"),
            ("mint", "Mint", "mint"),
            ("chives", "Chives", "chives"),
            ("ginger", "Ginger", "ginger"),
            ("cinnamon", "Cinnamon", "cinnamon"),
            ("nutmeg", "Nutmeg", "nutmeg"),
            ("cloves", "Clove", "cloves"),
            ("cardamom", "Cardamom", "cardamom"),
            ("cumin", "Cumin", "cumin"),
            ("coriander", "Coriander", "coriander"),
            ("paprika", "Paprika", "paprika"),
            ("cayenne", "Cayenne pepper", "cayenne pepper"),
            ("black pepper", "Black pepper", "black pepper"),
            ("salt", "Salt", "salt"),
            
            # Oils and fats
            ("olive oil", "Olive oil", "olive oil"),
            ("vegetable oil", "Vegetable oil", "vegetable oil"),
            ("canola oil", "Canola oil", "canola oil"),
            ("coconut oil", "Coconut oil", "coconut oil"),
            ("sesame oil", "Sesame oil", "sesame oil"),
            ("avocado oil", "Avocado oil", "avocado oil"),
            ("lard", "Lard", "lard"),
            ("shortening", "Shortening", "shortening"),
            
            # Legumes
            ("bean", "Bean", "bean"),
            ("black bean", "Black bean", "black bean"),
            ("kidney bean", "Kidney bean", "kidney bean"),
            ("chickpea", "Chickpea", "chickpea"),
            ("lentil", "Lentil", "lentil"),
            ("soybean", "Soybean", "soybean"),
            ("pea", "Pea", "pea"),
            ("green bean", "Green bean", "green bean"),
            
            # Other common ingredients
            ("egg", "Egg (food)", "egg"),
            ("honey", "Honey", "honey"),
            ("sugar", "Sugar", "sugar"),
            ("brown sugar", "Brown sugar", "brown sugar"),
            ("maple syrup", "Maple syrup", "maple syrup"),
            ("vanilla", "Vanilla", "vanilla"),
            ("chocolate", "Chocolate", "chocolate"),
            ("cocoa", "Cocoa bean", "cocoa"),
            ("coffee", "Coffee", "coffee"),
            ("tea", "Tea", "tea"),
            ("vinegar", "Vinegar", "vinegar"),
            ("soy sauce", "Soy sauce", "soy sauce"),
            ("worcestershire sauce", "Worcestershire sauce", "worcestershire sauce"),
            ("ketchup", "Ketchup", "ketchup"),
            ("mustard", "Mustard (condiment)", "mustard"),
            ("mayonnaise", "Mayonnaise", "mayonnaise"),
            ("salsa", "Salsa (sauce)", "salsa"),
            ("pesto", "Pesto", "pesto"),
            ("hummus", "Hummus", "hummus"),
            ("tahini", "Tahini", "tahini"),
        ]
        
        for surface, wiki_title, normalized in ingredients:
            self.add_entity(surface, wiki_title, normalized)
            # Also add plural forms
            if not surface.endswith('s'):
                self.add_entity(surface + 's', wiki_title, normalized)
        
        logger.info(f"Built gazetteer with {len(self.entities)} entities")
        return self.entities
    
    def save_gazetteer(self, output_file: str):
        """Save gazetteer to TSV file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("surface\twiki_title\tnormalized\n")
            for surface, (wiki_title, normalized) in sorted(self.entities.items()):
                f.write(f"{surface}\t{wiki_title}\t{normalized}\n")
        
        logger.info(f"Gazetteer saved to {output_file}")

def main():
    """Main function for gazetteer builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build entity gazetteer')
    parser.add_argument('--output', required=True, help='Output TSV file for gazetteer')
    
    args = parser.parse_args()
    
    logger.info("Starting Phase E: Gazetteer Builder")
    
    try:
        builder = GazetteerBuilder()
        builder.build_simple_gazetteer()
        builder.save_gazetteer(args.output)
        logger.info("Phase E (Gazetteer Builder) completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Phase E (Gazetteer Builder) failed: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())

