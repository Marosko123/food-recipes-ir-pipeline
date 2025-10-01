'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { Recipe } from '@/types/recipe';
import { apiClient } from '@/lib/api';
import { parseRecipeSlug, formatTime, formatDifficulty, formatRating, getPlaceholderImage } from '@/lib/utils';
import {
    Clock, Users, Star, ChefHat, ArrowLeft, ExternalLink,
    Calendar, User, Utensils, Heart, Share2, Printer,
    Flame, Zap, Wheat, Droplets, Scale, ChevronLeft, ChevronRight
} from 'lucide-react';

export default function RecipeDetailPage() {
    const params = useParams();
    const router = useRouter();
    const [recipe, setRecipe] = useState<Recipe | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'nutrition' | 'instructions'>('overview');

    // Navigation state
    const [allRecipeIds, setAllRecipeIds] = useState<string[]>([]);
    const [currentIndex, setCurrentIndex] = useState<number>(-1);
    const [navigationLoading, setNavigationLoading] = useState(false);

    useEffect(() => {
        if (params.slug) {
            loadRecipe(params.slug as string);
        }
    }, [params.slug]);

    // Load all recipe IDs for navigation
    useEffect(() => {
        loadAllRecipeIds();
    }, []);

    // Update current index when recipe changes
    useEffect(() => {
        if (recipe && allRecipeIds.length > 0) {
            const index = allRecipeIds.indexOf(recipe.id.toString());
            setCurrentIndex(index);
        }
    }, [recipe, allRecipeIds]);

    // Keyboard navigation
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            // Only handle navigation if we have recipes and no input is focused
            if (allRecipeIds.length <= 1 || currentIndex === -1 || navigationLoading) return;
            if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') return;

            switch (event.key) {
                case 'ArrowLeft':
                case 'h': // Vim-style navigation
                    event.preventDefault();
                    handlePrevious();
                    break;
                case 'ArrowRight':
                case 'l': // Vim-style navigation
                    event.preventDefault();
                    handleNext();
                    break;
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [allRecipeIds, currentIndex, navigationLoading]);

    const loadRecipe = async (slug: string) => {
        setLoading(true);
        setError(null);

        try {
            const parsed = parseRecipeSlug(slug);
            if (!parsed) {
                throw new Error('Invalid recipe URL');
            }

            const recipeData = await apiClient.getRecipe(parsed.id);
            setRecipe(recipeData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load recipe');
        } finally {
            setLoading(false);
        }
    };

    const loadAllRecipeIds = async () => {
        try {
            // Get all recipes (without search query to get full list)
            const response = await apiClient.searchRecipes({
                query: '',
                metric: 'bm25',
                page: 1,
                per_page: 1000, // Get a large number to cover all recipes
                filters: {}
            });

            // Handle both 'results' and 'recipes' field names
            const recipes = response.results || response.recipes || [];
            const ids = recipes.map(recipe => recipe.id.toString());
            setAllRecipeIds(ids);
        } catch (err) {
            console.error('Failed to load recipe IDs for navigation:', err);
            // If we can't load all IDs, we'll disable navigation
            setAllRecipeIds([]);
        }
    };

    const navigateToRecipe = async (direction: 'prev' | 'next') => {
        if (currentIndex === -1 || allRecipeIds.length === 0) return;

        const newIndex = direction === 'next'
            ? (currentIndex + 1) % allRecipeIds.length
            : (currentIndex - 1 + allRecipeIds.length) % allRecipeIds.length;

        const newRecipeId = allRecipeIds[newIndex];

        setNavigationLoading(true);

        try {
            // Create the new slug format: title-id
            const newRecipeData = await apiClient.getRecipe(newRecipeId);
            const slug = `${newRecipeData.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}-${newRecipeId}`;

            // Navigate to the new recipe
            router.push(`/recipe/${slug}`);
        } catch (err) {
            console.error('Failed to navigate to recipe:', err);
        } finally {
            setNavigationLoading(false);
        }
    };

    const handlePrevious = () => navigateToRecipe('prev');
    const handleNext = () => navigateToRecipe('next');

    const handleShare = async () => {
        if (navigator.share && recipe) {
            try {
                await navigator.share({
                    title: recipe.title,
                    text: recipe.description,
                    url: window.location.href,
                });
            } catch (err) {
                // Fallback to copying URL
                navigator.clipboard.writeText(window.location.href);
            }
        } else if (recipe) {
            navigator.clipboard.writeText(window.location.href);
        }
    };

    const handlePrint = () => {
        window.print();
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading recipe...</p>
                </div>
            </div>
        );
    }

    if (error || !recipe) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center max-w-md mx-auto px-4">
                    <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <ChefHat className="w-12 h-12 text-red-600" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900 mb-4">Recipe Not Found</h1>
                    <p className="text-gray-600 mb-6">
                        {error || "The recipe you're looking for doesn't exist or has been removed."}
                    </p>
                    <Link href="/" className="btn-primary">
                        Back to Home
                    </Link>
                </div>
            </div>
        );
    }

    const rating = formatRating(recipe.ratings?.rating);
    const reviewCount = recipe.ratings?.review_count;

    return (
        <div className="min-h-screen bg-white">
            {/* Header */}
            <div className="bg-gray-50 border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={() => router.back()}
                                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
                            >
                                <ArrowLeft className="w-5 h-5 mr-2" />
                                Back
                            </button>

                            {/* Recipe Navigation */}
                            {allRecipeIds.length > 1 && currentIndex !== -1 && (
                                <div className="hidden sm:flex items-center space-x-2 border-l border-gray-300 pl-4">
                                    <button
                                        onClick={handlePrevious}
                                        disabled={navigationLoading}
                                        className="flex items-center px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                        title="Previous recipe"
                                    >
                                        <ChevronLeft className="w-4 h-4 mr-1" />
                                        Previous
                                    </button>
                                    <span className="text-sm text-gray-500 px-2">
                                        {currentIndex + 1} of {allRecipeIds.length}
                                    </span>
                                    <button
                                        onClick={handleNext}
                                        disabled={navigationLoading}
                                        className="flex items-center px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                        title="Next recipe"
                                    >
                                        Next
                                        <ChevronRight className="w-4 h-4 ml-1" />
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="flex items-center space-x-2">
                            <button
                                onClick={handleShare}
                                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-lg transition-colors"
                                title="Share recipe"
                            >
                                <Share2 className="w-5 h-5" />
                            </button>
                            <button
                                onClick={handlePrint}
                                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-lg transition-colors"
                                title="Print recipe"
                            >
                                <Printer className="w-5 h-5" />
                            </button>
                            <a
                                href={recipe.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-lg transition-colors"
                                title="View original"
                            >
                                <ExternalLink className="w-5 h-5" />
                            </a>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Main Content */}
                    <div className="lg:col-span-2">
                        {/* Recipe Header */}
                        <div className="mb-8">
                            <div className="relative h-64 sm:h-80 rounded-xl overflow-hidden mb-6">
                                <Image
                                    src={recipe.image || getPlaceholderImage()}
                                    alt={recipe.title}
                                    fill
                                    className="object-cover"
                                    priority
                                    sizes="(max-width: 768px) 100vw, 66vw"
                                />
                                {recipe.difficulty && (
                                    <div className="absolute top-4 left-4">
                                        <span className="badge badge-primary">
                                            <ChefHat className="w-3 h-3 mr-1" />
                                            {formatDifficulty(recipe.difficulty)}
                                        </span>
                                    </div>
                                )}
                            </div>

                            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
                                {recipe.title}
                            </h1>

                            {recipe.description && (
                                <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                                    {recipe.description}
                                </p>
                            )}

                            {/* Meta Info */}
                            <div className="flex flex-wrap items-center gap-6 mb-6">
                                {recipe.times?.total && (
                                    <div className="flex items-center text-gray-600">
                                        <Clock className="w-5 h-5 mr-2" />
                                        <span className="font-medium">Total: {formatTime(recipe.times.total)}</span>
                                    </div>
                                )}
                                {recipe.times?.prep && (
                                    <div className="flex items-center text-gray-600">
                                        <Utensils className="w-5 h-5 mr-2" />
                                        <span>Prep: {formatTime(recipe.times.prep)}</span>
                                    </div>
                                )}
                                {recipe.times?.cook && (
                                    <div className="flex items-center text-gray-600">
                                        <Flame className="w-5 h-5 mr-2" />
                                        <span>Cook: {formatTime(recipe.times.cook)}</span>
                                    </div>
                                )}
                                {recipe.yield && (
                                    <div className="flex items-center text-gray-600">
                                        <Users className="w-5 h-5 mr-2" />
                                        <span>{recipe.yield}</span>
                                    </div>
                                )}
                                {rating > 0 && (
                                    <div className="flex items-center">
                                        <Star className="w-5 h-5 text-yellow-400 mr-1" />
                                        <span className="font-medium text-gray-900">{rating.toFixed(1)}</span>
                                        {reviewCount && (
                                            <span className="text-gray-600 ml-1">({reviewCount} reviews)</span>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Author & Date */}
                            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-6">
                                {recipe.author && (
                                    <div className="flex items-center">
                                        <User className="w-4 h-4 mr-1" />
                                        <span>by {recipe.author}</span>
                                    </div>
                                )}
                                {recipe.date_published && (
                                    <div className="flex items-center">
                                        <Calendar className="w-4 h-4 mr-1" />
                                        <span>{new Date(recipe.date_published).toLocaleDateString()}</span>
                                    </div>
                                )}
                            </div>

                            {/* Tags */}
                            <div className="flex flex-wrap gap-2 mb-8">
                                {recipe.cuisine.map((cuisine, index) => (
                                    <span key={`cuisine-${index}`} className="badge badge-primary">
                                        {cuisine}
                                    </span>
                                ))}
                                {recipe.category.map((category, index) => (
                                    <span key={`category-${index}`} className="badge badge-secondary">
                                        {category}
                                    </span>
                                ))}
                                {recipe.keywords.slice(0, 5).map((keyword, index) => (
                                    <span key={`keyword-${index}`} className="badge badge-gray">
                                        {keyword}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="border-b border-gray-200 mb-8">
                            <nav className="flex space-x-8">
                                {[
                                    { id: 'overview', label: 'Overview', icon: Utensils },
                                    { id: 'nutrition', label: 'Nutrition', icon: Scale },
                                    { id: 'instructions', label: 'Instructions', icon: ChefHat },
                                ].map(({ id, label, icon: Icon }) => (
                                    <button
                                        key={id}
                                        onClick={() => setActiveTab(id as any)}
                                        className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === id
                                            ? 'border-primary-500 text-primary-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                            }`}
                                    >
                                        <Icon className="w-4 h-4 mr-2" />
                                        {label}
                                    </button>
                                ))}
                            </nav>
                        </div>

                        {/* Tab Content */}
                        {activeTab === 'overview' && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {/* Ingredients */}
                                <div>
                                    <h3 className="text-xl font-bold text-gray-900 mb-4">Ingredients</h3>
                                    <ul className="space-y-3">
                                        {recipe.ingredients.map((ingredient, index) => (
                                            <li key={index} className="flex items-start">
                                                <span className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                                                <span className="text-gray-700">{ingredient}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* Tools */}
                                {recipe.tools.length > 0 && (
                                    <div>
                                        <h3 className="text-xl font-bold text-gray-900 mb-4">Tools Needed</h3>
                                        <ul className="space-y-3">
                                            {recipe.tools.map((tool, index) => (
                                                <li key={index} className="flex items-start">
                                                    <Utensils className="w-4 h-4 text-gray-400 mt-1 mr-3 flex-shrink-0" />
                                                    <span className="text-gray-700">{tool}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'nutrition' && recipe.nutrition && (
                            <div>
                                <h3 className="text-xl font-bold text-gray-900 mb-6">Nutritional Information</h3>
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                    {Object.entries(recipe.nutrition).map(([key, value]) => {
                                        if (!value) return null;

                                        const icons: Record<string, any> = {
                                            calories: Flame,
                                            fat: Droplets,
                                            carbohydrates: Wheat,
                                            protein: Zap,
                                        };

                                        const Icon = icons[key] || Scale;
                                        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

                                        return (
                                            <div key={key} className="bg-gray-50 rounded-lg p-4 text-center">
                                                <Icon className="w-6 h-6 text-primary-600 mx-auto mb-2" />
                                                <div className="font-bold text-lg text-gray-900">{value}</div>
                                                <div className="text-sm text-gray-600">{label}</div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {activeTab === 'instructions' && (
                            <div>
                                <h3 className="text-xl font-bold text-gray-900 mb-6">Instructions</h3>
                                <ol className="space-y-6">
                                    {recipe.instructions.map((instruction, index) => (
                                        <li key={index} className="flex">
                                            <div className="flex-shrink-0 w-8 h-8 bg-primary-500 text-white rounded-full flex items-center justify-center font-bold text-sm mr-4 mt-1">
                                                {index + 1}
                                            </div>
                                            <div className="flex-1">
                                                <p className="text-gray-700 leading-relaxed">{instruction}</p>
                                            </div>
                                        </li>
                                    ))}
                                </ol>
                            </div>
                        )}
                    </div>

                    {/* Sidebar */}
                    <div className="lg:col-span-1">
                        <div className="sticky top-24 space-y-6">
                            {/* Quick Facts */}
                            <div className="bg-gray-50 rounded-xl p-6">
                                <h3 className="font-bold text-gray-900 mb-4">Quick Facts</h3>
                                <div className="space-y-3">
                                    {recipe.times?.prep && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Prep Time</span>
                                            <span className="font-medium">{formatTime(recipe.times.prep)}</span>
                                        </div>
                                    )}
                                    {recipe.times?.cook && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Cook Time</span>
                                            <span className="font-medium">{formatTime(recipe.times.cook)}</span>
                                        </div>
                                    )}
                                    {recipe.times?.total && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Total Time</span>
                                            <span className="font-medium">{formatTime(recipe.times.total)}</span>
                                        </div>
                                    )}
                                    {recipe.yield && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Servings</span>
                                            <span className="font-medium">{recipe.yield}</span>
                                        </div>
                                    )}
                                    {recipe.difficulty && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Difficulty</span>
                                            <span className="font-medium">{formatDifficulty(recipe.difficulty)}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Nutrition Summary */}
                            {recipe.nutrition?.calories && (
                                <div className="bg-primary-50 rounded-xl p-6">
                                    <h3 className="font-bold text-gray-900 mb-4">Nutrition Highlights</h3>
                                    <div className="space-y-3">
                                        <div className="flex justify-between">
                                            <span className="text-gray-700">Calories</span>
                                            <span className="font-bold text-primary-700">{recipe.nutrition.calories}</span>
                                        </div>
                                        {recipe.nutrition.protein && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-700">Protein</span>
                                                <span className="font-medium">{recipe.nutrition.protein}g</span>
                                            </div>
                                        )}
                                        {recipe.nutrition.carbohydrates && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-700">Carbs</span>
                                                <span className="font-medium">{recipe.nutrition.carbohydrates}g</span>
                                            </div>
                                        )}
                                        {recipe.nutrition.fat && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-700">Fat</span>
                                                <span className="font-medium">{recipe.nutrition.fat}g</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Actions */}
                            <div className="space-y-3">
                                <button
                                    onClick={handleShare}
                                    className="w-full btn-secondary flex items-center justify-center"
                                >
                                    <Share2 className="w-4 h-4 mr-2" />
                                    Share Recipe
                                </button>
                                <button
                                    onClick={handlePrint}
                                    className="w-full btn-secondary flex items-center justify-center"
                                >
                                    <Printer className="w-4 h-4 mr-2" />
                                    Print Recipe
                                </button>
                                <a
                                    href={recipe.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="w-full btn-primary flex items-center justify-center"
                                >
                                    <ExternalLink className="w-4 h-4 mr-2" />
                                    View Original
                                </a>
                            </div>

                            {/* Keyboard Shortcuts */}
                            {allRecipeIds.length > 1 && (
                                <div className="bg-gray-50 rounded-lg p-4 mt-6">
                                    <h4 className="text-sm font-medium text-gray-900 mb-2">Keyboard Shortcuts</h4>
                                    <div className="space-y-1 text-sm text-gray-600">
                                        <div className="flex justify-between">
                                            <span>Previous recipe</span>
                                            <span className="font-mono bg-gray-200 px-2 py-0.5 rounded text-xs">← or H</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Next recipe</span>
                                            <span className="font-mono bg-gray-200 px-2 py-0.5 rounded text-xs">→ or L</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Bottom Navigation Section */}
                {allRecipeIds.length > 1 && currentIndex !== -1 && (
                    <div className="border-t border-gray-200 mt-16 pt-8">
                        <div className="flex items-center justify-between">
                            <button
                                onClick={handlePrevious}
                                disabled={navigationLoading}
                                className="group flex items-center space-x-3 p-4 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <div className="p-2 bg-white rounded-lg shadow-sm group-hover:shadow-md transition-shadow">
                                    <ChevronLeft className="w-5 h-5 text-gray-600" />
                                </div>
                                <div className="text-left">
                                    <div className="text-sm text-gray-500 uppercase tracking-wider font-medium">Previous</div>
                                    <div className="text-gray-900 font-medium">
                                        {navigationLoading ? 'Loading...' : 'Recipe'}
                                    </div>
                                </div>
                            </button>

                            <div className="text-center">
                                <div className="text-sm text-gray-500 mb-1">Recipe Navigation</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {currentIndex + 1} of {allRecipeIds.length}
                                </div>
                            </div>

                            <button
                                onClick={handleNext}
                                disabled={navigationLoading}
                                className="group flex items-center space-x-3 p-4 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <div className="text-right">
                                    <div className="text-sm text-gray-500 uppercase tracking-wider font-medium">Next</div>
                                    <div className="text-gray-900 font-medium">
                                        {navigationLoading ? 'Loading...' : 'Recipe'}
                                    </div>
                                </div>
                                <div className="p-2 bg-white rounded-lg shadow-sm group-hover:shadow-md transition-shadow">
                                    <ChevronRight className="w-5 h-5 text-gray-600" />
                                </div>
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Mobile Floating Navigation */}
            {allRecipeIds.length > 1 && currentIndex !== -1 && (
                <div className="sm:hidden fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
                    <div className="bg-white rounded-full shadow-lg border border-gray-200 px-6 py-3 flex items-center space-x-4">
                        <button
                            onClick={handlePrevious}
                            disabled={navigationLoading}
                            className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Previous recipe"
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </button>

                        <div className="text-sm text-gray-600 font-medium px-2">
                            {currentIndex + 1}/{allRecipeIds.length}
                        </div>

                        <button
                            onClick={handleNext}
                            disabled={navigationLoading}
                            className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Next recipe"
                        >
                            <ChevronRight className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
