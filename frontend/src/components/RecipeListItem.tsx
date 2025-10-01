'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Recipe } from '@/types/recipe';
import { formatTime, formatDifficulty, formatRating, generateRecipeSlug, getPlaceholderImage } from '@/lib/utils';
import { Clock, Users, Star, ChefHat, ExternalLink } from 'lucide-react';

interface RecipeListItemProps {
    recipe: Recipe;
    showScore?: boolean;
}

export default function RecipeListItem({ recipe, showScore = false }: RecipeListItemProps) {
    const recipeSlug = generateRecipeSlug(recipe.title, recipe.id);
    const rating = formatRating(recipe.ratings?.rating);
    const reviewCount = recipe.ratings?.review_count;

    return (
        <div className="bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow duration-200">
            <div className="flex">
                {/* Image */}
                <div className="relative w-48 h-32 flex-shrink-0">
                    <Link href={`/recipe/${recipeSlug}`}>
                        <Image
                            src={recipe.image || getPlaceholderImage()}
                            alt={recipe.title}
                            fill
                            className="object-cover rounded-l-lg"
                            sizes="192px"
                        />
                    </Link>
                    {recipe.difficulty && (
                        <div className="absolute top-2 left-2">
                            <span className="badge badge-primary text-xs">
                                <ChefHat className="w-3 h-3 mr-1" />
                                {formatDifficulty(recipe.difficulty)}
                            </span>
                        </div>
                    )}
                    {showScore && recipe.score && (
                        <div className="absolute top-2 right-2">
                            <span className="badge bg-black/70 text-white text-xs">
                                {recipe.score.toFixed(2)}
                            </span>
                        </div>
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 p-4">
                    <div className="flex justify-between items-start mb-2">
                        <Link href={`/recipe/${recipeSlug}`}>
                            <h3 className="text-lg font-semibold text-gray-900 hover:text-primary-600 transition-colors line-clamp-1">
                                {recipe.title}
                            </h3>
                        </Link>
                        <a
                            href={recipe.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-gray-400 hover:text-gray-600 ml-2"
                            title="View original"
                        >
                            <ExternalLink className="w-4 h-4" />
                        </a>
                    </div>

                    {/* Description */}
                    {recipe.description && (
                        <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                            {recipe.description}
                        </p>
                    )}

                    {/* Meta Information Row 1 */}
                    <div className="flex items-center justify-between mb-2">
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
                            {recipe.author && (
                                <div className="text-xs text-gray-500">
                                    by {recipe.author}
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

                    {/* Tags and Categories */}
                    <div className="flex flex-wrap gap-1">
                        {recipe.cuisine.slice(0, 2).map((cuisine, index) => (
                            <span key={`cuisine-${index}`} className="badge badge-primary text-xs">
                                {cuisine}
                            </span>
                        ))}
                        {recipe.category.slice(0, 2).map((category, index) => (
                            <span key={`category-${index}`} className="badge badge-secondary text-xs">
                                {category}
                            </span>
                        ))}
                        {recipe.keywords.slice(0, 3).map((keyword, index) => (
                            <span key={`keyword-${index}`} className="badge badge-gray text-xs">
                                {keyword}
                            </span>
                        ))}
                        {(recipe.cuisine.length + recipe.category.length + recipe.keywords.length > 7) && (
                            <span className="badge badge-gray text-xs">
                                +{(recipe.cuisine.length + recipe.category.length + recipe.keywords.length) - 7} more
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

