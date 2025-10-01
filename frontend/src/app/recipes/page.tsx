'use client';

import { useState, useEffect, useCallback, useMemo, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Recipe, SearchFilters, FilterOption, SortOption } from '@/types/recipe';
import { apiClient } from '@/lib/api';
import RecipeCard from '@/components/RecipeCard';
import RecipeListItem from '@/components/RecipeListItem';
import RecipeCardSkeleton from '@/components/RecipeCardSkeleton';
import SearchStats from '@/components/SearchStats';
import LoadingSpinner from '@/components/LoadingSpinner';
import MultiSelect from '@/components/MultiSelect';
import {
    Search, SlidersHorizontal, ArrowUpDown, Grid3X3, List,
    ChevronLeft, ChevronRight, ChevronDown, AlertCircle, TrendingUp,
    Clock, Star, ChefHat, Filter, X, Users, Utensils, Flame,
    Calendar, User, Scale, Wheat, Droplets, Zap, MapPin
} from 'lucide-react';
import { cn } from '@/lib/utils';

type ViewMode = 'grid' | 'list';
type LoadingState = 'idle' | 'loading' | 'error';

function RecipesListPageContent() {
    // State management
    const [recipes, setRecipes] = useState<Recipe[]>([]);
    const [loading, setLoading] = useState<LoadingState>('loading');
    const [error, setError] = useState<string | null>(null);

    // Search and filters
    const [searchQuery, setSearchQuery] = useState('');
    const [filters, setFilters] = useState<SearchFilters>({});
    const [tempSearchQuery, setTempSearchQuery] = useState('');

    // UI state
    const [viewMode, setViewMode] = useState<ViewMode>('grid');
    const [showMobileFilters, setShowMobileFilters] = useState(false);
    const [sortBy, setSortBy] = useState('relevance');
    const [searchMetric, setSearchMetric] = useState<'tfidf' | 'bm25'>('bm25');

    // Pagination
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(20);
    const [pageInput, setPageInput] = useState('');

    // Filter options
    const [cuisines, setCuisines] = useState<FilterOption[]>([]);
    const [categories, setCategories] = useState<FilterOption[]>([]);
    const [ingredients, setIngredients] = useState<FilterOption[]>([]);

    // Collapsible sections state - Most used filters first, cuisines open by default
    const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({
        cuisines: false,      // Most used - open by default
        time: true,           // Very common - second most used
        ingredients: true,    // Essential for dietary needs
        rating: true,         // Quality filter
        categories: true,     // Meal type filtering
        difficulty: true,     // Skill level
        servings: true,       // Portion size
        keywords: true,       // Text search
        nutrition: true,      // Health-conscious users
        author: true,         // Less common
        date: true,           // Rarely used
        image: true           // Rarely used
    });

    // Stats
    const [totalResults, setTotalResults] = useState(0);
    const [searchTime, setSearchTime] = useState<number | null>(null);

    const router = useRouter();
    const searchParams = useSearchParams();

    // Sort options
    const sortOptions: SortOption[] = [
        { value: 'relevance', label: 'Relevance', direction: 'desc' },
        { value: 'rating', label: 'Rating', direction: 'desc' },
        { value: 'time_asc', label: 'Cooking Time (Low to High)', direction: 'asc' },
        { value: 'time_desc', label: 'Cooking Time (High to Low)', direction: 'desc' },
        { value: 'title', label: 'Title (A-Z)', direction: 'asc' },
        { value: 'date', label: 'Date Published', direction: 'desc' },
    ];

    // Initialize from URL parameters
    useEffect(() => {
        const query = searchParams.get('q') || '';
        const page = parseInt(searchParams.get('page') || '1');
        const sort = searchParams.get('sort') || 'relevance';
        const metric = (searchParams.get('metric') as 'tfidf' | 'bm25') || 'bm25';
        const view = (searchParams.get('view') as ViewMode) || 'grid';

        setSearchQuery(query);
        setTempSearchQuery(query);
        setCurrentPage(page);
        setSortBy(sort);
        setSearchMetric(metric);
        setViewMode(view);

        // Parse filters from URL
        const urlFilters: SearchFilters = {};
        const maxTime = searchParams.get('max_time');
        const minTime = searchParams.get('min_time');
        const minPrepTime = searchParams.get('min_prep_time');
        const maxPrepTime = searchParams.get('max_prep_time');
        const minCookTime = searchParams.get('min_cook_time');
        const maxCookTime = searchParams.get('max_cook_time');
        const minServings = searchParams.get('min_servings');
        const maxServings = searchParams.get('max_servings');
        const difficulty = searchParams.get('difficulty');
        const minRating = searchParams.get('min_rating');
        const minReviewCount = searchParams.get('min_review_count');
        const minCalories = searchParams.get('min_calories');
        const maxCalories = searchParams.get('max_calories');
        const minProtein = searchParams.get('min_protein');
        const maxProtein = searchParams.get('max_protein');
        const minCarbs = searchParams.get('min_carbs');
        const maxCarbs = searchParams.get('max_carbs');
        const minFat = searchParams.get('min_fat');
        const maxFat = searchParams.get('max_fat');
        const author = searchParams.get('author');
        const authorLocation = searchParams.get('author_location');
        const dateFrom = searchParams.get('date_from');
        const dateTo = searchParams.get('date_to');
        const hasImage = searchParams.get('has_image');
        const cuisineParam = searchParams.get('cuisines') || searchParams.get('cuisine');
        const categoryParam = searchParams.get('categories') || searchParams.get('category');
        const ingredientParam = searchParams.get('ingredients');
        const keywordsParam = searchParams.get('keywords');
        const dietaryParam = searchParams.get('dietary');
        const mealTypeParam = searchParams.get('meal_type');

        if (maxTime) urlFilters.max_total_minutes = parseInt(maxTime);
        if (minTime) urlFilters.min_total_minutes = parseInt(minTime);
        if (minPrepTime) urlFilters.min_prep_minutes = parseInt(minPrepTime);
        if (maxPrepTime) urlFilters.max_prep_minutes = parseInt(maxPrepTime);
        if (minCookTime) urlFilters.min_cook_minutes = parseInt(minCookTime);
        if (maxCookTime) urlFilters.max_cook_minutes = parseInt(maxCookTime);
        if (minServings) urlFilters.min_servings = parseInt(minServings);
        if (maxServings) urlFilters.max_servings = parseInt(maxServings);
        if (difficulty) urlFilters.difficulty = [difficulty];
        if (minRating) urlFilters.min_rating = parseFloat(minRating);
        if (minReviewCount) urlFilters.min_review_count = parseInt(minReviewCount);
        if (minCalories) urlFilters.min_calories = parseInt(minCalories);
        if (maxCalories) urlFilters.max_calories = parseInt(maxCalories);
        if (minProtein) urlFilters.min_protein = parseInt(minProtein);
        if (maxProtein) urlFilters.max_protein = parseInt(maxProtein);
        if (minCarbs) urlFilters.min_carbs = parseInt(minCarbs);
        if (maxCarbs) urlFilters.max_carbs = parseInt(maxCarbs);
        if (minFat) urlFilters.min_fat = parseInt(minFat);
        if (maxFat) urlFilters.max_fat = parseInt(maxFat);
        if (author) urlFilters.author = author;
        if (authorLocation) urlFilters.author_location = authorLocation;
        if (dateFrom) urlFilters.date_from = dateFrom;
        if (dateTo) urlFilters.date_to = dateTo;
        if (hasImage === 'true') urlFilters.has_image = true;
        if (cuisineParam) urlFilters.cuisine = cuisineParam.split(',');
        if (categoryParam) urlFilters.category = categoryParam.split(',');
        if (ingredientParam) urlFilters.ingredients = ingredientParam.split(',');
        if (keywordsParam) urlFilters.keywords = keywordsParam.split(',');
        if (dietaryParam) urlFilters.dietary = dietaryParam.split(',');
        if (mealTypeParam) urlFilters.meal_type = mealTypeParam.split(',');

        setFilters(urlFilters);
    }, [searchParams]);

    // Load filter options
    useEffect(() => {
        loadFilterOptions();
    }, []);

    const loadFilterOptions = async () => {
        try {
            const [cuisinesData, ingredientsData] = await Promise.all([
                apiClient.getCuisines(),
                apiClient.getIngredients(),
            ]);

            // Convert to FilterOption format with counts
            const cuisineOptions = cuisinesData.cuisines.map(cuisine => ({
                value: cuisine,
                label: cuisine.charAt(0).toUpperCase() + cuisine.slice(1),
            }));

            const ingredientOptions = ingredientsData.ingredients.slice(0, 200).map(ingredient => ({
                value: ingredient,
                label: ingredient.charAt(0).toUpperCase() + ingredient.slice(1),
            }));

            // For categories, we'll extract from recipes (simplified for now)
            const categoryOptions = [
                { value: 'appetizer', label: 'Appetizer' },
                { value: 'main', label: 'Main Course' },
                { value: 'dessert', label: 'Dessert' },
                { value: 'side', label: 'Side Dish' },
                { value: 'beverage', label: 'Beverage' },
                { value: 'breakfast', label: 'Breakfast' },
                { value: 'lunch', label: 'Lunch' },
                { value: 'dinner', label: 'Dinner' },
            ];

            setCuisines(cuisineOptions);
            setCategories(categoryOptions);
            setIngredients(ingredientOptions);
        } catch (err) {
            console.error('Failed to load filter options:', err);
        }
    };

    const performSearch = useCallback(async () => {
        setLoading('loading');
        setError(null);

        const startTime = Date.now();

        try {
            const response = await apiClient.searchRecipes({
                query: searchQuery,
                metric: searchMetric,
                per_page: itemsPerPage, // Use server-side pagination
                page: currentPage,
                filters
            });

            // Handle both 'results' and 'recipes' field names
            let results = response.results || response.recipes || [];

            // Apply client-side sorting (since backend doesn't support all sort options)
            const sorted = [...results];
            switch (sortBy) {
                case 'rating':
                    results = sorted.sort((a, b) => {
                        const ratingA = parseFloat(a.ratings?.rating || '0');
                        const ratingB = parseFloat(b.ratings?.rating || '0');
                        return ratingB - ratingA;
                    });
                    break;
                case 'time_asc':
                    results = sorted.sort((a, b) => (a.times?.total || 999) - (b.times?.total || 999));
                    break;
                case 'time_desc':
                    results = sorted.sort((a, b) => (b.times?.total || 0) - (a.times?.total || 0));
                    break;
                case 'title':
                    results = sorted.sort((a, b) => a.title.localeCompare(b.title));
                    break;
                case 'date':
                    results = sorted.sort((a, b) => {
                        const dateA = new Date(a.date_published || '1970-01-01');
                        const dateB = new Date(b.date_published || '1970-01-01');
                        return dateB.getTime() - dateA.getTime();
                    });
                    break;
                case 'relevance':
                default:
                    results = sorted; // Backend already sorted by relevance
            }

            // Use server-side pagination data
            setRecipes(results);
            setTotalResults(response.total_results || results.length);
            setSearchTime(Date.now() - startTime);
            setLoading('idle');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Search failed');
            setLoading('error');
        }
    }, [searchQuery, searchMetric, itemsPerPage, currentPage, filters, sortBy]);

    const sortRecipes = (recipes: Recipe[], sortBy: string): Recipe[] => {
        const sorted = [...recipes];

        switch (sortBy) {
            case 'rating':
                return sorted.sort((a, b) => {
                    const ratingA = parseFloat(a.ratings?.rating || '0');
                    const ratingB = parseFloat(b.ratings?.rating || '0');
                    return ratingB - ratingA;
                });
            case 'time_asc':
                return sorted.sort((a, b) => (a.times?.total || 999) - (b.times?.total || 999));
            case 'time_desc':
                return sorted.sort((a, b) => (b.times?.total || 0) - (a.times?.total || 0));
            case 'title':
                return sorted.sort((a, b) => a.title.localeCompare(b.title));
            case 'date':
                return sorted.sort((a, b) => {
                    const dateA = new Date(a.date_published || '1970-01-01');
                    const dateB = new Date(b.date_published || '1970-01-01');
                    return dateB.getTime() - dateA.getTime();
                });
            case 'relevance':
            default:
                return sorted; // Backend already sorted by relevance
        }
    };

    // Perform search when parameters change
    useEffect(() => {
        performSearch();
    }, [performSearch]);

    const updateURL = useCallback(() => {
        const params = new URLSearchParams();

        if (searchQuery) params.set('q', searchQuery);
        if (currentPage > 1) params.set('page', currentPage.toString());
        if (sortBy !== 'relevance') params.set('sort', sortBy);
        if (searchMetric !== 'bm25') params.set('metric', searchMetric);
        if (viewMode !== 'grid') params.set('view', viewMode);

        if (filters.max_total_minutes) params.set('max_time', filters.max_total_minutes.toString());
        if (filters.min_total_minutes) params.set('min_time', filters.min_total_minutes.toString());
        if (filters.min_prep_minutes) params.set('min_prep_time', filters.min_prep_minutes.toString());
        if (filters.max_prep_minutes) params.set('max_prep_time', filters.max_prep_minutes.toString());
        if (filters.min_cook_minutes) params.set('min_cook_time', filters.min_cook_minutes.toString());
        if (filters.max_cook_minutes) params.set('max_cook_time', filters.max_cook_minutes.toString());
        if (filters.min_servings) params.set('min_servings', filters.min_servings.toString());
        if (filters.max_servings) params.set('max_servings', filters.max_servings.toString());
        if (filters.difficulty) params.set('difficulty', filters.difficulty.join(','));
        if (filters.min_rating) params.set('min_rating', filters.min_rating.toString());
        if (filters.min_review_count) params.set('min_review_count', filters.min_review_count.toString());
        if (filters.min_calories) params.set('min_calories', filters.min_calories.toString());
        if (filters.max_calories) params.set('max_calories', filters.max_calories.toString());
        if (filters.min_protein) params.set('min_protein', filters.min_protein.toString());
        if (filters.max_protein) params.set('max_protein', filters.max_protein.toString());
        if (filters.min_carbs) params.set('min_carbs', filters.min_carbs.toString());
        if (filters.max_carbs) params.set('max_carbs', filters.max_carbs.toString());
        if (filters.min_fat) params.set('min_fat', filters.min_fat.toString());
        if (filters.max_fat) params.set('max_fat', filters.max_fat.toString());
        if (filters.author) params.set('author', filters.author);
        if (filters.author_location) params.set('author_location', filters.author_location);
        if (filters.date_from) params.set('date_from', filters.date_from);
        if (filters.date_to) params.set('date_to', filters.date_to);
        if (filters.has_image) params.set('has_image', 'true');
        if (filters.cuisine?.length) params.set('cuisines', filters.cuisine.join(','));
        if (filters.category?.length) params.set('categories', filters.category.join(','));
        if (filters.ingredients?.length) params.set('ingredients', filters.ingredients.join(','));
        if (filters.keywords?.length) params.set('keywords', filters.keywords.join(','));
        if (filters.dietary?.length) params.set('dietary', filters.dietary.join(','));
        if (filters.meal_type?.length) params.set('meal_type', filters.meal_type.join(','));

        const newURL = `/recipes${params.toString() ? `?${params.toString()}` : ''}`;
        router.replace(newURL);
    }, [searchQuery, currentPage, sortBy, searchMetric, viewMode, filters, router]);

    // Update URL when parameters change
    useEffect(() => {
        updateURL();
    }, [updateURL]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setSearchQuery(tempSearchQuery);
        setCurrentPage(1);
    };

    const handleFiltersChange = (newFilters: SearchFilters) => {
        setFilters(newFilters);
        setCurrentPage(1);
    };

    const handleSortChange = (newSort: string) => {
        setSortBy(newSort);
        setCurrentPage(1);
    };

    const handlePageChange = (page: number) => {
        setCurrentPage(page);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const handlePageInputSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const pageNumber = parseInt(pageInput);
        if (pageNumber >= 1 && pageNumber <= totalPages) {
            handlePageChange(pageNumber);
            setPageInput('');
        }
    };

    const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        // Only allow numbers
        if (value === '' || /^\d+$/.test(value)) {
            setPageInput(value);
        }
    };

    const totalPages = Math.ceil(totalResults / itemsPerPage);

    const getActiveFilterCount = () => {
        return Object.keys(filters).filter(key => {
            const value = filters[key as keyof SearchFilters];
            return value !== undefined && value !== null &&
                (Array.isArray(value) ? value.length > 0 : true);
        }).length;
    };

    const toggleSection = (section: string) => {
        setCollapsedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-6">
                <div className="max-w-7xl mx-auto">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Recipe Collection</h1>
                    <p className="text-gray-600">
                        Discover and explore our complete collection of recipes with advanced search and filtering
                    </p>
                </div>
            </div>

            <div className="max-w-7xl mx-auto">
                {/* Mobile Filter Toggle */}
                <div className="lg:hidden fixed top-20 left-4 z-20">
                    <button
                        onClick={() => setShowMobileFilters(!showMobileFilters)}
                        className="bg-primary-600 text-white p-3 rounded-full shadow-lg hover:bg-primary-700 transition-colors"
                    >
                        <Filter className="w-5 h-5" />
                    </button>
                </div>

                {/* Mobile Filter Overlay */}
                {showMobileFilters && (
                    <div className="lg:hidden fixed inset-0 z-30 bg-black bg-opacity-50" onClick={() => setShowMobileFilters(false)} />
                )}

                {/* Mobile Filter Sidebar */}
                {showMobileFilters && (
                    <div className="lg:hidden fixed top-0 left-0 w-80 h-screen bg-white z-40 overflow-y-auto">
                        <div className="p-6">
                            {/* Mobile Close Button */}
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-semibold text-gray-900">Filters & Search</h3>
                                <button
                                    onClick={() => setShowMobileFilters(false)}
                                    className="p-2 text-gray-500 hover:text-gray-700"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Search Bar */}
                            <div className="mb-6">
                                <form onSubmit={handleSearch} className="space-y-4">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                        <input
                                            type="text"
                                            placeholder="Search recipes..."
                                            value={tempSearchQuery}
                                            onChange={(e) => setTempSearchQuery(e.target.value)}
                                            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                                        />
                                    </div>
                                    <button
                                        type="submit"
                                        className="w-full btn-primary py-3"
                                        disabled={loading === 'loading'}
                                    >
                                        {loading === 'loading' ? 'Searching...' : 'Search'}
                                    </button>
                                </form>
                            </div>

                            {/* Search Algorithm */}
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Search Algorithm
                                </label>
                                <select
                                    value={searchMetric}
                                    onChange={(e) => setSearchMetric(e.target.value as 'tfidf' | 'bm25')}
                                    className="w-full input-field"
                                >
                                    <option value="bm25">BM25 (Recommended)</option>
                                    <option value="tfidf">TF-IDF</option>
                                </select>
                            </div>

                            {/* Filters */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
                                    {getActiveFilterCount() > 0 && (
                                        <button
                                            onClick={() => setFilters({})}
                                            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                                        >
                                            Clear all ({getActiveFilterCount()})
                                        </button>
                                    )}
                                </div>

                                {/* Cuisines - Most Used Filter */}
                                {cuisines.length > 0 && (
                                    <div className="border border-gray-200 rounded-lg bg-white">
                                        <button
                                            onClick={() => toggleSection('cuisines')}
                                            className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                        >
                                            <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                <MapPin className="w-4 h-4 mr-2 text-gray-600" />
                                                Cuisines ({cuisines.length} available)
                                            </h4>
                                            <ChevronDown
                                                className={cn(
                                                    "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                    !collapsedSections.cuisines && "rotate-180"
                                                )}
                                            />
                                        </button>
                                        {!collapsedSections.cuisines && (
                                            <div className="px-4 pb-4">
                                                <MultiSelect
                                                    options={cuisines}
                                                    selected={filters.cuisine || []}
                                                    onSelectionChange={(selected) => handleFiltersChange({
                                                        ...filters,
                                                        cuisine: selected.length > 0 ? selected : undefined
                                                    })}
                                                    placeholder="Select cuisines..."
                                                    searchable={true}
                                                    maxDisplay={2}
                                                />
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Time Filters - Second Most Used */}
                                <div className="border border-gray-200 rounded-lg bg-white">
                                    <button
                                        onClick={() => toggleSection('time')}
                                        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        <h4 className="flex items-center text-sm font-medium text-gray-900">
                                            <Clock className="w-4 h-4 mr-2 text-gray-600" />
                                            Time Filters
                                        </h4>
                                        <ChevronDown
                                            className={cn(
                                                "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                !collapsedSections.time && "rotate-180"
                                            )}
                                        />
                                    </button>
                                    {!collapsedSections.time && (
                                        <div className="px-4 pb-4 space-y-4">

                                            {/* Total Time */}
                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <Clock className="w-3 h-3 mr-1 text-gray-500" />
                                                    Total Time
                                                </label>
                                                <div className="grid grid-cols-2 gap-2">
                                                    <select
                                                        value={filters.min_total_minutes || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            min_total_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    >
                                                        <option value="">Min</option>
                                                        <option value="5">5 min</option>
                                                        <option value="15">15 min</option>
                                                        <option value="30">30 min</option>
                                                        <option value="60">1 hour</option>
                                                    </select>
                                                    <select
                                                        value={filters.max_total_minutes || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            max_total_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    >
                                                        <option value="">Max</option>
                                                        <option value="15">15 min</option>
                                                        <option value="30">30 min</option>
                                                        <option value="60">1 hour</option>
                                                        <option value="120">2 hours</option>
                                                        <option value="240">4 hours</option>
                                                    </select>
                                                </div>
                                            </div>

                                            {/* Prep Time */}
                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <Utensils className="w-3 h-3 mr-1 text-gray-500" />
                                                    Prep Time
                                                </label>
                                                <div className="grid grid-cols-2 gap-2">
                                                    <select
                                                        value={filters.min_prep_minutes || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            min_prep_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    >
                                                        <option value="">Min</option>
                                                        <option value="5">5 min</option>
                                                        <option value="10">10 min</option>
                                                        <option value="15">15 min</option>
                                                        <option value="30">30 min</option>
                                                    </select>
                                                    <select
                                                        value={filters.max_prep_minutes || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            max_prep_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    >
                                                        <option value="">Max</option>
                                                        <option value="10">10 min</option>
                                                        <option value="20">20 min</option>
                                                        <option value="30">30 min</option>
                                                        <option value="60">1 hour</option>
                                                    </select>
                                                </div>
                                            </div>

                                            {/* Cook Time */}
                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <Flame className="w-3 h-3 mr-1 text-gray-500" />
                                                    Cook Time
                                                </label>
                                                <div className="grid grid-cols-2 gap-2">
                                                    <select
                                                        value={filters.min_cook_minutes || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            min_cook_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    >
                                                        <option value="">Min</option>
                                                        <option value="5">5 min</option>
                                                        <option value="10">10 min</option>
                                                        <option value="20">20 min</option>
                                                        <option value="30">30 min</option>
                                                    </select>
                                                    <select
                                                        value={filters.max_cook_minutes || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            max_cook_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    >
                                                        <option value="">Max</option>
                                                        <option value="15">15 min</option>
                                                        <option value="30">30 min</option>
                                                        <option value="60">1 hour</option>
                                                        <option value="120">2 hours</option>
                                                        <option value="180">3 hours</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Servings */}
                                <div className="border border-gray-200 rounded-lg bg-white">
                                    <button
                                        onClick={() => toggleSection('servings')}
                                        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        <h4 className="flex items-center text-sm font-medium text-gray-900">
                                            <Users className="w-4 h-4 mr-2 text-gray-600" />
                                            Servings
                                        </h4>
                                        <ChevronDown
                                            className={cn(
                                                "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                !collapsedSections.servings && "rotate-180"
                                            )}
                                        />
                                    </button>
                                    {!collapsedSections.servings && (
                                        <div className="px-4 pb-4">
                                            <div className="grid grid-cols-2 gap-2">
                                                <select
                                                    value={filters.min_servings || ''}
                                                    onChange={(e) => handleFiltersChange({
                                                        ...filters,
                                                        min_servings: e.target.value ? parseInt(e.target.value) : undefined
                                                    })}
                                                    className="input-field text-sm"
                                                >
                                                    <option value="">Min</option>
                                                    <option value="1">1 serving</option>
                                                    <option value="2">2 servings</option>
                                                    <option value="4">4 servings</option>
                                                    <option value="6">6 servings</option>
                                                </select>
                                                <select
                                                    value={filters.max_servings || ''}
                                                    onChange={(e) => handleFiltersChange({
                                                        ...filters,
                                                        max_servings: e.target.value ? parseInt(e.target.value) : undefined
                                                    })}
                                                    className="input-field text-sm"
                                                >
                                                    <option value="">Max</option>
                                                    <option value="2">2 servings</option>
                                                    <option value="4">4 servings</option>
                                                    <option value="8">8 servings</option>
                                                    <option value="12">12 servings</option>
                                                </select>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Rating & Reviews */}
                                <div className="border border-gray-200 rounded-lg bg-white">
                                    <button
                                        onClick={() => toggleSection('rating')}
                                        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        <h4 className="flex items-center text-sm font-medium text-gray-900">
                                            <Star className="w-4 h-4 mr-2 text-gray-600" />
                                            Rating & Reviews
                                        </h4>
                                        <ChevronDown
                                            className={cn(
                                                "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                !collapsedSections.rating && "rotate-180"
                                            )}
                                        />
                                    </button>
                                    {!collapsedSections.rating && (
                                        <div className="px-4 pb-4 space-y-4">

                                            {/* Rating */}
                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <Star className="w-3 h-3 mr-1 text-yellow-500" />
                                                    Minimum Rating
                                                </label>
                                                <div className="space-y-2">
                                                    <input
                                                        type="range"
                                                        min="0"
                                                        max="5"
                                                        step="0.5"
                                                        value={filters.min_rating || 0}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            min_rating: parseFloat(e.target.value) || undefined
                                                        })}
                                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                                    />
                                                    <div className="text-sm text-gray-600 text-center">
                                                        {filters.min_rating ? `${filters.min_rating}+ ⭐` : 'Any rating'}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Review Count */}
                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <User className="w-3 h-3 mr-1 text-gray-500" />
                                                    Minimum Reviews
                                                </label>
                                                <select
                                                    value={filters.min_review_count || ''}
                                                    onChange={(e) => handleFiltersChange({
                                                        ...filters,
                                                        min_review_count: e.target.value ? parseInt(e.target.value) : undefined
                                                    })}
                                                    className="w-full input-field text-sm"
                                                >
                                                    <option value="">Any amount</option>
                                                    <option value="1">1+ reviews</option>
                                                    <option value="5">5+ reviews</option>
                                                    <option value="10">10+ reviews</option>
                                                    <option value="25">25+ reviews</option>
                                                    <option value="50">50+ reviews</option>
                                                </select>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Difficulty */}
                                <div className="border border-gray-200 rounded-lg bg-white">
                                    <button
                                        onClick={() => toggleSection('difficulty')}
                                        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        <h4 className="flex items-center text-sm font-medium text-gray-900">
                                            <ChefHat className="w-4 h-4 mr-2 text-gray-600" />
                                            Difficulty Level
                                        </h4>
                                        <ChevronDown
                                            className={cn(
                                                "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                !collapsedSections.difficulty && "rotate-180"
                                            )}
                                        />
                                    </button>
                                    {!collapsedSections.difficulty && (
                                        <div className="px-4 pb-4">
                                            <div className="space-y-2">
                                                {['easy', 'medium', 'hard'].map((level) => (
                                                    <label key={level} className="flex items-center">
                                                        <input
                                                            type="checkbox"
                                                            checked={filters.difficulty?.includes(level) || false}
                                                            onChange={(e) => {
                                                                const currentDifficulties = filters.difficulty || [];
                                                                const newDifficulties = e.target.checked
                                                                    ? [...currentDifficulties, level]
                                                                    : currentDifficulties.filter(d => d !== level);

                                                                handleFiltersChange({
                                                                    ...filters,
                                                                    difficulty: newDifficulties.length > 0 ? newDifficulties : undefined
                                                                });
                                                            }}
                                                            className="mr-2"
                                                        />
                                                        <span className="text-sm capitalize">{level}</span>
                                                    </label>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Nutrition Filters */}
                                <div className="border border-gray-200 rounded-lg bg-white">
                                    <button
                                        onClick={() => toggleSection('nutrition')}
                                        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        <h4 className="flex items-center text-sm font-medium text-gray-900">
                                            <Scale className="w-4 h-4 mr-2 text-gray-600" />
                                            Nutrition
                                        </h4>
                                        <ChevronDown
                                            className={cn(
                                                "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                !collapsedSections.nutrition && "rotate-180"
                                            )}
                                        />
                                    </button>
                                    {!collapsedSections.nutrition && (
                                        <div className="px-4 pb-4 space-y-4">

                                            {/* Calories */}
                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <Flame className="w-3 h-3 mr-1 text-orange-500" />
                                                    Calories
                                                </label>
                                                <div className="grid grid-cols-2 gap-2">
                                                    <input
                                                        type="number"
                                                        placeholder="Min"
                                                        value={filters.min_calories || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            min_calories: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    />
                                                    <input
                                                        type="number"
                                                        placeholder="Max"
                                                        value={filters.max_calories || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            max_calories: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    />
                                                </div>
                                            </div>

                                            {/* Protein */}
                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <Zap className="w-3 h-3 mr-1 text-blue-500" />
                                                    Protein (g)
                                                </label>
                                                <div className="grid grid-cols-2 gap-2">
                                                    <input
                                                        type="number"
                                                        placeholder="Min"
                                                        value={filters.min_protein || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            min_protein: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    />
                                                    <input
                                                        type="number"
                                                        placeholder="Max"
                                                        value={filters.max_protein || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            max_protein: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    />
                                                </div>
                                            </div>

                                            {/* Carbohydrates */}
                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <Wheat className="w-3 h-3 mr-1 text-amber-500" />
                                                    Carbs (g)
                                                </label>
                                                <div className="grid grid-cols-2 gap-2">
                                                    <input
                                                        type="number"
                                                        placeholder="Min"
                                                        value={filters.min_carbs || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            min_carbs: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    />
                                                    <input
                                                        type="number"
                                                        placeholder="Max"
                                                        value={filters.max_carbs || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            max_carbs: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    />
                                                </div>
                                            </div>

                                            {/* Fat */}
                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <Droplets className="w-3 h-3 mr-1 text-yellow-500" />
                                                    Fat (g)
                                                </label>
                                                <div className="grid grid-cols-2 gap-2">
                                                    <input
                                                        type="number"
                                                        placeholder="Min"
                                                        value={filters.min_fat || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            min_fat: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    />
                                                    <input
                                                        type="number"
                                                        placeholder="Max"
                                                        value={filters.max_fat || ''}
                                                        onChange={(e) => handleFiltersChange({
                                                            ...filters,
                                                            max_fat: e.target.value ? parseInt(e.target.value) : undefined
                                                        })}
                                                        className="input-field text-sm"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Author Filters */}
                                <div className="border border-gray-200 rounded-lg bg-white">
                                    <button
                                        onClick={() => toggleSection('author')}
                                        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        <h4 className="flex items-center text-sm font-medium text-gray-900">
                                            <User className="w-4 h-4 mr-2 text-gray-600" />
                                            Author
                                        </h4>
                                        <ChevronDown
                                            className={cn(
                                                "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                !collapsedSections.author && "rotate-180"
                                            )}
                                        />
                                    </button>
                                    {!collapsedSections.author && (
                                        <div className="px-4 pb-4 space-y-4">

                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <User className="w-3 h-3 mr-1 text-gray-500" />
                                                    Author Name
                                                </label>
                                                <input
                                                    type="text"
                                                    placeholder="Search by author..."
                                                    value={filters.author || ''}
                                                    onChange={(e) => handleFiltersChange({
                                                        ...filters,
                                                        author: e.target.value || undefined
                                                    })}
                                                    className="w-full input-field text-sm"
                                                />
                                            </div>

                                            <div>
                                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                    <MapPin className="w-3 h-3 mr-1 text-gray-500" />
                                                    Author Location
                                                </label>
                                                <input
                                                    type="text"
                                                    placeholder="e.g. New York, Italy..."
                                                    value={filters.author_location || ''}
                                                    onChange={(e) => handleFiltersChange({
                                                        ...filters,
                                                        author_location: e.target.value || undefined
                                                    })}
                                                    className="w-full input-field text-sm"
                                                />
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Date Filters */}
                                <div className="border border-gray-200 rounded-lg bg-white">
                                    <button
                                        onClick={() => toggleSection('date')}
                                        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        <h4 className="flex items-center text-sm font-medium text-gray-900">
                                            <Calendar className="w-4 h-4 mr-2 text-gray-600" />
                                            Published Date
                                        </h4>
                                        <ChevronDown
                                            className={cn(
                                                "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                !collapsedSections.date && "rotate-180"
                                            )}
                                        />
                                    </button>
                                    {!collapsedSections.date && (
                                        <div className="px-4 pb-4">
                                            <div className="grid grid-cols-2 gap-2">
                                                <input
                                                    type="date"
                                                    value={filters.date_from || ''}
                                                    onChange={(e) => handleFiltersChange({
                                                        ...filters,
                                                        date_from: e.target.value || undefined
                                                    })}
                                                    className="input-field text-sm"
                                                />
                                                <input
                                                    type="date"
                                                    value={filters.date_to || ''}
                                                    onChange={(e) => handleFiltersChange({
                                                        ...filters,
                                                        date_to: e.target.value || undefined
                                                    })}
                                                    className="input-field text-sm"
                                                />
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Image Filter */}
                                <div className="border border-gray-200 rounded-lg bg-white">
                                    <button
                                        onClick={() => toggleSection('image')}
                                        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        <h4 className="flex items-center text-sm font-medium text-gray-900">
                                            <Filter className="w-4 h-4 mr-2 text-gray-600" />
                                            Image Filter
                                        </h4>
                                        <ChevronDown
                                            className={cn(
                                                "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                !collapsedSections.image && "rotate-180"
                                            )}
                                        />
                                    </button>
                                    {!collapsedSections.image && (
                                        <div className="px-4 pb-4">
                                            <label className="flex items-center">
                                                <input
                                                    type="checkbox"
                                                    checked={filters.has_image || false}
                                                    onChange={(e) => handleFiltersChange({
                                                        ...filters,
                                                        has_image: e.target.checked || undefined
                                                    })}
                                                    className="mr-2"
                                                />
                                                <span className="text-sm font-medium text-gray-700">Only recipes with images</span>
                                            </label>
                                        </div>
                                    )}
                                </div>

                                {/* Cuisines */}
                                {cuisines.length > 0 && (
                                    <div className="border border-gray-200 rounded-lg bg-white">
                                        <button
                                            onClick={() => toggleSection('cuisines')}
                                            className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                        >
                                            <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                <MapPin className="w-4 h-4 mr-2 text-gray-600" />
                                                Cuisines ({cuisines.length} available)
                                            </h4>
                                            <ChevronDown
                                                className={cn(
                                                    "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                    !collapsedSections.cuisines && "rotate-180"
                                                )}
                                            />
                                        </button>
                                        {!collapsedSections.cuisines && (
                                            <div className="px-4 pb-4">
                                                <MultiSelect
                                                    options={cuisines}
                                                    selected={filters.cuisine || []}
                                                    onSelectionChange={(selected) => handleFiltersChange({
                                                        ...filters,
                                                        cuisine: selected.length > 0 ? selected : undefined
                                                    })}
                                                    placeholder="Select cuisines..."
                                                    searchable={true}
                                                    maxDisplay={2}
                                                />
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Categories */}
                                {categories.length > 0 && (
                                    <div className="border border-gray-200 rounded-lg bg-white">
                                        <button
                                            onClick={() => toggleSection('categories')}
                                            className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                        >
                                            <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                <ChefHat className="w-4 h-4 mr-2 text-gray-600" />
                                                Categories ({categories.length} available)
                                            </h4>
                                            <ChevronDown
                                                className={cn(
                                                    "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                    !collapsedSections.categories && "rotate-180"
                                                )}
                                            />
                                        </button>
                                        {!collapsedSections.categories && (
                                            <div className="px-4 pb-4">
                                                <MultiSelect
                                                    options={categories}
                                                    selected={filters.category || []}
                                                    onSelectionChange={(selected) => handleFiltersChange({
                                                        ...filters,
                                                        category: selected.length > 0 ? selected : undefined
                                                    })}
                                                    placeholder="Select categories..."
                                                    searchable={true}
                                                    maxDisplay={2}
                                                />
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Ingredients */}
                                {ingredients.length > 0 && (
                                    <div className="border border-gray-200 rounded-lg bg-white">
                                        <button
                                            onClick={() => toggleSection('ingredients')}
                                            className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                        >
                                            <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                <Utensils className="w-4 h-4 mr-2 text-green-500" />
                                                Must Include Ingredients ({ingredients.length} available)
                                            </h4>
                                            <ChevronDown
                                                className={cn(
                                                    "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                    !collapsedSections.ingredients && "rotate-180"
                                                )}
                                            />
                                        </button>
                                        {!collapsedSections.ingredients && (
                                            <div className="px-4 pb-4">
                                                <MultiSelect
                                                    options={ingredients.slice(0, 200)}
                                                    selected={filters.ingredients || []}
                                                    onSelectionChange={(selected) => handleFiltersChange({
                                                        ...filters,
                                                        ingredients: selected.length > 0 ? selected : undefined
                                                    })}
                                                    placeholder="Select required ingredients..."
                                                    searchable={true}
                                                    maxDisplay={3}
                                                />
                                                {ingredients.length > 200 && (
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        Showing top 200 most common ingredients
                                                    </p>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Keywords */}
                                <div className="border border-gray-200 rounded-lg bg-white">
                                    <button
                                        onClick={() => toggleSection('keywords')}
                                        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                    >
                                        <h4 className="flex items-center text-sm font-medium text-gray-900">
                                            <Search className="w-4 h-4 mr-2 text-gray-600" />
                                            Keywords
                                        </h4>
                                        <ChevronDown
                                            className={cn(
                                                "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                !collapsedSections.keywords && "rotate-180"
                                            )}
                                        />
                                    </button>
                                    {!collapsedSections.keywords && (
                                        <div className="px-4 pb-4">
                                            <input
                                                type="text"
                                                placeholder="e.g. healthy, quick, vegetarian..."
                                                value={filters.keywords?.join(', ') || ''}
                                                onChange={(e) => {
                                                    const keywords = e.target.value
                                                        .split(',')
                                                        .map(k => k.trim())
                                                        .filter(k => k.length > 0);

                                                    handleFiltersChange({
                                                        ...filters,
                                                        keywords: keywords.length > 0 ? keywords : undefined
                                                    });
                                                }}
                                                className="w-full input-field text-sm"
                                            />
                                            <p className="text-xs text-gray-500 mt-1">
                                                Separate multiple keywords with commas
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Main Content Area - Two Column Layout */}
                <div className="px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex gap-8">
                        {/* Left Column - Filters (Desktop) */}
                        <div className="hidden lg:block w-80 flex-shrink-0">
                            <div className="sticky top-8">
                                <div className="bg-white rounded-lg border border-gray-200 p-6">
                                    {/* Search Bar */}
                                    <div className="mb-6">
                                        <form onSubmit={handleSearch} className="space-y-4">
                                            <div className="relative">
                                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                                <input
                                                    type="text"
                                                    placeholder="Search recipes..."
                                                    value={tempSearchQuery}
                                                    onChange={(e) => setTempSearchQuery(e.target.value)}
                                                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                                                />
                                            </div>
                                            <button
                                                type="submit"
                                                className="w-full btn-primary py-3"
                                                disabled={loading === 'loading'}
                                            >
                                                {loading === 'loading' ? 'Searching...' : 'Search'}
                                            </button>
                                        </form>
                                    </div>

                                    {/* Search Algorithm */}
                                    <div className="mb-6">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Search Algorithm
                                        </label>
                                        <select
                                            value={searchMetric}
                                            onChange={(e) => setSearchMetric(e.target.value as 'tfidf' | 'bm25')}
                                            className="w-full input-field"
                                        >
                                            <option value="bm25">BM25 (Recommended)</option>
                                            <option value="tfidf">TF-IDF</option>
                                        </select>
                                    </div>

                                    {/* Filters - Reordered by Usage Frequency */}
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
                                            {getActiveFilterCount() > 0 && (
                                                <button
                                                    onClick={() => setFilters({})}
                                                    className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                                                >
                                                    Clear all ({getActiveFilterCount()})
                                                </button>
                                            )}
                                        </div>

                                        {/* 1. Cuisines - Most Used Filter (Open by Default) */}
                                        {cuisines.length > 0 && (
                                            <div className="border border-gray-200 rounded-lg bg-white">
                                                <button
                                                    onClick={() => toggleSection('cuisines')}
                                                    className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                                >
                                                    <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                        <MapPin className="w-4 h-4 mr-2 text-gray-600" />
                                                        Cuisines ({cuisines.length} available)
                                                    </h4>
                                                    <ChevronDown
                                                        className={cn(
                                                            "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                            !collapsedSections.cuisines && "rotate-180"
                                                        )}
                                                    />
                                                </button>
                                                {!collapsedSections.cuisines && (
                                                    <div className="px-4 pb-4">
                                                        <MultiSelect
                                                            options={cuisines}
                                                            selected={filters.cuisine || []}
                                                            onSelectionChange={(selected) => handleFiltersChange({
                                                                ...filters,
                                                                cuisine: selected.length > 0 ? selected : undefined
                                                            })}
                                                            placeholder="Select cuisines..."
                                                            searchable={true}
                                                            maxDisplay={2}
                                                        />
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {/* 2. Time Filters - Second Most Used */}
                                        <div className="border border-gray-200 rounded-lg bg-white">
                                            <button
                                                onClick={() => toggleSection('time')}
                                                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                            >
                                                <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                    <Clock className="w-4 h-4 mr-2 text-gray-600" />
                                                    Time Filters
                                                </h4>
                                                <ChevronDown
                                                    className={cn(
                                                        "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                        !collapsedSections.time && "rotate-180"
                                                    )}
                                                />
                                            </button>
                                            {!collapsedSections.time && (
                                                <div className="px-4 pb-4 space-y-4">

                                                    {/* Total Time */}
                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <Clock className="w-3 h-3 mr-1 text-gray-500" />
                                                            Total Time
                                                        </label>
                                                        <div className="grid grid-cols-2 gap-2">
                                                            <select
                                                                value={filters.min_total_minutes || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    min_total_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            >
                                                                <option value="">Min</option>
                                                                <option value="5">5 min</option>
                                                                <option value="15">15 min</option>
                                                                <option value="30">30 min</option>
                                                                <option value="60">1 hour</option>
                                                            </select>
                                                            <select
                                                                value={filters.max_total_minutes || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    max_total_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            >
                                                                <option value="">Max</option>
                                                                <option value="15">15 min</option>
                                                                <option value="30">30 min</option>
                                                                <option value="60">1 hour</option>
                                                                <option value="120">2 hours</option>
                                                                <option value="240">4 hours</option>
                                                            </select>
                                                        </div>
                                                    </div>

                                                    {/* Prep Time */}
                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <Utensils className="w-3 h-3 mr-1 text-gray-500" />
                                                            Prep Time
                                                        </label>
                                                        <div className="grid grid-cols-2 gap-2">
                                                            <select
                                                                value={filters.min_prep_minutes || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    min_prep_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            >
                                                                <option value="">Min</option>
                                                                <option value="5">5 min</option>
                                                                <option value="10">10 min</option>
                                                                <option value="15">15 min</option>
                                                                <option value="30">30 min</option>
                                                            </select>
                                                            <select
                                                                value={filters.max_prep_minutes || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    max_prep_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            >
                                                                <option value="">Max</option>
                                                                <option value="10">10 min</option>
                                                                <option value="20">20 min</option>
                                                                <option value="30">30 min</option>
                                                                <option value="60">1 hour</option>
                                                            </select>
                                                        </div>
                                                    </div>

                                                    {/* Cook Time */}
                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <Flame className="w-3 h-3 mr-1 text-gray-500" />
                                                            Cook Time
                                                        </label>
                                                        <div className="grid grid-cols-2 gap-2">
                                                            <select
                                                                value={filters.min_cook_minutes || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    min_cook_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            >
                                                                <option value="">Min</option>
                                                                <option value="5">5 min</option>
                                                                <option value="10">10 min</option>
                                                                <option value="20">20 min</option>
                                                                <option value="30">30 min</option>
                                                            </select>
                                                            <select
                                                                value={filters.max_cook_minutes || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    max_cook_minutes: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            >
                                                                <option value="">Max</option>
                                                                <option value="15">15 min</option>
                                                                <option value="30">30 min</option>
                                                                <option value="60">1 hour</option>
                                                                <option value="120">2 hours</option>
                                                                <option value="180">3 hours</option>
                                                            </select>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Servings */}
                                        <div className="border border-gray-200 rounded-lg bg-white">
                                            <button
                                                onClick={() => toggleSection('servings')}
                                                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                            >
                                                <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                    <Users className="w-4 h-4 mr-2 text-gray-600" />
                                                    Servings
                                                </h4>
                                                <ChevronDown
                                                    className={cn(
                                                        "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                        !collapsedSections.servings && "rotate-180"
                                                    )}
                                                />
                                            </button>
                                            {!collapsedSections.servings && (
                                                <div className="px-4 pb-4">
                                                    <div className="grid grid-cols-2 gap-2">
                                                        <select
                                                            value={filters.min_servings || ''}
                                                            onChange={(e) => handleFiltersChange({
                                                                ...filters,
                                                                min_servings: e.target.value ? parseInt(e.target.value) : undefined
                                                            })}
                                                            className="input-field text-sm"
                                                        >
                                                            <option value="">Min</option>
                                                            <option value="1">1 serving</option>
                                                            <option value="2">2 servings</option>
                                                            <option value="4">4 servings</option>
                                                            <option value="6">6 servings</option>
                                                        </select>
                                                        <select
                                                            value={filters.max_servings || ''}
                                                            onChange={(e) => handleFiltersChange({
                                                                ...filters,
                                                                max_servings: e.target.value ? parseInt(e.target.value) : undefined
                                                            })}
                                                            className="input-field text-sm"
                                                        >
                                                            <option value="">Max</option>
                                                            <option value="2">2 servings</option>
                                                            <option value="4">4 servings</option>
                                                            <option value="8">8 servings</option>
                                                            <option value="12">12 servings</option>
                                                        </select>
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Rating & Reviews */}
                                        <div className="border border-gray-200 rounded-lg bg-white">
                                            <button
                                                onClick={() => toggleSection('rating')}
                                                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                            >
                                                <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                    <Star className="w-4 h-4 mr-2 text-gray-600" />
                                                    Rating & Reviews
                                                </h4>
                                                <ChevronDown
                                                    className={cn(
                                                        "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                        !collapsedSections.rating && "rotate-180"
                                                    )}
                                                />
                                            </button>
                                            {!collapsedSections.rating && (
                                                <div className="px-4 pb-4 space-y-4">

                                                    {/* Rating */}
                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <Star className="w-3 h-3 mr-1 text-yellow-500" />
                                                            Minimum Rating
                                                        </label>
                                                        <div className="space-y-2">
                                                            <input
                                                                type="range"
                                                                min="0"
                                                                max="5"
                                                                step="0.5"
                                                                value={filters.min_rating || 0}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    min_rating: parseFloat(e.target.value) || undefined
                                                                })}
                                                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                                            />
                                                            <div className="text-sm text-gray-600 text-center">
                                                                {filters.min_rating ? `${filters.min_rating}+ ⭐` : 'Any rating'}
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Review Count */}
                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <User className="w-3 h-3 mr-1 text-gray-500" />
                                                            Minimum Reviews
                                                        </label>
                                                        <select
                                                            value={filters.min_review_count || ''}
                                                            onChange={(e) => handleFiltersChange({
                                                                ...filters,
                                                                min_review_count: e.target.value ? parseInt(e.target.value) : undefined
                                                            })}
                                                            className="w-full input-field text-sm"
                                                        >
                                                            <option value="">Any amount</option>
                                                            <option value="1">1+ reviews</option>
                                                            <option value="5">5+ reviews</option>
                                                            <option value="10">10+ reviews</option>
                                                            <option value="25">25+ reviews</option>
                                                            <option value="50">50+ reviews</option>
                                                        </select>
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Difficulty */}
                                        <div className="border border-gray-200 rounded-lg bg-white">
                                            <button
                                                onClick={() => toggleSection('difficulty')}
                                                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                            >
                                                <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                    <ChefHat className="w-4 h-4 mr-2 text-gray-600" />
                                                    Difficulty Level
                                                </h4>
                                                <ChevronDown
                                                    className={cn(
                                                        "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                        !collapsedSections.difficulty && "rotate-180"
                                                    )}
                                                />
                                            </button>
                                            {!collapsedSections.difficulty && (
                                                <div className="px-4 pb-4">
                                                    <div className="space-y-2">
                                                        {['easy', 'medium', 'hard'].map((level) => (
                                                            <label key={level} className="flex items-center">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={filters.difficulty?.includes(level) || false}
                                                                    onChange={(e) => {
                                                                        const currentDifficulties = filters.difficulty || [];
                                                                        const newDifficulties = e.target.checked
                                                                            ? [...currentDifficulties, level]
                                                                            : currentDifficulties.filter(d => d !== level);

                                                                        handleFiltersChange({
                                                                            ...filters,
                                                                            difficulty: newDifficulties.length > 0 ? newDifficulties : undefined
                                                                        });
                                                                    }}
                                                                    className="mr-2"
                                                                />
                                                                <span className="text-sm capitalize">{level}</span>
                                                            </label>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Nutrition Filters */}
                                        <div className="border border-gray-200 rounded-lg bg-white">
                                            <button
                                                onClick={() => toggleSection('nutrition')}
                                                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                            >
                                                <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                    <Scale className="w-4 h-4 mr-2 text-gray-600" />
                                                    Nutrition
                                                </h4>
                                                <ChevronDown
                                                    className={cn(
                                                        "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                        !collapsedSections.nutrition && "rotate-180"
                                                    )}
                                                />
                                            </button>
                                            {!collapsedSections.nutrition && (
                                                <div className="px-4 pb-4 space-y-4">

                                                    {/* Calories */}
                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <Flame className="w-3 h-3 mr-1 text-orange-500" />
                                                            Calories
                                                        </label>
                                                        <div className="grid grid-cols-2 gap-2">
                                                            <input
                                                                type="number"
                                                                placeholder="Min"
                                                                value={filters.min_calories || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    min_calories: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            />
                                                            <input
                                                                type="number"
                                                                placeholder="Max"
                                                                value={filters.max_calories || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    max_calories: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            />
                                                        </div>
                                                    </div>

                                                    {/* Protein */}
                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <Zap className="w-3 h-3 mr-1 text-blue-500" />
                                                            Protein (g)
                                                        </label>
                                                        <div className="grid grid-cols-2 gap-2">
                                                            <input
                                                                type="number"
                                                                placeholder="Min"
                                                                value={filters.min_protein || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    min_protein: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            />
                                                            <input
                                                                type="number"
                                                                placeholder="Max"
                                                                value={filters.max_protein || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    max_protein: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            />
                                                        </div>
                                                    </div>

                                                    {/* Carbohydrates */}
                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <Wheat className="w-3 h-3 mr-1 text-amber-500" />
                                                            Carbs (g)
                                                        </label>
                                                        <div className="grid grid-cols-2 gap-2">
                                                            <input
                                                                type="number"
                                                                placeholder="Min"
                                                                value={filters.min_carbs || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    min_carbs: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            />
                                                            <input
                                                                type="number"
                                                                placeholder="Max"
                                                                value={filters.max_carbs || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    max_carbs: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            />
                                                        </div>
                                                    </div>

                                                    {/* Fat */}
                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <Droplets className="w-3 h-3 mr-1 text-yellow-500" />
                                                            Fat (g)
                                                        </label>
                                                        <div className="grid grid-cols-2 gap-2">
                                                            <input
                                                                type="number"
                                                                placeholder="Min"
                                                                value={filters.min_fat || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    min_fat: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            />
                                                            <input
                                                                type="number"
                                                                placeholder="Max"
                                                                value={filters.max_fat || ''}
                                                                onChange={(e) => handleFiltersChange({
                                                                    ...filters,
                                                                    max_fat: e.target.value ? parseInt(e.target.value) : undefined
                                                                })}
                                                                className="input-field text-sm"
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Author Filters */}
                                        <div className="border border-gray-200 rounded-lg bg-white">
                                            <button
                                                onClick={() => toggleSection('author')}
                                                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                            >
                                                <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                    <User className="w-4 h-4 mr-2 text-gray-600" />
                                                    Author
                                                </h4>
                                                <ChevronDown
                                                    className={cn(
                                                        "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                        !collapsedSections.author && "rotate-180"
                                                    )}
                                                />
                                            </button>
                                            {!collapsedSections.author && (
                                                <div className="px-4 pb-4 space-y-4">

                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <User className="w-3 h-3 mr-1 text-gray-500" />
                                                            Author Name
                                                        </label>
                                                        <input
                                                            type="text"
                                                            placeholder="Search by author..."
                                                            value={filters.author || ''}
                                                            onChange={(e) => handleFiltersChange({
                                                                ...filters,
                                                                author: e.target.value || undefined
                                                            })}
                                                            className="w-full input-field text-sm"
                                                        />
                                                    </div>

                                                    <div>
                                                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                                            <MapPin className="w-3 h-3 mr-1 text-gray-500" />
                                                            Author Location
                                                        </label>
                                                        <input
                                                            type="text"
                                                            placeholder="e.g. New York, Italy..."
                                                            value={filters.author_location || ''}
                                                            onChange={(e) => handleFiltersChange({
                                                                ...filters,
                                                                author_location: e.target.value || undefined
                                                            })}
                                                            className="w-full input-field text-sm"
                                                        />
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Date Filters */}
                                        <div className="border border-gray-200 rounded-lg bg-white">
                                            <button
                                                onClick={() => toggleSection('date')}
                                                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                            >
                                                <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                    <Calendar className="w-4 h-4 mr-2 text-gray-600" />
                                                    Published Date
                                                </h4>
                                                <ChevronDown
                                                    className={cn(
                                                        "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                        !collapsedSections.date && "rotate-180"
                                                    )}
                                                />
                                            </button>
                                            {!collapsedSections.date && (
                                                <div className="px-4 pb-4">
                                                    <div className="grid grid-cols-2 gap-2">
                                                        <input
                                                            type="date"
                                                            value={filters.date_from || ''}
                                                            onChange={(e) => handleFiltersChange({
                                                                ...filters,
                                                                date_from: e.target.value || undefined
                                                            })}
                                                            className="input-field text-sm"
                                                        />
                                                        <input
                                                            type="date"
                                                            value={filters.date_to || ''}
                                                            onChange={(e) => handleFiltersChange({
                                                                ...filters,
                                                                date_to: e.target.value || undefined
                                                            })}
                                                            className="input-field text-sm"
                                                        />
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Image Filter */}
                                        <div className="border border-gray-200 rounded-lg bg-white">
                                            <button
                                                onClick={() => toggleSection('image')}
                                                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                            >
                                                <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                    <Filter className="w-4 h-4 mr-2 text-gray-600" />
                                                    Image Filter
                                                </h4>
                                                <ChevronDown
                                                    className={cn(
                                                        "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                        !collapsedSections.image && "rotate-180"
                                                    )}
                                                />
                                            </button>
                                            {!collapsedSections.image && (
                                                <div className="px-4 pb-4">
                                                    <label className="flex items-center">
                                                        <input
                                                            type="checkbox"
                                                            checked={filters.has_image || false}
                                                            onChange={(e) => handleFiltersChange({
                                                                ...filters,
                                                                has_image: e.target.checked || undefined
                                                            })}
                                                            className="mr-2"
                                                        />
                                                        <span className="text-sm font-medium text-gray-700">Only recipes with images</span>
                                                    </label>
                                                </div>
                                            )}
                                        </div>

                                        {/* Cuisines */}
                                        {cuisines.length > 0 && (
                                            <div className="border border-gray-200 rounded-lg bg-white">
                                                <button
                                                    onClick={() => toggleSection('cuisines')}
                                                    className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                                >
                                                    <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                        <MapPin className="w-4 h-4 mr-2 text-gray-600" />
                                                        Cuisines ({cuisines.length} available)
                                                    </h4>
                                                    <ChevronDown
                                                        className={cn(
                                                            "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                            !collapsedSections.cuisines && "rotate-180"
                                                        )}
                                                    />
                                                </button>
                                                {!collapsedSections.cuisines && (
                                                    <div className="px-4 pb-4">
                                                        <MultiSelect
                                                            options={cuisines}
                                                            selected={filters.cuisine || []}
                                                            onSelectionChange={(selected) => handleFiltersChange({
                                                                ...filters,
                                                                cuisine: selected.length > 0 ? selected : undefined
                                                            })}
                                                            placeholder="Select cuisines..."
                                                            searchable={true}
                                                            maxDisplay={2}
                                                        />
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {/* Categories */}
                                        {categories.length > 0 && (
                                            <div className="border border-gray-200 rounded-lg bg-white">
                                                <button
                                                    onClick={() => toggleSection('categories')}
                                                    className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                                >
                                                    <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                        <ChefHat className="w-4 h-4 mr-2 text-gray-600" />
                                                        Categories ({categories.length} available)
                                                    </h4>
                                                    <ChevronDown
                                                        className={cn(
                                                            "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                            !collapsedSections.categories && "rotate-180"
                                                        )}
                                                    />
                                                </button>
                                                {!collapsedSections.categories && (
                                                    <div className="px-4 pb-4">
                                                        <MultiSelect
                                                            options={categories}
                                                            selected={filters.category || []}
                                                            onSelectionChange={(selected) => handleFiltersChange({
                                                                ...filters,
                                                                category: selected.length > 0 ? selected : undefined
                                                            })}
                                                            placeholder="Select categories..."
                                                            searchable={true}
                                                            maxDisplay={2}
                                                        />
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {/* Ingredients */}
                                        {ingredients.length > 0 && (
                                            <div className="border border-gray-200 rounded-lg bg-white">
                                                <button
                                                    onClick={() => toggleSection('ingredients')}
                                                    className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                                >
                                                    <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                        <Utensils className="w-4 h-4 mr-2 text-green-500" />
                                                        Must Include Ingredients ({ingredients.length} available)
                                                    </h4>
                                                    <ChevronDown
                                                        className={cn(
                                                            "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                            !collapsedSections.ingredients && "rotate-180"
                                                        )}
                                                    />
                                                </button>
                                                {!collapsedSections.ingredients && (
                                                    <div className="px-4 pb-4">
                                                        <MultiSelect
                                                            options={ingredients.slice(0, 200)}
                                                            selected={filters.ingredients || []}
                                                            onSelectionChange={(selected) => handleFiltersChange({
                                                                ...filters,
                                                                ingredients: selected.length > 0 ? selected : undefined
                                                            })}
                                                            placeholder="Select required ingredients..."
                                                            searchable={true}
                                                            maxDisplay={3}
                                                        />
                                                        {ingredients.length > 200 && (
                                                            <p className="text-xs text-gray-500 mt-1">
                                                                Showing top 200 most common ingredients
                                                            </p>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {/* Keywords */}
                                        <div className="border border-gray-200 rounded-lg bg-white">
                                            <button
                                                onClick={() => toggleSection('keywords')}
                                                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors duration-200"
                                            >
                                                <h4 className="flex items-center text-sm font-medium text-gray-900">
                                                    <Search className="w-4 h-4 mr-2 text-gray-600" />
                                                    Keywords
                                                </h4>
                                                <ChevronDown
                                                    className={cn(
                                                        "w-4 h-4 text-gray-500 transition-transform duration-200",
                                                        !collapsedSections.keywords && "rotate-180"
                                                    )}
                                                />
                                            </button>
                                            {!collapsedSections.keywords && (
                                                <div className="px-4 pb-4">
                                                    <input
                                                        type="text"
                                                        placeholder="e.g. healthy, quick, vegetarian..."
                                                        value={filters.keywords?.join(', ') || ''}
                                                        onChange={(e) => {
                                                            const keywords = e.target.value
                                                                .split(',')
                                                                .map(k => k.trim())
                                                                .filter(k => k.length > 0);

                                                            handleFiltersChange({
                                                                ...filters,
                                                                keywords: keywords.length > 0 ? keywords : undefined
                                                            });
                                                        }}
                                                        className="w-full input-field text-sm"
                                                    />
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        Separate multiple keywords with commas
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>                           
                        </div>
                        {/* Right Column - Recipe Results */}
                            <div className="flex-1 min-w-0">
                                {/* Results Header */}
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center space-x-4">
                                        <h2 className="text-xl font-semibold text-gray-900">
                                            {searchQuery ? `Results for "${searchQuery}"` : 'All Recipes'}
                                        </h2>
                                        {loading === 'idle' && (
                                            <SearchStats
                                                totalResults={totalResults}
                                                searchTime={searchTime || undefined}
                                                currentPage={currentPage}
                                                itemsPerPage={itemsPerPage}
                                                searchQuery={searchQuery}
                                                metric={searchMetric}
                                                activeFilters={getActiveFilterCount()}
                                            />
                                        )}
                                    </div>

                                    <div className="flex items-center space-x-4">
                                        {/* Sort */}
                                        <div className="flex items-center space-x-2">
                                            <ArrowUpDown className="w-4 h-4 text-gray-500" />
                                            <select
                                                value={sortBy}
                                                onChange={(e) => handleSortChange(e.target.value)}
                                                className="text-sm border border-gray-200 rounded px-2 py-1"
                                            >
                                                {sortOptions.map(option => (
                                                    <option key={option.value} value={option.value}>
                                                        {option.label}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>

                                        {/* View Mode */}
                                        <div className="flex items-center border border-gray-200 rounded-lg">
                                            <button
                                                onClick={() => setViewMode('grid')}
                                                className={cn(
                                                    'p-2 rounded-l-lg transition-colors',
                                                    viewMode === 'grid' ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:bg-gray-100'
                                                )}
                                            >
                                                <Grid3X3 className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => setViewMode('list')}
                                                className={cn(
                                                    'p-2 rounded-r-lg transition-colors',
                                                    viewMode === 'list' ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:bg-gray-100'
                                                )}
                                            >
                                                <List className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                {/* Error State */}
                                {loading === 'error' && (
                                    <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
                                        <div className="flex items-center">
                                            <AlertCircle className="w-6 h-6 text-red-600 mr-3" />
                                            <div>
                                                <h3 className="text-lg font-medium text-red-900">Search Error</h3>
                                                <p className="text-red-700 mt-1">{error}</p>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Loading State */}
                                {loading === 'loading' && (
                                    <div className={cn(
                                        viewMode === 'grid'
                                            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-fr'
                                            : 'space-y-4'
                                    )}>
                                        {Array.from({ length: itemsPerPage }).map((_, index) => (
                                            <RecipeCardSkeleton key={index} />
                                        ))}
                                    </div>
                                )}

                                {/* Empty State */}
                                {loading === 'idle' && recipes.length === 0 && !error && (
                                    <div className="text-center py-16">
                                        <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                                            <ChefHat className="w-12 h-12 text-gray-400" />
                                        </div>
                                        <h3 className="text-xl font-medium text-gray-900 mb-2">No recipes found</h3>
                                        <p className="text-gray-600 mb-6">
                                            {searchQuery || getActiveFilterCount() > 0
                                                ? "Try adjusting your search terms or filters"
                                                : "No recipes available at the moment"
                                            }
                                        </p>
                                        {(searchQuery || getActiveFilterCount() > 0) && (
                                            <button
                                                onClick={() => {
                                                    setSearchQuery('');
                                                    setTempSearchQuery('');
                                                    setFilters({});
                                                    setCurrentPage(1);
                                                }}
                                                className="btn-primary"
                                            >
                                                Clear search and filters
                                            </button>
                                        )}
                                    </div>
                                )}

                                {/* Results Grid/List */}
                                {loading === 'idle' && recipes.length > 0 && (
                                    <>
                                        <div className={cn(
                                            viewMode === 'grid'
                                                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-fr'
                                                : 'space-y-4'
                                        )}>
                                            {recipes.map((recipe) => (
                                                viewMode === 'grid' ? (
                                                    <RecipeCard
                                                        key={recipe.id}
                                                        recipe={recipe}
                                                        showScore={!!searchQuery}
                                                    />
                                                ) : (
                                                    <RecipeListItem
                                                        key={recipe.id}
                                                        recipe={recipe}
                                                        showScore={!!searchQuery}
                                                    />
                                                )
                                            ))}
                                        </div>

                                        {/* Pagination */}
                                        {totalPages > 1 && (
                                            <div className="flex flex-col items-center space-y-4 mt-12">
                                                {/* Page Navigation */}
                                                <div className="flex items-center justify-center space-x-2">
                                                    <button
                                                        onClick={() => handlePageChange(currentPage - 1)}
                                                        disabled={currentPage === 1}
                                                        className="flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                                    >
                                                        <ChevronLeft className="w-4 h-4 mr-1" />
                                                        Previous
                                                    </button>

                                                    {/* Page numbers */}
                                                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                                        const page = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                                                        if (page > totalPages) return null;

                                                        return (
                                                            <button
                                                                key={page}
                                                                onClick={() => handlePageChange(page)}
                                                                className={cn(
                                                                    'px-3 py-2 border text-sm font-medium rounded-md',
                                                                    page === currentPage
                                                                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                                                                        : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                                                                )}
                                                            >
                                                                {page}
                                                            </button>
                                                        );
                                                    })}

                                                    <button
                                                        onClick={() => handlePageChange(currentPage + 1)}
                                                        disabled={currentPage === totalPages}
                                                        className="flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                                    >
                                                        Next
                                                        <ChevronRight className="w-4 h-4 ml-1" />
                                                    </button>
                                                </div>

                                                {/* Page Input */}
                                                <div className="flex items-center space-x-2">
                                                    <span className="text-sm text-gray-600">Go to page:</span>
                                                    <form onSubmit={handlePageInputSubmit} className="flex items-center space-x-2">
                                                        <input
                                                            type="text"
                                                            value={pageInput}
                                                            onChange={handlePageInputChange}
                                                            placeholder="Page number"
                                                            className="w-20 px-3 py-2 border border-gray-300 rounded-md text-sm text-center focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                                                            maxLength={4}
                                                        />
                                                        <button
                                                            type="submit"
                                                            disabled={!pageInput || parseInt(pageInput) < 1 || parseInt(pageInput) > totalPages}
                                                            className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                                        >
                                                            Go
                                                        </button>
                                                    </form>
                                                    <span className="text-sm text-gray-500">
                                                        of {totalPages}
                                                    </span>
                                                </div>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function RecipesListPage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading recipes...</p>
            </div>
        </div>}>
            <RecipesListPageContent />
        </Suspense>
    );
}

