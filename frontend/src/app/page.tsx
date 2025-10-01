'use client';

import { useState, useEffect } from 'react';
import { Recipe, SearchFilters, SearchResponse } from '@/types/recipe';
import { apiClient } from '@/lib/api';
import SearchBar from '@/components/SearchBar';
import RecipeCard from '@/components/RecipeCard';
import RecipeCardSkeleton from '@/components/RecipeCardSkeleton';
import LoadingSpinner from '@/components/LoadingSpinner';
import { AlertCircle, TrendingUp, Clock, Users } from 'lucide-react';

export default function HomePage() {
    const [recipes, setRecipes] = useState<Recipe[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchMetric, setSearchMetric] = useState<'tfidf' | 'bm25'>('bm25');
    const [cuisines, setCuisines] = useState<string[]>([]);
    const [stats, setStats] = useState<{ total_docs: number; total_terms: number; avg_doc_length: number } | null>(null);

    // Load initial data
    useEffect(() => {
        loadInitialData();
        loadCuisines();
        loadStats();
    }, []);

    const loadInitialData = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await apiClient.searchRecipes({
                query: '',
                metric: 'bm25',
                per_page: 12
            });
            setRecipes(response.results || response.recipes || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load recipes');
        } finally {
            setLoading(false);
        }
    };

    const loadCuisines = async () => {
        try {
            const response = await apiClient.getCuisines();
            setCuisines(response.cuisines);
        } catch (err) {
            console.error('Failed to load cuisines:', err);
        }
    };

    const loadStats = async () => {
        try {
            const response = await apiClient.getStats();
            setStats(response);
        } catch (err) {
            console.error('Failed to load stats:', err);
        }
    };

    const handleSearch = async (query: string, filters: SearchFilters) => {
        setLoading(true);
        setError(null);
        setSearchQuery(query);

        try {
            const response = await apiClient.searchRecipes({
                query,
                metric: searchMetric,
                per_page: 20,
                filters
            });
            setRecipes(response.results || response.recipes || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Search failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen">
            {/* Hero Section */}
            <section className="bg-gradient-to-br from-primary-50 via-white to-secondary-50 py-16 sm:py-24">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-12">
                        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
                            Discover Amazing
                            <span className="text-primary-600 block">Recipes</span>
                        </h1>
                        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
                            Search through thousands of delicious recipes with detailed instructions,
                            ingredients, and nutritional information.
                        </p>

                        {/* Stats */}
                        {stats && stats.total_docs && (
                            <div className="flex flex-wrap justify-center gap-8 mb-12">
                                <div className="text-center">
                                    <div className="text-3xl font-bold text-primary-600">{stats.total_docs.toLocaleString()}</div>
                                    <div className="text-sm text-gray-600">Recipes</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-3xl font-bold text-secondary-600">{stats.total_terms.toLocaleString()}</div>
                                    <div className="text-sm text-gray-600">Indexed Terms</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-3xl font-bold text-gray-700">{Math.round(stats.avg_doc_length)}</div>
                                    <div className="text-sm text-gray-600">Avg Words/Recipe</div>
                                </div>
                            </div>
                        )}

                        {/* Search Bar */}
                        <SearchBar
                            onSearch={handleSearch}
                            loading={loading}
                            initialQuery={searchQuery}
                            cuisines={cuisines}
                        />

                        {/* Search Options */}
                        <div className="flex justify-center items-center mt-6 space-x-4">
                            <span className="text-sm text-gray-600">Search algorithm:</span>
                            <div className="flex space-x-2">
                                <button
                                    onClick={() => setSearchMetric('bm25')}
                                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${searchMetric === 'bm25'
                                        ? 'bg-primary-100 text-primary-700'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }`}
                                >
                                    BM25
                                </button>
                                <button
                                    onClick={() => setSearchMetric('tfidf')}
                                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${searchMetric === 'tfidf'
                                        ? 'bg-primary-100 text-primary-700'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }`}
                                >
                                    TF-IDF
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Results Section */}
            <section className="py-12">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Results Header */}
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900">
                                {searchQuery ? `Search Results for "${searchQuery}"` : 'Featured Recipes'}
                            </h2>
                            <p className="text-gray-600 mt-1">
                                {recipes.length > 0 && `Found ${recipes.length} recipe${recipes.length !== 1 ? 's' : ''}`}
                                {searchQuery && ` using ${searchMetric.toUpperCase()} algorithm`}
                            </p>
                        </div>

                        <div className="flex items-center space-x-4">
                            {searchQuery && (
                                <div className="flex items-center space-x-2 text-sm text-gray-500">
                                    <TrendingUp className="w-4 h-4" />
                                    <span>Ranked by relevance</span>
                                </div>
                            )}
                            <a
                                href="/recipes"
                                className="text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors"
                            >
                                Browse all recipes →
                            </a>
                        </div>
                    </div>

                    {/* Error State */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
                            <div className="flex items-center">
                                <AlertCircle className="w-6 h-6 text-red-600 mr-3" />
                                <div>
                                    <h3 className="text-lg font-medium text-red-900">Error</h3>
                                    <p className="text-red-700 mt-1">{error}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Loading State */}
                    {loading && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 auto-rows-fr">
                            {Array.from({ length: 8 }).map((_, index) => (
                                <RecipeCardSkeleton key={index} />
                            ))}
                        </div>
                    )}

                    {/* Empty State */}
                    {!loading && !error && recipes.length === 0 && (
                        <div className="text-center py-16">
                            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                                <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-medium text-gray-900 mb-2">No recipes found</h3>
                            <p className="text-gray-600 mb-6">
                                {searchQuery
                                    ? "Try adjusting your search terms or filters"
                                    : "No recipes available at the moment"
                                }
                            </p>
                            {searchQuery && (
                                <button
                                    onClick={() => handleSearch('', {})}
                                    className="btn-primary"
                                >
                                    Show all recipes
                                </button>
                            )}
                        </div>
                    )}

                    {/* Recipes Grid */}
                    {!loading && recipes.length > 0 && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 auto-rows-fr">
                            {recipes.map((recipe, index) => (
                                <RecipeCard
                                    key={recipe.id}
                                    recipe={recipe}
                                    showScore={!!searchQuery}
                                    priority={index < 4}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </section>

            {/* Features Section */}
            {!searchQuery && (
                <section className="bg-gray-50 py-16">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center mb-12">
                            <h2 className="text-3xl font-bold text-gray-900 mb-4">
                                Why Choose Our Recipe Search?
                            </h2>
                            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                                Advanced search algorithms and comprehensive recipe data to help you find exactly what you're looking for.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                            <div className="text-center p-6">
                                <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <TrendingUp className="w-8 h-8 text-primary-600" />
                                </div>
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">Smart Search</h3>
                                <p className="text-gray-600">
                                    Advanced BM25 and TF-IDF algorithms provide highly relevant search results.
                                </p>
                            </div>

                            <div className="text-center p-6">
                                <div className="w-16 h-16 bg-secondary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Clock className="w-8 h-8 text-secondary-600" />
                                </div>
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">Detailed Information</h3>
                                <p className="text-gray-600">
                                    Complete nutritional data, cooking times, and step-by-step instructions.
                                </p>
                            </div>

                            <div className="text-center p-6">
                                <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Users className="w-8 h-8 text-yellow-600" />
                                </div>
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">Community Driven</h3>
                                <p className="text-gray-600">
                                    Recipes from real cooks with ratings and reviews from the community.
                                </p>
                            </div>
                        </div>
                    </div>
                </section>
            )}
        </div>
    );
}
