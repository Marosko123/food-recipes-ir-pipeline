'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Recipe } from '@/types/recipe';
import { formatTime, formatDifficulty, formatRating, generateRecipeSlug, getPlaceholderImage } from '@/lib/utils';
import { Clock, Users, Star, ChefHat } from 'lucide-react';

interface RecipeCardProps {
    recipe: Recipe;
    showScore?: boolean;
    priority?: boolean;
    compact?: boolean;
}

export default function RecipeCard({ recipe, showScore = false, priority = false, compact = false }: RecipeCardProps) {
    const recipeSlug = generateRecipeSlug(recipe.title, recipe.id);
    const rating = formatRating(recipe.ratings?.rating);
    const reviewCount = recipe.ratings?.review_count;

    // Parse nutrition values
    const parseNutrition = (value: string | undefined): number => {
        if (!value) return 0;
        return parseFloat(value) || 0;
    };

    const calories = parseNutrition(recipe.nutrition?.calories);
    const protein = parseNutrition(recipe.nutrition?.protein);

    // Compact version for meal planner
    if (compact) {
        return (
            <Link href={`/recipe/${recipeSlug}`}>
                <div className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow bg-white">
                    {recipe.image && (
                        <div className="relative h-32 bg-gray-200">
                            <Image
                                src={recipe.image}
                                alt={recipe.title}
                                fill
                                className="object-cover"
                                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
                            />
                        </div>
                    )}
                    <div className="p-3">
                        <h4 className="font-semibold text-sm text-gray-900 line-clamp-2 mb-2">
                            {recipe.title}
                        </h4>
                        
                        {/* Compact Nutrition */}
                        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                            <div>
                                <span className="font-medium">{Math.round(calories)}</span> cal
                            </div>
                            <div>
                                <span className="font-medium">{Math.round(protein)}g</span> protein
                            </div>
                        </div>

                        {recipe.times?.total && (
                            <div className="flex items-center text-xs text-gray-500 mt-2">
                                <Clock className="w-3 h-3 mr-1" />
                                <span>{recipe.times.total} min</span>
                            </div>
                        )}
                    </div>
                </div>
            </Link>
        );
    }

    // Full version
    return (
        <Link href={`/recipe/${recipeSlug}`} className="h-full">
            <div className="recipe-card group cursor-pointer overflow-hidden">
                {/* Image */}
                <div className="relative h-48 w-full overflow-hidden flex-shrink-0">
                    <Image
                        src={recipe.image || getPlaceholderImage()}
                        alt={recipe.title}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-300"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                        priority={priority}
                    />
                    {recipe.difficulty && (
                        <div className="absolute top-3 left-3">
                            <span className="badge badge-primary">
                                <ChefHat className="w-3 h-3 mr-1" />
                                {formatDifficulty(recipe.difficulty)}
                            </span>
                        </div>
                    )}
                    {showScore && recipe.score && (
                        <div className="absolute top-3 right-3">
                            <span className="badge bg-black/70 text-white">
                                Score: {recipe.score.toFixed(2)}
                            </span>
                        </div>
                    )}
                </div>

                {/* Content */}
                <div className="recipe-card-content">
                    {/* Title */}
                    <h3 className="font-semibold text-lg text-gray-900 mb-2 line-clamp-2 group-hover:text-primary-600 transition-colors" style={{ minHeight: '3.5rem' }}>
                        {recipe.title}
                    </h3>

                    {/* Description */}
                    <div className="flex-1">
                        {recipe.description ? (
                            <p className="text-gray-600 text-sm mb-3 line-clamp-2" style={{ minHeight: '2.5rem' }}>
                                {recipe.description}
                            </p>
                        ) : (
                            <div style={{ minHeight: '2.5rem' }} />
                        )}
                    </div>

                    {/* Meta Information - Always at bottom */}
                    <div className="recipe-card-meta mt-auto">
                        <div className="flex items-center justify-between gap-2 mb-3 flex-wrap">
                            <div className="flex items-center gap-3 text-sm text-gray-500 flex-shrink-0">
                                {recipe.times?.total && (
                                    <div className="flex items-center whitespace-nowrap">
                                        <Clock className="w-4 h-4 mr-1 flex-shrink-0" />
                                        <span>{formatTime(recipe.times.total)}</span>
                                    </div>
                                )}
                                {recipe.yield && (
                                    <div className="flex items-center whitespace-nowrap">
                                        <Users className="w-4 h-4 mr-1 flex-shrink-0" />
                                        <span className="truncate max-w-[100px]">{recipe.yield}</span>
                                    </div>
                                )}
                            </div>

                            {rating > 0 && (
                                <div className="flex items-center whitespace-nowrap flex-shrink-0">
                                    <Star className="w-4 h-4 text-yellow-400 mr-1 fill-yellow-400" />
                                    <span className="text-sm font-medium text-gray-700">
                                        {rating.toFixed(1)}
                                    </span>
                                    {reviewCount && (
                                        <span className="text-xs text-gray-500 ml-1">
                                            ({reviewCount})
                                        </span>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Cuisine Tags */}
                        {recipe.cuisine.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-3">
                                {recipe.cuisine.slice(0, 3).map((cuisine, index) => (
                                    <span key={index} className="badge badge-secondary text-xs whitespace-nowrap">
                                        {cuisine}
                                    </span>
                                ))}
                                {recipe.cuisine.length > 3 && (
                                    <span className="badge badge-gray text-xs whitespace-nowrap">
                                        +{recipe.cuisine.length - 3}
                                    </span>
                                )}
                            </div>
                        )}

                        {/* Author */}
                        {recipe.author && (
                            <div className="text-xs text-gray-500 truncate">
                                by {recipe.author}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Link>
    );
}
