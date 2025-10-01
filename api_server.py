#!/usr/bin/env python3
"""
Flask API Server for Food Recipes Search
Provides REST API endpoints for the frontend.
"""

import json
import logging
import sys
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from search_cli.run import RobustRecipeSearcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global searcher instance
searcher = None

def initialize_searcher():
    """Initialize the search engine."""
    global searcher
    try:
        searcher = RobustRecipeSearcher('data/index/v1')
        logger.info("Search engine initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize search engine: {e}")
        return False

def get_default_recipes(limit=10000):
    """Get default recipes from the normalized data."""
    try:
        # Try different normalized data paths
        possible_paths = [
            'data/normalized/recipes.jsonl'
        ]
        
        recipes = []
        for path in possible_paths:
            if Path(path).exists():
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                recipe = json.loads(line)
                                recipes.append(recipe)
                                if len(recipes) >= limit:
                                    break
                            except json.JSONDecodeError:
                                continue
                break
        
        # If no recipes found, create some sample data
        if not recipes:
            recipes = [
                {
                    'id': f'sample_{i}',
                    'title': f'Sample Recipe {i}',
                    'description': f'This is a sample recipe number {i} for testing purposes.',
                    'ingredients': [f'Ingredient {i}A', f'Ingredient {i}B', f'Ingredient {i}C'],
                    'instructions': [f'Step 1 for recipe {i}', f'Step 2 for recipe {i}', f'Step 3 for recipe {i}'],
                    'times': {'total': 30 + i * 5, 'prep': 10 + i, 'cook': 20 + i * 2},
                    'yield': 4 + i,
                    'cuisine': ['Sample Cuisine'],
                    'difficulty': 'medium',
                    'author': f'Chef {i}',
                    'score': 0.8 + i * 0.01
                }
                for i in range(1, min(limit + 1, 21))
            ]
        
        return recipes[:limit]
        
    except Exception as e:
        logger.error(f"Error loading default recipes: {e}")
        return []

