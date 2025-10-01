'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
    ChevronDown,
    Clock,
    Star,
    Heart,
    Zap,
    Utensils,
    Flame,
    Dumbbell,
    Apple,
    Carrot,
    Fish,
    Beef,
    Wheat,
    Leaf,
    Cake,
    Coffee,
    Pizza,
    Salad
} from 'lucide-react';

interface DropdownItem {
    label: string;
    href?: string;
    filters?: Record<string, any>;
    icon?: React.ReactNode;
}

interface DropdownMenu {
    label: string;
    items: DropdownItem[];
}

const navigationMenus: DropdownMenu[] = [
    {
        label: 'GYM',
        items: [
            { label: 'Bulk', filters: { keywords: ['bulk', 'mass', 'gaining', 'calories'] }, icon: <Dumbbell className="w-4 h-4" /> },
            { label: 'Cut', filters: { keywords: ['cut', 'lean', 'fat loss', 'low calorie'] }, icon: <Zap className="w-4 h-4" /> },
            { label: 'High Protein', filters: { keywords: ['protein', 'high protein', 'muscle'] }, icon: <Zap className="w-4 h-4" /> },
            { label: 'High Fat', filters: { keywords: ['high fat', 'keto', 'fatty'] }, icon: <Flame className="w-4 h-4" /> },
            { label: 'Low Fat', filters: { keywords: ['low fat', 'lean', 'healthy'] }, icon: <Leaf className="w-4 h-4" /> },
            { label: 'Pre-Workout', filters: { keywords: ['pre workout', 'energy', 'carbs'] }, icon: <Clock className="w-4 h-4" /> },
            { label: 'Post-Workout', filters: { keywords: ['post workout', 'recovery', 'protein'] }, icon: <Heart className="w-4 h-4" /> }
        ]
    },
    {
        label: 'RECIPES',
        items: [
            { label: 'All Recipes', href: '/recipes', icon: <Utensils className="w-4 h-4" /> },
            { label: 'Quick & Easy', filters: { max_total_minutes: 15 }, icon: <Clock className="w-4 h-4" /> },
            { label: '30-Minute Meals', filters: { max_total_minutes: 30 }, icon: <Clock className="w-4 h-4" /> },
            { label: 'One-Pot Meals', filters: { category: ['one-pot'] }, icon: <Flame className="w-4 h-4" /> },
            { label: 'Slow Cooker', filters: { category: ['slow-cooker'] }, icon: <Flame className="w-4 h-4" /> }
        ]
    },
    {
        label: 'CUISINE',
        items: [
            { label: 'Italian', filters: { cuisine: ['italian'] }, icon: <Pizza className="w-4 h-4" /> },
            { label: 'Asian', filters: { cuisine: ['asian', 'chinese', 'japanese', 'thai'] }, icon: <Utensils className="w-4 h-4" /> },
            { label: 'Mexican', filters: { cuisine: ['mexican'] }, icon: <Flame className="w-4 h-4" /> },
            { label: 'Indian', filters: { cuisine: ['indian'] }, icon: <Flame className="w-4 h-4" /> },
            { label: 'Mediterranean', filters: { cuisine: ['mediterranean'] }, icon: <Fish className="w-4 h-4" /> },
            { label: 'American', filters: { cuisine: ['american'] }, icon: <Utensils className="w-4 h-4" /> }
        ]
    },
    {
        label: 'MEAT & SEAFOOD',
        items: [
            { label: 'Chicken', filters: { ingredients: ['chicken breasts', 'chicken'] }, icon: <Utensils className="w-4 h-4" /> },
            { label: 'Beef & Steak', filters: { ingredients: ['beef', 'steak'] }, icon: <Beef className="w-4 h-4" /> },
            { label: 'Fish & Seafood', filters: { ingredients: ['fish', 'seafood', 'salmon'] }, icon: <Fish className="w-4 h-4" /> },
            { label: 'Pork', filters: { ingredients: ['pork', 'bacon'] }, icon: <Beef className="w-4 h-4" /> }
        ]
    },
    {
        label: 'MEAL TYPE',
        items: [
            { label: 'Breakfast', filters: { meal_type: ['breakfast'] }, icon: <Coffee className="w-4 h-4" /> },
            { label: 'Desserts', filters: { meal_type: ['desserts'] }, icon: <Cake className="w-4 h-4" /> },
            { label: 'Snacks', filters: { keywords: ['snack', 'quick'] }, icon: <Apple className="w-4 h-4" /> }
        ]
    }
];

