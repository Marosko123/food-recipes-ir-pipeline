'use client';

import { useState } from 'react';
import { Search, Filter } from 'lucide-react';
import { SearchFilters } from '@/types/recipe';

interface SearchBarProps {
    onSearch: (query: string, filters: SearchFilters) => void;
    loading?: boolean;
    initialQuery?: string;
    cuisines?: string[];
}

export default function SearchBar({ onSearch, loading = false, initialQuery = '', cuisines = [] }: SearchBarProps) {
    const [query, setQuery] = useState(initialQuery);
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState<SearchFilters>({});

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch(query, filters);
    };

    const handleFilterChange = (key: keyof SearchFilters, value: any) => {
        const newFilters = { ...filters, [key]: value };
        setFilters(newFilters);
    };

    const clearFilters = () => {
        setFilters({});
    };

    const hasActiveFilters = Object.keys(filters).some(key => {
        const value = filters[key as keyof SearchFilters];
        return value !== undefined && value !== null &&
            (Array.isArray(value) ? value.length > 0 : true);
    });

    return (
        <div className="w-full max-w-4xl mx-auto">
            {/* Search Form */}
            <form onSubmit={handleSubmit} className="relative">
                <div className="relative">
                    <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                        type="text"
                        placeholder="Search for recipes, ingredients, or cuisines..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="w-full pl-12 pr-24 py-4 text-lg border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all duration-200 bg-white shadow-sm"
                        disabled={loading}
                    />
                    <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
                        <button
                            type="button"
                            onClick={() => setShowFilters(!showFilters)}
                            className={`p-2 rounded-lg transition-colors duration-200 ${hasActiveFilters || showFilters
                                    ? 'bg-primary-100 text-primary-600'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            <Filter className="w-5 h-5" />
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-primary px-6 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Searching...' : 'Search'}
                        </button>
                    </div>
                </div>
            </form>

            {/* Filters Panel */}
            {showFilters && (
                <div className="mt-4 p-6 bg-white rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
                        {hasActiveFilters && (
                            <button
                                onClick={clearFilters}
                                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                            >
                                Clear all
                            </button>
                        )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {/* Max Cooking Time */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Max Cooking Time
                            </label>
                            <select
                                value={filters.max_total_minutes || ''}
                                onChange={(e) => handleFilterChange('max_total_minutes', e.target.value ? parseInt(e.target.value) : undefined)}
                                className="w-full input-field"
                            >
                                <option value="">Any time</option>
                                <option value="15">15 minutes</option>
                                <option value="30">30 minutes</option>
                                <option value="60">1 hour</option>
                                <option value="120">2 hours</option>
                            </select>
                        </div>

                        {/* Difficulty */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Difficulty
                            </label>
                            <select
                                value={filters.difficulty || ''}
                                onChange={(e) => handleFilterChange('difficulty', e.target.value || undefined)}
                                className="w-full input-field"
                            >
                                <option value="">Any difficulty</option>
                                <option value="easy">Easy</option>
                                <option value="medium">Medium</option>
                                <option value="hard">Hard</option>
                            </select>
                        </div>

                        {/* Cuisine */}
                        {cuisines.length > 0 && (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Cuisine
                                </label>
                                <select
                                    value={filters.cuisine?.[0] || ''}
                                    onChange={(e) => handleFilterChange('cuisine', e.target.value ? [e.target.value] : undefined)}
                                    className="w-full input-field"
                                >
                                    <option value="">Any cuisine</option>
                                    {cuisines.slice(0, 20).map((cuisine) => (
                                        <option key={cuisine} value={cuisine}>
                                            {cuisine.charAt(0).toUpperCase() + cuisine.slice(1)}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {/* Min Rating */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Min Rating
                            </label>
                            <select
                                value={filters.min_rating || ''}
                                onChange={(e) => handleFilterChange('min_rating', e.target.value ? parseFloat(e.target.value) : undefined)}
                                className="w-full input-field"
                            >
                                <option value="">Any rating</option>
                                <option value="3">3+ stars</option>
                                <option value="4">4+ stars</option>
                                <option value="4.5">4.5+ stars</option>
                            </select>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

