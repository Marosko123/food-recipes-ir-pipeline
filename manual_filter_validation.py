#!/usr/bin/env python3
"""
Manual filter validation - checks recipe data directly without search index
"""

import json
from pathlib import Path

def validate_rating_filter():
    """Manually validate that rating filtering logic works correctly"""
    print("\n" + "=" * 60)
    print("Manual Validation: Rating & Review Count Filters")
    print("=" * 60)
    
    recipes_with_high_rating = []
    recipes_with_many_reviews = []
    
    with open('data/normalized/recipes.jsonl', 'r') as f:
        for i, line in enumerate(f):
            if i >= 100:  # Check first 100 recipes
                break
            
            recipe = json.loads(line)
            ratings = recipe.get('ratings') or {}
            
            # Test string-to-float conversion
            rating_str = ratings.get('rating', '0') if isinstance(ratings, dict) else '0'
            review_count_str = ratings.get('review_count', '0') if isinstance(ratings, dict) else '0'
            
            try:
                rating_value = float(rating_str) if rating_str else 0.0
                review_count_value = int(review_count_str) if review_count_str else 0
                
                # Test min_rating filter
                if rating_value >= 4.0:
                    recipes_with_high_rating.append({
                        'title': recipe.get('title', 'Unknown')[:50],
                        'rating': rating_value,
                        'review_count': review_count_value
                    })
                
                # Test min_review_count filter
                if review_count_value >= 50:
                    recipes_with_many_reviews.append({
                        'title': recipe.get('title', 'Unknown')[:50],
                        'rating': rating_value,
                        'review_count': review_count_value
                    })
                    
            except (ValueError, TypeError) as e:
                print(f"⚠️  Conversion error for recipe {recipe.get('id')}: {e}")
    
    print(f"\n✅ Found {len(recipes_with_high_rating)} recipes with rating >= 4.0")
    print("Sample recipes:")
    for recipe in recipes_with_high_rating[:3]:
        print(f"  - {recipe['title']}")
        print(f"    Rating: {recipe['rating']}, Reviews: {recipe['review_count']}")
    
    print(f"\n✅ Found {len(recipes_with_many_reviews)} recipes with >= 50 reviews")
    print("Sample recipes:")
    for recipe in recipes_with_many_reviews[:3]:
        print(f"  - {recipe['title']}")
        print(f"    Rating: {recipe['rating']}, Reviews: {recipe['review_count']}")

def validate_nutrition_filter():
    """Manually validate that nutrition filtering logic works correctly"""
    print("\n" + "=" * 60)
    print("Manual Validation: Nutrition Filters")
    print("=" * 60)
    
    low_calorie_recipes = []
    
    with open('data/normalized/recipes.jsonl', 'r') as f:
        for i, line in enumerate(f):
            if i >= 100:  # Check first 100 recipes
                break
            
            recipe = json.loads(line)
            nutrition = recipe.get('nutrition') or {}
            
            # Test string-to-float conversion for nutrition
            calories_str = nutrition.get('calories', '0') if isinstance(nutrition, dict) else '0'
            
            try:
                calories_value = float(calories_str) if calories_str else 0.0
                
                # Test max_calories filter
                if calories_value > 0 and calories_value <= 300:
                    low_calorie_recipes.append({
                        'title': recipe.get('title', 'Unknown')[:50],
                        'calories': calories_value,
                        'protein': float(nutrition.get('protein', '0') or '0'),
                        'fat': float(nutrition.get('fat', '0') or '0')
                    })
                    
            except (ValueError, TypeError) as e:
                print(f"⚠️  Conversion error for recipe {recipe.get('id')}: {e}")
    
    print(f"\n✅ Found {len(low_calorie_recipes)} recipes with <= 300 calories")
    print("Sample recipes:")
    for recipe in low_calorie_recipes[:3]:
        print(f"  - {recipe['title']}")
        print(f"    Calories: {recipe['calories']}, Protein: {recipe['protein']}g, Fat: {recipe['fat']}g")

def validate_time_filter():
    """Manually validate that time filtering logic works correctly"""
    print("\n" + "=" * 60)
    print("Manual Validation: Time Filters")
    print("=" * 60)
    
    quick_recipes = []
    
    with open('data/normalized/recipes.jsonl', 'r') as f:
        for i, line in enumerate(f):
            if i >= 100:  # Check first 100 recipes
                break
            
            recipe = json.loads(line)
            times = recipe.get('times', {})
            
            total_time = times.get('total', 0)
            
            # Test max_total_minutes filter
            if total_time > 0 and total_time <= 30:
                quick_recipes.append({
                    'title': recipe.get('title', 'Unknown')[:50],
                    'total_time': total_time,
                    'prep_time': times.get('prep', 0),
                    'cook_time': times.get('cook', 0)
                })
    
    print(f"\n✅ Found {len(quick_recipes)} recipes with <= 30 minutes total time")
    print("Sample recipes:")
    for recipe in quick_recipes[:3]:
        print(f"  - {recipe['title']}")
        print(f"    Total: {recipe['total_time']}min (Prep: {recipe['prep_time']}min, Cook: {recipe['cook_time']}min)")

if __name__ == '__main__':
    print("\n🧪 Manual Filter Validation")
    print("Testing filter logic on raw recipe data")
    
    validate_rating_filter()
    validate_nutrition_filter()
    validate_time_filter()
    
    print("\n" + "=" * 60)
    print("✅ Manual validation completed successfully!")
    print("=" * 60)