export default function Navigation() {
    const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
    const [hoverTimeout, setHoverTimeout] = useState<NodeJS.Timeout | null>(null);
    const router = useRouter();

    const handleItemClick = (item: DropdownItem) => {
        if (item.href) {
            router.push(item.href);
        } else if (item.filters) {
            // Build query string from filters
            const params = new URLSearchParams();
            Object.entries(item.filters).forEach(([key, value]) => {
                if (Array.isArray(value)) {
                    params.set(key, value.join(','));
                } else {
                    params.set(key, value.toString());
                }
            });
            router.push(`/recipes?${params.toString()}`);
        }
        setActiveDropdown(null);
    };

    const handleMouseEnter = (menuLabel: string) => {
        // Clear any existing timeout
        if (hoverTimeout) {
            clearTimeout(hoverTimeout);
            setHoverTimeout(null);
        }
        setActiveDropdown(menuLabel);
    };

    const handleMouseLeave = () => {
        // Set a delay before closing the dropdown
        const timeout = setTimeout(() => {
            setActiveDropdown(null);
        }, 300); // 300ms delay
        setHoverTimeout(timeout);
    };

    const handleDropdownMouseEnter = () => {
        // Clear timeout when mouse enters dropdown
        if (hoverTimeout) {
            clearTimeout(hoverTimeout);
            setHoverTimeout(null);
        }
    };

    const handleDropdownMouseLeave = () => {
        // Close dropdown when mouse leaves dropdown area
        setActiveDropdown(null);
    };

    // Cleanup timeout on unmount
    useEffect(() => {
        return () => {
            if (hoverTimeout) {
                clearTimeout(hoverTimeout);
            }
        };
    }, [hoverTimeout]);

    return (
        <header className="bg-gray-900 text-white shadow-lg sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo and Browse Link */}
                    <div className="flex items-center space-x-6">
                        <Link href="/" className="flex items-center space-x-3 group hover:opacity-80 transition-all duration-200">
                            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg group-hover:shadow-2xl transition-all duration-200 group-hover:rotate-3">
                                <Utensils className="w-6 h-6 text-white drop-shadow-sm" />
                            </div>
                            <h1 className="text-xl font-bold bg-gradient-to-r from-orange-400 via-red-400 to-pink-400 bg-clip-text text-transparent group-hover:from-orange-300 group-hover:via-red-300 group-hover:to-pink-300 transition-all duration-200">
                                Food Recipes
                            </h1>
                        </Link>

                        {/* Browse All Recipes Link */}
                        <Link
                            href="/recipes"
                            className="hidden sm:flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition-all duration-200 bg-gray-800/50 hover:bg-orange-500 rounded-lg border border-gray-700 hover:border-orange-400 hover:shadow-lg hover:shadow-orange-500/25 group"
                        >
                            <Utensils className="w-4 h-4 group-hover:rotate-12 transition-transform duration-200" />
                            <span>Browse All Recipes</span>
                        </Link>
                    </div>

                    {/* Desktop Navigation */}
                    <nav className="hidden lg:flex items-center space-x-1">
                        {navigationMenus.map((menu) => (
                            <div
                                key={menu.label}
                                className="relative"
                                onMouseEnter={() => handleMouseEnter(menu.label)}
                                onMouseLeave={handleMouseLeave}
                            >
                                <button className="px-4 py-2 text-sm font-medium text-white hover:text-orange-400 transition-colors duration-200 flex items-center space-x-1">
                                    <span>{menu.label}</span>
                                    <ChevronDown className="w-4 h-4" />
                                </button>

                                {/* Dropdown Menu */}
                                {activeDropdown === menu.label && (
                                    <div
                                        className="absolute top-full left-0 w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50"
                                        onMouseEnter={handleDropdownMouseEnter}
                                        onMouseLeave={handleDropdownMouseLeave}
                                    >
                                        <div className="py-2">
                                            {menu.items.map((item, index) => (
                                                <button
                                                    key={index}
                                                    onClick={() => handleItemClick(item)}
                                                    className="w-full px-4 py-3 text-left text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors duration-200 flex items-center space-x-3"
                                                >
                                                    {item.icon && <span className="text-orange-400">{item.icon}</span>}
                                                    <span>{item.label}</span>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </nav>

                    {/* Mobile Menu Button */}
                    <div className="flex items-center">
                        <button className="lg:hidden p-2 text-gray-400 hover:text-orange-400 transition-colors duration-200">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Navigation */}
            <div className="lg:hidden bg-gray-800 border-t border-gray-700">
                <div className="px-4 py-2">
                    <div className="grid grid-cols-2 gap-2">
                        {navigationMenus.slice(0, 4).map((menu) => (
                            <div key={menu.label} className="relative">
                                <button
                                    onClick={() => setActiveDropdown(activeDropdown === menu.label ? null : menu.label)}
                                    className="w-full px-3 py-2 text-sm font-medium text-white hover:bg-gray-700 rounded transition-colors duration-200 flex items-center justify-between"
                                >
                                    <span>{menu.label}</span>
                                    <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${activeDropdown === menu.label ? 'rotate-180' : ''}`} />
                                </button>

                                {activeDropdown === menu.label && (
                                    <div className="mt-1 bg-gray-700 rounded-lg shadow-lg">
                                        <div className="py-2">
                                            {menu.items.map((item, index) => (
                                                <button
                                                    key={index}
                                                    onClick={() => handleItemClick(item)}
                                                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-600 hover:text-white transition-colors duration-200 flex items-center space-x-2"
                                                >
                                                    {item.icon && <span className="text-orange-400">{item.icon}</span>}
                                                    <span>{item.label}</span>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </header>
    );
}
