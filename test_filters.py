#!/usr/bin/env python3
"""
Test script to validate all filtering functionality.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from search_cli.run import RobustRecipeSearcher

def test_filters():
    """Test various filters to ensure they work correctly."""
    
    print("🧪 Testing Food Recipes IR Pipeline Filters\n")
    print("=" * 60)
    
    # Initialize searcher
    try:
        searcher = RobustRecipeSearcher('data/index/v1')
        print("✅ Search engine initialized successfully\n")
    except Exception as e:
        print(f"❌ Failed to initialize search engine: {e}")
        return False
    
    # Test 1: Rating filter
    print("\n" + "=" * 60)
    print("Test 1: Rating Filter (min_rating=4.0)")
    print("=" * 60)
    try:
        results = searcher.search_bm25('', limit=5, filters={'min_rating': 4.0})
        print(f"Found {len(results)} results")
        for doc_id, score, snippet in results[:3]:
            recipe = searcher._get_recipe_data(doc_id)
            if recipe:
                rating = recipe.get('ratings', {}).get('rating', 'N/A')
                print(f"  - {recipe.get('title', 'Unknown')[:50]}")
                print(f"    Rating: {rating}, Review Count: {recipe.get('ratings', {}).get('review_count', 'N/A')}")
        print("✅ Rating filter test passed")
    except Exception as e:
        print(f"❌ Rating filter test failed: {e}")
        return False
    
    # Test 2: Review count filter
    print("\n" + "=" * 60)
    print("Test 2: Review Count Filter (min_review_count=50)")
    print("=" * 60)
    try:
        results = searcher.search_bm25('', limit=5, filters={'min_review_count': 50})
        print(f"Found {len(results)} results")
        for doc_id, score, snippet in results[:3]:
            recipe = searcher._get_recipe_data(doc_id)
            if recipe:
                rating = recipe.get('ratings', {}).get('rating', 'N/A')
                review_count = recipe.get('ratings', {}).get('review_count', 'N/A')
                print(f"  - {recipe.get('title', 'Unknown')[:50]}")
                print(f"    Rating: {rating}, Review Count: {review_count}")
        print("✅ Review count filter test passed")
    except Exception as e:
        print(f"❌ Review count filter test failed: {e}")
        return False
    
    # Test 3: Time filter
    print("\n" + "=" * 60)
    print("Test 3: Time Filter (max_total_minutes=30)")
    print("=" * 60)
    try:
        results = searcher.search_bm25('', limit=5, filters={'max_total_minutes': 30})
        print(f"Found {len(results)} results")
        for doc_id, score, snippet in results[:3]:
            recipe = searcher._get_recipe_data(doc_id)
            if recipe:
                total_time = recipe.get('times', {}).get('total', 'N/A')
                print(f"  - {recipe.get('title', 'Unknown')[:50]}")
                print(f"    Total Time: {total_time} minutes")
        print("✅ Time filter test passed")
    except Exception as e:
        print(f"❌ Time filter test failed: {e}")
        return False
    
    # Test 4: Nutrition filter (calories)
    print("\n" + "=" * 60)
    print("Test 4: Nutrition Filter (max_calories=300)")
    print("=" * 60)
    try:
        results = searcher.search_bm25('', limit=5, filters={'max_calories': 300})
        print(f"Found {len(results)} results")
        for doc_id, score, snippet in results[:3]:
            recipe = searcher._get_recipe_data(doc_id)
            if recipe:
                calories = recipe.get('nutrition', {}).get('calories', 'N/A')
                print(f"  - {recipe.get('title', 'Unknown')[:50]}")
                print(f"    Calories: {calories}")
        print("✅ Nutrition filter test passed")
    except Exception as e:
        print(f"❌ Nutrition filter test failed: {e}")
        return False
    
    # Test 5: Combined filters
    print("\n" + "=" * 60)
    print("Test 5: Combined Filters (rating>=3.5, time<=45min, calories<=500)")
    print("=" * 60)
    try:
        results = searcher.search_bm25('', limit=5, filters={
            'min_rating': 3.5,
            'max_total_minutes': 45,
            'max_calories': 500
        })
        print(f"Found {len(results)} results")
        for doc_id, score, snippet in results[:3]:
            recipe = searcher._get_recipe_data(doc_id)
            if recipe:
                rating = recipe.get('ratings', {}).get('rating', 'N/A')
                total_time = recipe.get('times', {}).get('total', 'N/A')
                calories = recipe.get('nutrition', {}).get('calories', 'N/A')
                print(f"  - {recipe.get('title', 'Unknown')[:50]}")
                print(f"    Rating: {rating}, Time: {total_time}min, Calories: {calories}")
        print("✅ Combined filters test passed")
    except Exception as e:
        print(f"❌ Combined filters test failed: {e}")
        return False
    
    # Test 6: Cuisine filter
    print("\n" + "=" * 60)
    print("Test 6: Cuisine Filter (Italian)")
    print("=" * 60)
    try:
        results = searcher.search_bm25('', limit=5, filters={'cuisine': ['Italian']})
        print(f"Found {len(results)} results")
        for doc_id, score, snippet in results[:3]:
            recipe = searcher._get_recipe_data(doc_id)
            if recipe:
                cuisines = recipe.get('cuisine', [])
                print(f"  - {recipe.get('title', 'Unknown')[:50]}")
                print(f"    Cuisines: {', '.join(cuisines)}")
        print("✅ Cuisine filter test passed")
    except Exception as e:
        print(f"❌ Cuisine filter test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All filter tests completed successfully!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_filters()
    sys.exit(0 if success else 1)