def get_total_recipe_count():
    """Get total number of recipes in the database."""
    try:
        recipes_file = Path('data/normalized/recipes.jsonl')
        if not recipes_file.exists():
            return 0
        
        count = 0
        with open(recipes_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
    except Exception as e:
        logger.error(f"Error counting recipes: {e}")
        return 0

def get_default_recipes_paginated(offset, limit):
    """Get paginated default recipes from the normalized data."""
    try:
        recipes_file = Path('data/normalized/recipes.jsonl')
        if not recipes_file.exists():
            return []
        
        recipes = []
        current_offset = 0
        
        with open(recipes_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    if current_offset >= offset:
                        try:
                            recipe = json.loads(line)
                            recipes.append(recipe)
                            if len(recipes) >= limit:
                                break
                        except json.JSONDecodeError:
                            continue
                    current_offset += 1
        
        return recipes
        
    except Exception as e:
        logger.error(f"Error loading paginated recipes: {e}")
        return []

@app.route('/api/search', methods=['POST'])
def search():
    """Search endpoint with pagination support."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        metric = data.get('metric', 'bm25')
        page = data.get('page', 1)
        per_page = data.get('per_page', 20)
        filters = data.get('filters', {})
        
        # Calculate pagination
        offset = (page - 1) * per_page
        limit = per_page
        
        # Handle empty query for default recipes
        if not query:
            # If filters are applied, use search engine to filter results
            if filters:
                try:
                    # Use search engine with empty query but apply filters
                    if metric == 'bm25':
                        results = searcher.search_bm25('', limit, filters, offset)
                    else:
                        results = searcher.search_tfidf('', limit, filters, offset)
                    
                    # Get total count for filtered results
                    total_results = searcher.get_total_results('', filters)
                    
                    # Convert results to recipe format
                    recipe_results = []
                    for doc_id, score, snippet in results:
                        recipe_data = searcher._get_recipe_data(doc_id)
                        if recipe_data:
                            recipe_data['score'] = score
                            recipe_data['snippet'] = snippet
                            recipe_results.append(recipe_data)
                    
                    stats = searcher.get_stats()
                    
                    return jsonify({
                        'results': recipe_results,
                        'total_results': total_results,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': (total_results + per_page - 1) // per_page,
                        'stats': stats,
                        'query': '',
                        'metric': metric,
                        'filters': filters
                    })
                except Exception as e:
                    logger.error(f"Filtered search error: {e}")
                    return jsonify({'error': 'Failed to apply filters'}), 500
            else:
                # No filters, return paginated default recipes
                try:
                    # Get total count of recipes
                    total_recipes = get_total_recipe_count()
                    
                    # Get paginated recipes
                    default_recipes = get_default_recipes_paginated(offset, limit)
                    stats = searcher.get_stats()
                    
                    return jsonify({
                        'results': default_recipes,
                        'total_results': total_recipes,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': (total_recipes + per_page - 1) // per_page,
                        'stats': stats,
                        'query': '',
                        'metric': metric
                    })
                except Exception as e:
                    logger.error(f"Default recipes error: {e}")
                    return jsonify({'error': 'Failed to load default recipes'}), 500
        
        if not searcher:
            return jsonify({'error': 'Search engine not initialized'}), 500
        
        # Perform search with pagination
        if metric == 'bm25':
            search_results = searcher.search_bm25(query, limit, filters, offset)
        else:
            search_results = searcher.search_tfidf(query, limit, filters, offset)
        
        # Convert results to recipe format
        recipe_results = []
        for doc_id, score, snippet in search_results:
            recipe_data = searcher._get_recipe_data(doc_id)
            if recipe_data:
                recipe_data['score'] = score
                recipe_data['snippet'] = snippet
                recipe_results.append(recipe_data)
        
        # Get total count for search results
        total_results = searcher.get_total_results(query, filters)
        
        # Get statistics
        stats = searcher.get_stats()
        
        return jsonify({
            'results': recipe_results,
            'total_results': total_results,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_results + per_page - 1) // per_page,
            'stats': stats,
            'query': query,
            'metric': metric,
            'filters': filters
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'searcher_initialized': searcher is not None
    })

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get search engine statistics."""
    if not searcher:
        return jsonify({'error': 'Search engine not initialized'}), 500
    
    try:
        stats = searcher.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get detailed recipe information."""
    try:
        # Load the normalized recipes to get full details
        recipes_file = Path('data/normalized/recipes.jsonl')
        if not recipes_file.exists():
            return jsonify({'error': 'Recipes not found'}), 404
        
        with open(recipes_file, 'r', encoding='utf-8') as f:
            for line in f:
                recipe = json.loads(line)
                if recipe.get('id') == recipe_id:
                    return jsonify(recipe)
        
        return jsonify({'error': 'Recipe not found'}), 404
        
    except Exception as e:
        logger.error(f"Recipe fetch error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ingredients', methods=['GET'])
def get_ingredients():
    """Get list of all ingredients."""
    try:
        ingredients = set()
        recipes_file = Path('data/normalized/recipes.jsonl')
        
        if not recipes_file.exists():
            return jsonify({'ingredients': []})
        
        with open(recipes_file, 'r', encoding='utf-8') as f:
            for line in f:
                recipe = json.loads(line)
                if 'ingredients' in recipe:
                    for ingredient in recipe['ingredients']:
                        # Extract main ingredient name (before any quantities)
                        clean_ingredient = ingredient.split(' ', 1)[-1].strip()
                        if clean_ingredient:
                            ingredients.add(clean_ingredient.lower())
        
        return jsonify({'ingredients': sorted(list(ingredients))})
        
    except Exception as e:
        logger.error(f"Ingredients fetch error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/cuisines', methods=['GET'])
def get_cuisines():
    """Get list of all cuisines."""
    try:
        cuisines = set()
        recipes_file = Path('data/normalized/recipes.jsonl')
        
        if not recipes_file.exists():
            return jsonify({'cuisines': []})
        
        with open(recipes_file, 'r', encoding='utf-8') as f:
            for line in f:
                recipe = json.loads(line)
                if 'cuisine' in recipe and recipe['cuisine']:
                    for cuisine in recipe['cuisine']:
                        if cuisine.strip():
                            cuisines.add(cuisine.strip().lower())
        
        return jsonify({'cuisines': sorted(list(cuisines))})
        
    except Exception as e:
        logger.error(f"Cuisines fetch error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get organized categories for filtering."""
    try:
        categories_file = Path('data/categories.json')
        
        if categories_file.exists():
            with open(categories_file, 'r', encoding='utf-8') as f:
                categories = json.load(f)
        else:
            # Fallback to basic categories if file doesn't exist
            categories = {
                'cuisines': {},
                'meal_types': {},
                'dietary': {},
                'cooking_methods': {},
                'ingredients': {}
            }
        
        return jsonify(categories)
        
    except Exception as e:
        logger.error(f"Categories error: {e}")
        return jsonify({'error': 'Failed to load categories'}), 500

# Serve static files for development
@app.route('/')
def serve_frontend():
    """Serve the frontend application."""
    return send_from_directory('frontend/build', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('frontend/build', path)

if __name__ == '__main__':
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Food Recipes API Server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    args = parser.parse_args()
    
    # Initialize search engine
    if not initialize_searcher():
        logger.error("Failed to initialize search engine. Exiting.")
        sys.exit(1)
    
    # Run the Flask app
    logger.info(f"Starting Food Recipes API server on port {args.port}...")
    app.run(host='0.0.0.0', port=args.port, debug=True)

