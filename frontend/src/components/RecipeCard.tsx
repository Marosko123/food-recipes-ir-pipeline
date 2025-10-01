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
}

export default function RecipeCard({ recipe, showScore = false, priority = false }: RecipeCardProps) {
    const recipeSlug = generateRecipeSlug(recipe.title, recipe.id);
    const rating = formatRating(recipe.ratings?.rating);
    const reviewCount = recipe.ratings?.review_count;

    return (
        <Link href={`/recipe/${recipeSlug}`}>
            <div className="recipe-card group cursor-pointer overflow-hidden">
                {/* Image */}
                <div className="relative h-48 w-full overflow-hidden">
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
                <div className="p-4">
                    {/* Title */}
                    <h3 className="font-semibold text-lg text-gray-900 mb-2 line-clamp-2 group-hover:text-primary-600 transition-colors">
                        {recipe.title}
                    </h3>

                    {/* Description */}
                    {recipe.description && (
                        <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                            {recipe.description}
                        </p>
                    )}

                    {/* Meta Information */}
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                            {recipe.times?.total && (
                                <div className="flex items-center">
                                    <Clock className="w-4 h-4 mr-1" />
                                    {formatTime(recipe.times.total)}
                                </div>
                            )}
                            {recipe.yield && (
                                <div className="flex items-center">
                                    <Users className="w-4 h-4 mr-1" />
                                    {recipe.yield}
                                </div>
                            )}
                        </div>

                        {rating > 0 && (
                            <div className="flex items-center">
                                <Star className="w-4 h-4 text-yellow-400 mr-1" />
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
                                <span key={index} className="badge badge-secondary text-xs">
                                    {cuisine}
                                </span>
                            ))}
                            {recipe.cuisine.length > 3 && (
                                <span className="badge badge-gray text-xs">
                                    +{recipe.cuisine.length - 3}
                                </span>
                            )}
                        </div>
                    )}

                    {/* Author */}
                    {recipe.author && (
                        <div className="text-xs text-gray-500">
                            by {recipe.author}
                        </div>
                    )}
                </div>
            </div>
        </Link>
    );
}
