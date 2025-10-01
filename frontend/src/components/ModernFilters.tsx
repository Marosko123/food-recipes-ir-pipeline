'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { SearchFilters } from '@/types/recipe';
import {
    ChevronDown, ChevronRight, Clock, Globe, Utensils,
    Heart, ChefHat, Zap, Users, Star, Filter, X
} from 'lucide-react';

interface ModernFiltersProps {
    filters: SearchFilters;
    onFiltersChange: (filters: SearchFilters) => void;
}

interface CategoryData {
    cuisines: Record<string, number>;
    meal_types: Record<string, number>;
    dietary: Record<string, number>;
    cooking_methods: Record<string, number>;
    ingredients: Record<string, number>;
}

interface FilterSection {
    id: string;
    title: string;
    icon: React.ReactNode;
    count: number;
    expanded: boolean;
    priority: number;
}

export default function ModernFilters({ filters, onFiltersChange }: ModernFiltersProps) {
    const [categories, setCategories] = useState<CategoryData | null>(null);
    const [loading, setLoading] = useState(true);
    const [sections, setSections] = useState<FilterSection[]>([]);

    useEffect(() => {
        const loadCategories = async () => {
            try {
                const data = await apiClient.getCategories();
                setCategories(data);

                // Create sections ordered by priority (most used first)
                const newSections: FilterSection[] = [
                    {
                        id: 'dietary',
                        title: 'Dietary & Lifestyle',
                        icon: <Heart className="w-4 h-4" />,
                        count: Object.keys(data.dietary).length,
                        expanded: false,
                        priority: 1
                    },
                    {
                        id: 'cuisines',
                        title: 'Cuisines',
                        icon: <Globe className="w-4 h-4" />,
                        count: Object.keys(data.cuisines).length,
                        expanded: false,
                        priority: 2
                    },
                    {
                        id: 'meal_types',
                        title: 'Meal Types',
                        icon: <Utensils className="w-4 h-4" />,
                        count: Object.keys(data.meal_types).length,
                        expanded: false,
                        priority: 3
                    },
                    {
                        id: 'time',
                        title: 'Time & Difficulty',
                        icon: <Clock className="w-4 h-4" />,
                        count: 0,
                        expanded: false,
                        priority: 4
                    },
                    {
                        id: 'cooking_methods',
                        title: 'Cooking Methods',
                        icon: <ChefHat className="w-4 h-4" />,
                        count: Object.keys(data.cooking_methods).length,
                        expanded: false,
                        priority: 5
                    },
                    {
                        id: 'rating',
                        title: 'Rating & Reviews',
                        icon: <Star className="w-4 h-4" />,
                        count: 0,
                        expanded: false,
                        priority: 6
                    },
                    {
                        id: 'ingredients',
                        title: 'Popular Ingredients',
                        icon: <Zap className="w-4 h-4" />,
                        count: Object.keys(data.ingredients).length,
                        expanded: false,
                        priority: 7
                    }
                ];

                setSections(newSections);
            } catch (error) {
                console.error('Failed to load categories:', error);
            } finally {
                setLoading(false);
            }
        };

        loadCategories();
    }, []);

    const toggleSection = (sectionId: string) => {
        setSections(prev => prev.map(section =>
            section.id === sectionId
                ? { ...section, expanded: !section.expanded }
                : section
        ));
    };

    const handleFilterChange = (filterType: keyof SearchFilters, value: string, checked: boolean) => {
        const currentValues = filters[filterType] as string[] || [];

        if (checked) {
            onFiltersChange({
                ...filters,
                [filterType]: [...currentValues, value]
            });
        } else {
            onFiltersChange({
                ...filters,
                [filterType]: currentValues.filter(v => v !== value)
            });
        }
    };

    const clearAllFilters = () => {
        onFiltersChange({});
    };

    const getActiveFilterCount = () => {
        return Object.keys(filters).filter(key => {
            const value = filters[key as keyof SearchFilters];
            return value !== undefined && value !== null &&
                (Array.isArray(value) ? value.length > 0 : true);
        }).length;
    };

    const renderFilterSection = (section: FilterSection) => {
        if (!categories) return null;

        const isExpanded = section.expanded;
        const activeCount = getActiveFilterCount();

        return (
            <div key={section.id} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                    onClick={() => toggleSection(section.id)}
                    className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors duration-200 flex items-center justify-between"
                >
                    <div className="flex items-center space-x-3">
                        <div className="text-gray-600">
                            {section.icon}
                        </div>
                        <div className="text-left">
                            <h3 className="font-medium text-gray-900">{section.title}</h3>
                            <p className="text-sm text-gray-500">
                                {section.count > 0 ? `${section.count} options` : 'Custom filters'}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-2">
                        {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-gray-500" />
                        ) : (
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                        )}
                    </div>
                </button>

                {isExpanded && (
                    <div className="p-4 bg-white border-t border-gray-200">
                        {renderFilterContent(section.id)}
                    </div>
                )}
            </div>
        );
    };

    const renderFilterContent = (sectionId: string) => {
        if (!categories) return null;

        switch (sectionId) {
            case 'dietary':
                return renderCategoryFilters('dietary', categories.dietary, 'dietary');

            case 'cuisines':
                return renderCategoryFilters('cuisines', categories.cuisines, 'cuisine');

            case 'meal_types':
                return renderCategoryFilters('meal_types', categories.meal_types, 'meal_type');

            case 'cooking_methods':
                return renderCategoryFilters('cooking_methods', categories.cooking_methods, 'cooking_method');

            case 'ingredients':
                return renderCategoryFilters('ingredients', categories.ingredients, 'ingredients');

            case 'time':
                return renderTimeFilters();

            case 'rating':
                return renderRatingFilters();

            default:
                return null;
        }
    };

    const renderCategoryFilters = (title: string, items: Record<string, number>, filterKey: keyof SearchFilters) => {
        const sortedItems = Object.entries(items)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 15); // Show top 15 items

        return (
            <div className="space-y-3">
                <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto">
                    {sortedItems.map(([item, count]) => {
                        const isSelected = (filters[filterKey] as string[] || []).includes(item);
                        return (
                            <label
                                key={item}
                                className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                            >
                                <input
                                    type="checkbox"
                                    checked={isSelected}
                                    onChange={(e) => handleFilterChange(filterKey, item, e.target.checked)}
                                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                                />
                                <div className="flex-1 min-w-0">
                                    <span className="text-sm font-medium text-gray-900 capitalize">
                                        {item.replace(/-/g, ' ')}
                                    </span>
                                </div>
                                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                                    {count}
                                </span>
                            </label>
                        );
                    })}
                </div>
            </div>
        );
    };

    const renderTimeFilters = () => {
        return (
            <div className="space-y-4">
                {/* Total Time */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Total Time
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                        <select
                            value={filters.min_total_minutes || ''}
                            onChange={(e) => onFiltersChange({
                                ...filters,
                                min_total_minutes: e.target.value ? parseInt(e.target.value) : undefined
                            })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        >
                            <option value="">Min</option>
                            <option value="5">5 min</option>
                            <option value="15">15 min</option>
                            <option value="30">30 min</option>
                            <option value="60">1 hour</option>
                            <option value="120">2 hours</option>
                        </select>
                        <select
                            value={filters.max_total_minutes || ''}
                            onChange={(e) => onFiltersChange({
                                ...filters,
                                max_total_minutes: e.target.value ? parseInt(e.target.value) : undefined
                            })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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

                {/* Difficulty */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Difficulty
                    </label>
                    <div className="space-y-2">
                        {['easy', 'medium', 'hard'].map(difficulty => (
                            <label key={difficulty} className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    checked={(filters.difficulty || []).includes(difficulty)}
                                    onChange={(e) => handleFilterChange('difficulty', difficulty, e.target.checked)}
                                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                                />
                                <span className="text-sm text-gray-900 capitalize">{difficulty}</span>
                            </label>
                        ))}
                    </div>
                </div>
            </div>
        );
    };

    const renderRatingFilters = () => {
        return (
            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Minimum Rating
                    </label>
                    <select
                        value={filters.min_rating || ''}
                        onChange={(e) => onFiltersChange({
                            ...filters,
                            min_rating: e.target.value ? parseFloat(e.target.value) : undefined
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                        <option value="">Any rating</option>
                        <option value="3">3+ stars</option>
                        <option value="4">4+ stars</option>
                        <option value="4.5">4.5+ stars</option>
                        <option value="5">5 stars only</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Minimum Reviews
                    </label>
                    <select
                        value={filters.min_review_count || ''}
                        onChange={(e) => onFiltersChange({
                            ...filters,
                            min_review_count: e.target.value ? parseInt(e.target.value) : undefined
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                        <option value="">Any reviews</option>
                        <option value="5">5+ reviews</option>
                        <option value="10">10+ reviews</option>
                        <option value="25">25+ reviews</option>
                        <option value="50">50+ reviews</option>
                    </select>
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="space-y-4">
                {[1, 2, 3, 4].map(i => (
                    <div key={i} className="animate-pulse">
                        <div className="h-16 bg-gray-200 rounded-lg"></div>
                    </div>
                ))}
            </div>
        );
    }

    const activeCount = getActiveFilterCount();

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <Filter className="w-5 h-5 text-gray-600" />
                    <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
                    {activeCount > 0 && (
                        <span className="bg-primary-100 text-primary-800 text-xs font-medium px-2 py-1 rounded-full">
                            {activeCount}
                        </span>
                    )}
                </div>
                {activeCount > 0 && (
                    <button
                        onClick={clearAllFilters}
                        className="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1"
                    >
                        <X className="w-4 h-4" />
                        <span>Clear all</span>
                    </button>
                )}
            </div>

            {/* Filter Sections */}
            <div className="space-y-3">
                {sections.map(renderFilterSection)}
            </div>
        </div>
    );
}
