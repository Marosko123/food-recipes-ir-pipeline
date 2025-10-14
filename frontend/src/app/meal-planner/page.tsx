'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Calculator, User, Activity, Target, TrendingUp, Utensils, Clock, Flame, Scale, Share2, CheckCircle, Copy, Coffee, Sun, Moon, Cookie, RefreshCw } from 'lucide-react';
import { Recipe } from '@/types/recipe';
import RecipeCard from '@/components/RecipeCard';
import { apiClient } from '@/lib/api';

type Gender = 'male' | 'female';
type ActivityLevel = 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';
type Goal = 'lose' | 'maintain' | 'gain' | 'muscle';
type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snacks';

interface UserProfile {
    gender: Gender;
    age: number;
    height: number; // cm
    weight: number; // kg
    activityLevel: ActivityLevel;
    goal: Goal;
}

interface MealPlan {
    breakfast: Recipe[];
    lunch: Recipe[];
    dinner: Recipe[];
    snacks: Recipe[];
}

interface DailyTargets {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
}

interface MealTargets {
    breakfast: DailyTargets;
    lunch: DailyTargets;
    dinner: DailyTargets;
    snacks: DailyTargets;
}

function MealPlannerContent() {
    const searchParams = useSearchParams();
    const router = useRouter();

    const [profile, setProfile] = useState<UserProfile>({
        gender: 'male',
        age: 25,
        height: 175,
        weight: 70,
        activityLevel: 'moderate',
        goal: 'maintain'
    });

    // Load profile from localStorage on mount
    useEffect(() => {
        const savedProfile = localStorage.getItem('mealPlannerProfile');
        if (savedProfile) {
            try {
                const parsed = JSON.parse(savedProfile);
                setProfile(parsed);
            } catch (error) {
                console.error('Failed to parse saved profile:', error);
            }
        }
    }, []);    const [targets, setTargets] = useState<DailyTargets | null>(null);
    const [mealTargets, setMealTargets] = useState<MealTargets | null>(null);
    const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
    const [loading, setLoading] = useState(false);
    const [regeneratingMeal, setRegeneratingMeal] = useState<MealType | null>(null);
    const [recipes, setRecipes] = useState<Recipe[]>([]);
    const [shareUrl, setShareUrl] = useState<string>('');
    const [copied, setCopied] = useState(false);
    const [validationErrors, setValidationErrors] = useState<string[]>([]);

    // Load profile from URL on mount
    useEffect(() => {
        const urlGender = searchParams.get('gender');
        const urlAge = searchParams.get('age');
        const urlHeight = searchParams.get('height');
        const urlWeight = searchParams.get('weight');
        const urlActivity = searchParams.get('activity');
        const urlGoal = searchParams.get('goal');

        if (urlGender || urlAge || urlHeight || urlWeight || urlActivity || urlGoal) {
            setProfile({
                gender: (urlGender as Gender) || 'male',
                age: parseInt(urlAge || '30'),
                height: parseInt(urlHeight || '175'),
                weight: parseInt(urlWeight || '75'),
                activityLevel: (urlActivity as ActivityLevel) || 'moderate',
                goal: (urlGoal as Goal) || 'maintain'
            });
            
            // Auto-generate meal plan from shared link
            setTimeout(() => {
                const btn = document.getElementById('generate-btn');
                if (btn) btn.click();
            }, 500);
        }
    }, [searchParams]);

    // Load recipes on mount
    useEffect(() => {
        loadRecipes();
    }, []);

    const loadRecipes = async () => {
        try {
            const response = await apiClient.searchRecipes({
                per_page: 500,
                query: '',
                metric: 'bm25'
            });
            setRecipes(response.results || response.recipes || []);
        } catch (error) {
            console.error('Failed to load recipes:', error);
        }
    };

    // Calculate BMR using Harris-Benedict equation
    const calculateBMR = (profile: UserProfile): number => {
        if (profile.gender === 'male') {
            return 88.362 + (13.397 * profile.weight) + (4.799 * profile.height) - (5.677 * profile.age);
        } else {
            return 447.593 + (9.247 * profile.weight) + (3.098 * profile.height) - (4.330 * profile.age);
        }
    };

    // Calculate TDEE (Total Daily Energy Expenditure)
    const calculateTDEE = (bmr: number, activityLevel: ActivityLevel): number => {
        const multipliers: Record<ActivityLevel, number> = {
            sedentary: 1.2,
            light: 1.375,
            moderate: 1.55,
            active: 1.725,
            very_active: 1.9
        };
        return bmr * multipliers[activityLevel];
    };

    // Calculate meal-specific targets
    const calculateMealTargets = (dailyTargets: DailyTargets): MealTargets => {
        return {
            breakfast: {
                calories: Math.round(dailyTargets.calories * 0.25),
                protein: Math.round(dailyTargets.protein * 0.25),
                carbs: Math.round(dailyTargets.carbs * 0.25),
                fat: Math.round(dailyTargets.fat * 0.25)
            },
            lunch: {
                calories: Math.round(dailyTargets.calories * 0.35),
                protein: Math.round(dailyTargets.protein * 0.35),
                carbs: Math.round(dailyTargets.carbs * 0.35),
                fat: Math.round(dailyTargets.fat * 0.35)
            },
            dinner: {
                calories: Math.round(dailyTargets.calories * 0.30),
                protein: Math.round(dailyTargets.protein * 0.30),
                carbs: Math.round(dailyTargets.carbs * 0.30),
                fat: Math.round(dailyTargets.fat * 0.30)
            },
            snacks: {
                calories: Math.round(dailyTargets.calories * 0.10),
                protein: Math.round(dailyTargets.protein * 0.10),
                carbs: Math.round(dailyTargets.carbs * 0.10),
                fat: Math.round(dailyTargets.fat * 0.10)
            }
        };
    };

    // Calculate daily targets based on goal
    const calculateTargets = (profile: UserProfile): DailyTargets => {
        const bmr = calculateBMR(profile);
        const tdee = calculateTDEE(bmr, profile.activityLevel);
        
        let calories = tdee;
        let proteinPercent = 0.25;
        let carbsPercent = 0.45;
        let fatPercent = 0.30;

        switch (profile.goal) {
            case 'lose':
                calories = tdee * 0.85; // 15% deficit
                proteinPercent = 0.35;
                carbsPercent = 0.35;
                fatPercent = 0.30;
                break;
            case 'gain':
                calories = tdee * 1.10; // 10% surplus
                proteinPercent = 0.25;
                carbsPercent = 0.50;
                fatPercent = 0.25;
                break;
            case 'muscle':
                calories = tdee * 1.15; // 15% surplus
                proteinPercent = 0.35; // High protein for muscle growth
                carbsPercent = 0.45;
                fatPercent = 0.20;
                break;
            case 'maintain':
            default:
                calories = tdee;
                break;
        }

        return {
            calories: Math.round(calories),
            protein: Math.round((calories * proteinPercent) / 4), // 4 cal per gram
            carbs: Math.round((calories * carbsPercent) / 4),
            fat: Math.round((calories * fatPercent) / 9) // 9 cal per gram
        };
    };

    // Parse nutrition value from string
    const parseNutrition = (value: string | undefined): number => {
        if (!value) return 0;
        return parseFloat(value) || 0;
    };

    // Calculate recipe nutrition
    const getRecipeNutrition = (recipe: Recipe) => {
        return {
            calories: parseNutrition(recipe.nutrition?.calories),
            protein: parseNutrition(recipe.nutrition?.protein),
            carbs: parseNutrition(recipe.nutrition?.carbohydrates),
            fat: parseNutrition(recipe.nutrition?.fat)
        };
    };

    // Calculate total nutrition for a meal
    const calculateMealNutrition = (recipes: Recipe[]): DailyTargets => {
        return recipes.reduce((acc, recipe) => {
            const nutr = getRecipeNutrition(recipe);
            return {
                calories: acc.calories + nutr.calories,
                protein: acc.protein + nutr.protein,
                carbs: acc.carbs + nutr.carbs,
                fat: acc.fat + nutr.fat
            };
        }, { calories: 0, protein: 0, carbs: 0, fat: 0 });
    };

    // Filter recipes by meal type and nutritional criteria
    const filterRecipesByMeal = (mealType: MealType, targetCals: number, excludeIds: string[] = []) => {
        // Primary category terms (highest priority)
        const categoryTerms: Record<string, string[]> = {
            breakfast: ['breakfast', 'brunch'],
            lunch: ['lunch'],
            dinner: ['dinner', 'main dish', 'main course'],
            snacks: ['snack', 'appetizer', 'dessert']
        };

        // Exclude terms - recipes with these in title should NOT be in this meal type
        const excludeTerms: Record<string, string[]> = {
            breakfast: ['dinner', 'lunch', 'kabob', 'kabab', 'bbq', 'barbecue', 'grilled chicken', 'roast', 'casserole', 'steak', 'curry', 'pasta', 'ribs', 'brisket'],
            lunch: [],
            dinner: ['breakfast', 'brunch', 'cereal', 'oatmeal'],
            snacks: ['breakfast', 'dinner', 'lunch', 'main']
        };

        // Secondary keyword terms (fallback if no category match)
        const keywordTerms: Record<string, string[]> = {
            breakfast: ['morning', 'cereal', 'pancake', 'waffle', 'egg', 'oatmeal', 'smoothie', 'french toast', 'bagel', 'muffin', 'toast', 'bacon', 'sausage', 'hash brown', 'crepe', 'omelet', 'scramble', 'breakfast burrito'],
            lunch: ['sandwich', 'salad', 'soup', 'wrap', 'burger', 'pizza'],
            dinner: ['entree', 'casserole', 'roast', 'steak', 'chicken breast', 'pasta', 'curry', 'stir fry', 'grilled'],
            snacks: ['bar', 'bite', 'cookie', 'brownie', 'cake', 'pie', 'chips', 'dip']
        };

        const categories = categoryTerms[mealType];
        const keywords = keywordTerms[mealType];
        const excludes = excludeTerms[mealType];
        const calMin = targetCals * 0.7;
        const calMax = targetCals * 1.3;

        // First, try to find recipes with matching category
        let filtered = recipes.filter(recipe => {
            if (excludeIds.includes(recipe.id)) return false;
            
            const nutrition = getRecipeNutrition(recipe);
            const lowerTitle = recipe.title.toLowerCase();
            
            // Exclude recipes with wrong meal type indicators in title
            const hasExcludedTerm = excludes.some(term => lowerTitle.includes(term));
            if (hasExcludedTerm) return false;
            
            // Check category first (strict matching)
            const matchesCategory = categories.some(cat => 
                recipe.category.some(recipeCat => recipeCat.toLowerCase() === cat.toLowerCase())
            );
            
            const matchesCals = nutrition.calories >= calMin && nutrition.calories <= calMax;
            const hasImage = !!recipe.image;
            const validNutrition = nutrition.calories > 50 && nutrition.protein > 0;
            
            return matchesCategory && matchesCals && hasImage && validNutrition;
        });

        // If not enough category matches, add keyword matches as fallback
        if (filtered.length < 10) {
            const keywordMatches = recipes.filter(recipe => {
                if (excludeIds.includes(recipe.id)) return false;
                const nutrition = getRecipeNutrition(recipe);
                const lowerTitle = recipe.title.toLowerCase();
                
                // Check if already in filtered list
                if (filtered.some(f => f.id === recipe.id)) return false;
                
                // Exclude recipes with wrong meal type indicators in title
                const hasExcludedTerm = excludes.some(term => lowerTitle.includes(term));
                if (hasExcludedTerm) return false;
                
                // Check keywords and title
                const matchesKeyword = keywords.some(kw => 
                    lowerTitle.includes(kw) ||
                    recipe.keywords.some(k => k.toLowerCase().includes(kw))
                );
                
                const matchesCals = nutrition.calories >= calMin && nutrition.calories <= calMax;
                const hasImage = !!recipe.image;
                const validNutrition = nutrition.calories > 50 && nutrition.protein > 0;
                
                return matchesKeyword && matchesCals && hasImage && validNutrition;
            });
            
            filtered = [...filtered, ...keywordMatches];
        }

        // Shuffle for variety, then sort by calorie proximity
        const shuffled = filtered.sort(() => Math.random() - 0.5);
        
        return shuffled.sort((a, b) => {
            const aNutr = getRecipeNutrition(a);
            const bNutr = getRecipeNutrition(b);
            const aDiff = Math.abs(aNutr.calories - targetCals);
            const bDiff = Math.abs(bNutr.calories - targetCals);
            return aDiff - bDiff;
        });
    };

    // Validate inputs
    const validateProfile = (): string[] => {
        const errors: string[] = [];
        
        if (profile.age < 18 || profile.age > 100) {
            errors.push('Age must be between 18 and 100 years');
        }
        if (profile.height < 120 || profile.height > 250) {
            errors.push('Height must be between 120 and 250 cm');
        }
        if (profile.weight < 40 || profile.weight > 200) {
            errors.push('Weight must be between 40 and 200 kg');
        }
        
        return errors;
    };

    // Generate shareable URL
    const generateShareUrl = () => {
        const params = new URLSearchParams({
            gender: profile.gender,
            age: profile.age.toString(),
            height: profile.height.toString(),
            weight: profile.weight.toString(),
            activity: profile.activityLevel,
            goal: profile.goal
        });
        
        const url = `${window.location.origin}/meal-planner?${params.toString()}`;
        setShareUrl(url);
        return url;
    };

    // Copy to clipboard
    const copyToClipboard = async () => {
        try {
            await navigator.clipboard.writeText(shareUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            alert('Failed to copy to clipboard');
        }
    };

    // Generate recipes for a specific meal
    const generateMealRecipes = (mealType: MealType, targetCals: number, excludeIds: string[] = []): Recipe[] => {
        const availableRecipes = filterRecipesByMeal(mealType, targetCals, excludeIds);
        
        if (availableRecipes.length === 0) {
            console.warn(`No recipes found for ${mealType} with target calories ${targetCals}`);
            return [];
        }

        const selected: Recipe[] = [];
        let totalCals = 0;

        // Select recipes until we reach target calories
        for (const recipe of availableRecipes) {
            if (selected.length >= 3) break; // Max 3 recipes per meal
            
            const recipeNutr = getRecipeNutrition(recipe);
            
            // Skip if this recipe would put us way over budget (unless it's the first one)
            if (selected.length > 0 && totalCals + recipeNutr.calories > targetCals * 1.3) {
                continue;
            }
            
            // Add the recipe
            selected.push(recipe);
            totalCals += recipeNutr.calories;
            
            // Stop if we're in the sweet spot (90-120% of target)
            if (totalCals >= targetCals * 0.9 && totalCals <= targetCals * 1.2) {
                break;
            }
        }

        // If we have no recipes, take at least one
        if (selected.length === 0 && availableRecipes.length > 0) {
            selected.push(availableRecipes[0]);
        }

        return selected;
    };

    // Regenerate a specific meal with smart nutrient targeting
    const regenerateMeal = (mealType: MealType) => {
        if (!mealPlan || !mealTargets || !targets) return;

        setRegeneratingMeal(mealType);

        // Calculate current daily totals to see what we need
        const dailyTotals = calculateDailyTotals();
        
        let targetAdjustment = 1.0; // Default multiplier
        let preferProtein = false;
        let preferLowCal = false;
        let preferLowFat = false;
        
        if (dailyTotals) {
            const calorieRatio = dailyTotals.calories / targets.calories;
            const proteinRatio = dailyTotals.protein / targets.protein;
            const fatRatio = dailyTotals.fat / targets.fat;
            
            // If we're over on calories, aim for lower calorie options
            if (calorieRatio > 1.15) {
                targetAdjustment = 0.8; // Aim for 80% of meal target
                preferLowCal = true;
                console.log(`🔽 Over calories (${Math.round(calorieRatio * 100)}%), selecting lighter options`);
            }
            // If we're under on calories, aim for higher calorie options
            else if (calorieRatio < 0.85) {
                targetAdjustment = 1.2; // Aim for 120% of meal target
                console.log(`🔼 Under calories (${Math.round(calorieRatio * 100)}%), selecting heartier options`);
            }
            
            // If we're under on protein, prefer high-protein options
            if (proteinRatio < 0.85) {
                preferProtein = true;
                console.log(`💪 Under protein (${Math.round(proteinRatio * 100)}%), prioritizing high-protein recipes`);
            }
            
            // If we're over on fat, prefer low-fat options
            if (fatRatio > 1.15) {
                preferLowFat = true;
                console.log(`🥑 Over fat (${Math.round(fatRatio * 100)}%), selecting low-fat options`);
            }
        }

        // Get all currently used recipe IDs
        const usedIds = [
            ...mealPlan.breakfast.map(r => r.id),
            ...mealPlan.lunch.map(r => r.id),
            ...mealPlan.dinner.map(r => r.id),
            ...mealPlan.snacks.map(r => r.id)
        ];

        // Generate new recipes with adjusted target
        const adjustedTargetCals = mealTargets[mealType].calories * targetAdjustment;
        const availableRecipes = filterRecipesByMeal(mealType, adjustedTargetCals, usedIds);
        
        // Apply smart sorting based on nutritional needs
        const smartSorted = availableRecipes.sort((a, b) => {
            const aNutr = getRecipeNutrition(a);
            const bNutr = getRecipeNutrition(b);
            
            let aScore = 0;
            let bScore = 0;
            
            // Score based on calorie proximity
            const aCalDiff = Math.abs(aNutr.calories - adjustedTargetCals);
            const bCalDiff = Math.abs(bNutr.calories - adjustedTargetCals);
            aScore += (1000 - aCalDiff) * 2; // Calorie proximity is important
            bScore += (1000 - bCalDiff) * 2;
            
            // Prefer high protein if needed
            if (preferProtein) {
                const proteinPerCal_a = aNutr.protein / (aNutr.calories || 1);
                const proteinPerCal_b = bNutr.protein / (bNutr.calories || 1);
                aScore += proteinPerCal_a * 5000; // High weight for protein density
                bScore += proteinPerCal_b * 5000;
            }
            
            // Prefer low calorie if needed
            if (preferLowCal) {
                aScore += (2000 - aNutr.calories) * 1.5;
                bScore += (2000 - bNutr.calories) * 1.5;
            }
            
            // Prefer low fat if needed
            if (preferLowFat) {
                aScore += (100 - aNutr.fat) * 10;
                bScore += (100 - bNutr.fat) * 10;
            }
            
            return bScore - aScore; // Higher score first
        });

        // Select recipes from the smart-sorted list
        const selected: Recipe[] = [];
        let totalCals = 0;

        for (const recipe of smartSorted) {
            if (selected.length >= 3) break;
            
            const recipeNutr = getRecipeNutrition(recipe);
            
            if (selected.length > 0 && totalCals + recipeNutr.calories > adjustedTargetCals * 1.3) {
                continue;
            }
            
            selected.push(recipe);
            totalCals += recipeNutr.calories;
            
            if (totalCals >= adjustedTargetCals * 0.9 && totalCals <= adjustedTargetCals * 1.2) {
                break;
            }
        }

        // If we have no recipes, take at least one
        if (selected.length === 0 && smartSorted.length > 0) {
            selected.push(smartSorted[0]);
        }

        // Update meal plan
        setMealPlan({
            ...mealPlan,
            [mealType]: selected
        });

        setRegeneratingMeal(null);
    };

    // Regenerate all meals at once
    const regenerateAllMeals = () => {
        if (!mealTargets) return;

        setLoading(true);

        // Generate completely new recipes for all meals
        const breakfastRecipes = generateMealRecipes('breakfast', mealTargets.breakfast.calories);
        const usedIds = breakfastRecipes.map(r => r.id);
        
        const lunchRecipes = generateMealRecipes('lunch', mealTargets.lunch.calories, usedIds);
        usedIds.push(...lunchRecipes.map(r => r.id));
        
        const dinnerRecipes = generateMealRecipes('dinner', mealTargets.dinner.calories, usedIds);
        usedIds.push(...dinnerRecipes.map(r => r.id));
        
        const snackRecipes = generateMealRecipes('snacks', mealTargets.snacks.calories, usedIds);

        setMealPlan({
            breakfast: breakfastRecipes,
            lunch: lunchRecipes,
            dinner: dinnerRecipes,
            snacks: snackRecipes
        });

        setLoading(false);
    };

    // Generate meal plan
    const generateMealPlan = () => {
        // Validate first
        const errors = validateProfile();
        setValidationErrors(errors);
        
        if (errors.length > 0) {
            return;
        }

        if (recipes.length === 0) {
            alert('Recipes are still loading. Please try again in a moment.');
            return;
        }

        // Save profile to localStorage
        try {
            localStorage.setItem('mealPlannerProfile', JSON.stringify(profile));
        } catch (error) {
            console.error('Failed to save profile to localStorage:', error);
        }

        setLoading(true);

        const calculatedTargets = calculateTargets(profile);
        setTargets(calculatedTargets);

        const calculatedMealTargets = calculateMealTargets(calculatedTargets);
        setMealTargets(calculatedMealTargets);
        
        // Generate share URL
        generateShareUrl();

        // Generate recipes for each meal
        const breakfastRecipes = generateMealRecipes('breakfast', calculatedMealTargets.breakfast.calories);
        const usedIds = breakfastRecipes.map(r => r.id);
        
        const lunchRecipes = generateMealRecipes('lunch', calculatedMealTargets.lunch.calories, usedIds);
        usedIds.push(...lunchRecipes.map(r => r.id));
        
        const dinnerRecipes = generateMealRecipes('dinner', calculatedMealTargets.dinner.calories, usedIds);
        usedIds.push(...dinnerRecipes.map(r => r.id));
        
        const snackRecipes = generateMealRecipes('snacks', calculatedMealTargets.snacks.calories, usedIds);

        setMealPlan({
            breakfast: breakfastRecipes,
            lunch: lunchRecipes,
            dinner: dinnerRecipes,
            snacks: snackRecipes
        });

        setLoading(false);
    };

    const activityLevels: { value: ActivityLevel; label: string; description: string }[] = [
        { value: 'sedentary', label: 'Sedentary', description: 'Little or no exercise' },
        { value: 'light', label: 'Light', description: '1-3 days/week' },
        { value: 'moderate', label: 'Moderate', description: '3-5 days/week' },
        { value: 'active', label: 'Active', description: '6-7 days/week' },
        { value: 'very_active', label: 'Very Active', description: 'Athlete/Physical job' }
    ];

    const goals: { value: Goal; label: string; description: string }[] = [
        { value: 'lose', label: 'Weight Loss', description: '15% calorie deficit' },
        { value: 'maintain', label: 'Maintenance', description: 'Maintain current weight' },
        { value: 'gain', label: 'Weight Gain', description: '10% calorie surplus' },
        { value: 'muscle', label: 'Muscle Growth', description: '15% surplus, high protein' }
    ];

    const getMealIcon = (mealType: MealType) => {
        switch (mealType) {
            case 'breakfast': return <Coffee className="w-6 h-6" />;
            case 'lunch': return <Sun className="w-6 h-6" />;
            case 'dinner': return <Moon className="w-6 h-6" />;
            case 'snacks': return <Cookie className="w-6 h-6" />;
        }
    };

    const getMealTitle = (mealType: MealType) => {
        return mealType.charAt(0).toUpperCase() + mealType.slice(1);
    };

    // Calculate total nutrition for the entire day
    const calculateDailyTotals = (): DailyTargets | null => {
        if (!mealPlan) return null;
        
        const allRecipes = [
            ...mealPlan.breakfast,
            ...mealPlan.lunch,
            ...mealPlan.dinner,
            ...mealPlan.snacks
        ];
        
        return calculateMealNutrition(allRecipes);
    };

    // Get status color based on percentage of target
    const getStatusColor = (actual: number, target: number): string => {
        const percentage = (actual / target) * 100;
        if (percentage < 85) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
        if (percentage > 115) return 'text-red-600 bg-red-50 border-red-200';
        return 'text-green-600 bg-green-50 border-green-200';
    };

    // Get status icon based on percentage of target
    const getStatusIcon = (actual: number, target: number) => {
        const percentage = (actual / target) * 100;
        if (percentage < 85) return '⚠️';
        if (percentage > 115) return '⚠️';
        return '✅';
    };

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold text-gray-900 mb-4">
                        Personalized Meal Planner
                    </h1>
                    <p className="text-xl text-gray-600">
                        Create custom meal plans based on your goals and nutritional needs
                    </p>
                </div>

                {/* Profile Input Form */}
                <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
                    <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                        <User className="w-6 h-6 mr-2 text-primary-600" />
                        Your Profile
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {/* Gender */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Gender
                            </label>
                            <div className="flex space-x-4">
                                <button
                                    onClick={() => setProfile({ ...profile, gender: 'male' })}
                                    className={`flex-1 py-2 px-4 rounded-lg border-2 transition-colors ${
                                        profile.gender === 'male'
                                            ? 'border-primary-600 bg-primary-50 text-primary-700'
                                            : 'border-gray-300 hover:border-gray-400'
                                    }`}
                                >
                                    Male
                                </button>
                                <button
                                    onClick={() => setProfile({ ...profile, gender: 'female' })}
                                    className={`flex-1 py-2 px-4 rounded-lg border-2 transition-colors ${
                                        profile.gender === 'female'
                                            ? 'border-primary-600 bg-primary-50 text-primary-700'
                                            : 'border-gray-300 hover:border-gray-400'
                                    }`}
                                >
                                    Female
                                </button>
                            </div>
                        </div>

                        {/* Age */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Age (years)
                            </label>
                            <input
                                type="number"
                                value={profile.age}
                                onChange={(e) => setProfile({ ...profile, age: parseInt(e.target.value) || 0 })}
                                className="w-full input-field"
                                min="18"
                                max="100"
                            />
                        </div>

                        {/* Height */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Height (cm)
                            </label>
                            <input
                                type="number"
                                value={profile.height}
                                onChange={(e) => setProfile({ ...profile, height: parseInt(e.target.value) || 0 })}
                                className="w-full input-field"
                                min="120"
                                max="250"
                            />
                        </div>

                        {/* Weight */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Weight (kg)
                            </label>
                            <input
                                type="number"
                                value={profile.weight}
                                onChange={(e) => setProfile({ ...profile, weight: parseInt(e.target.value) || 0 })}
                                className="w-full input-field"
                                min="40"
                                max="200"
                            />
                        </div>

                        {/* Activity Level */}
                        <div className="md:col-span-2">
                            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <Activity className="w-4 h-4 mr-1" />
                                Activity Level
                            </label>
                            <select
                                value={profile.activityLevel}
                                onChange={(e) => setProfile({ ...profile, activityLevel: e.target.value as ActivityLevel })}
                                className="w-full input-field"
                            >
                                {activityLevels.map(level => (
                                    <option key={level.value} value={level.value}>
                                        {level.label} - {level.description}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Goal */}
                        <div className="md:col-span-3">
                            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <Target className="w-4 h-4 mr-1" />
                                Goal
                            </label>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                                {goals.map(goal => (
                                    <button
                                        key={goal.value}
                                        onClick={() => setProfile({ ...profile, goal: goal.value })}
                                        className={`py-3 px-4 rounded-lg border-2 transition-colors text-left ${
                                            profile.goal === goal.value
                                                ? 'border-primary-600 bg-primary-50 text-primary-700'
                                                : 'border-gray-300 hover:border-gray-400'
                                        }`}
                                    >
                                        <div className="font-semibold">{goal.label}</div>
                                        <div className="text-xs text-gray-600">{goal.description}</div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Validation Errors */}
                    {validationErrors.length > 0 && (
                        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
                            <h4 className="text-red-800 font-semibold mb-2">Please fix the following errors:</h4>
                            <ul className="list-disc list-inside text-red-700 text-sm space-y-1">
                                {validationErrors.map((error, idx) => (
                                    <li key={idx}>{error}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Generate Button */}
                    <div className="mt-6 flex justify-center">
                        <button
                            id="generate-btn"
                            onClick={generateMealPlan}
                            disabled={loading}
                            className="btn-primary px-8 py-3 text-lg flex items-center space-x-2"
                        >
                            <Calculator className="w-5 h-5" />
                            <span>{loading ? 'Generating...' : 'Generate My Meal Plan'}</span>
                        </button>
                    </div>
                </div>

                {/* Daily Targets */}
                {targets && (
                    <>
                        <div className="bg-gradient-to-r from-primary-600 to-orange-500 rounded-lg shadow-lg p-6 mb-6 text-white">
                            <h2 className="text-2xl font-bold mb-4 flex items-center">
                                <TrendingUp className="w-6 h-6 mr-2" />
                                Your Daily Targets
                            </h2>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
                                    <div className="flex items-center mb-2">
                                        <Flame className="w-5 h-5 mr-2" />
                                        <span className="text-sm font-medium">Calories</span>
                                    </div>
                                    <div className="text-3xl font-bold">{targets.calories}</div>
                                    <div className="text-xs opacity-80">kcal</div>
                                </div>
                                <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
                                    <div className="flex items-center mb-2">
                                        <TrendingUp className="w-5 h-5 mr-2" />
                                        <span className="text-sm font-medium">Protein</span>
                                    </div>
                                    <div className="text-3xl font-bold">{targets.protein}</div>
                                    <div className="text-xs opacity-80">grams</div>
                                </div>
                                <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
                                    <div className="flex items-center mb-2">
                                        <Utensils className="w-5 h-5 mr-2" />
                                        <span className="text-sm font-medium">Carbs</span>
                                    </div>
                                    <div className="text-3xl font-bold">{targets.carbs}</div>
                                    <div className="text-xs opacity-80">grams</div>
                                </div>
                                <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
                                    <div className="flex items-center mb-2">
                                        <Scale className="w-5 h-5 mr-2" />
                                        <span className="text-sm font-medium">Fat</span>
                                    </div>
                                    <div className="text-3xl font-bold">{targets.fat}</div>
                                    <div className="text-xs opacity-80">grams</div>
                                </div>
                            </div>
                        </div>

                        {/* Share Section */}
                        <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 mb-8 shadow-md">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center">
                                    <Share2 className="w-6 h-6 text-purple-600 mr-2" />
                                    <h3 className="text-xl font-semibold text-gray-800">Share Your Meal Plan</h3>
                                </div>
                                {!shareUrl && (
                                    <button
                                        onClick={() => {
                                            const url = generateShareUrl();
                                            setShareUrl(url);
                                        }}
                                        className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2"
                                    >
                                        <Share2 className="w-4 h-4" />
                                        <span>Generate Share Link</span>
                                    </button>
                                )}
                            </div>

                            {shareUrl && (
                                <div className="space-y-3">
                                    <p className="text-sm text-gray-600">
                                        Share this link with friends to send them your personalized meal plan:
                                    </p>
                                    <div className="flex items-center space-x-2">
                                        <input
                                            type="text"
                                            value={shareUrl}
                                            readOnly
                                            className="flex-1 px-4 py-2 bg-white border border-purple-200 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        />
                                        <button
                                            onClick={copyToClipboard}
                                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
                                                copied
                                                    ? 'bg-green-500 text-white'
                                                    : 'bg-purple-600 hover:bg-purple-700 text-white'
                                            }`}
                                        >
                                            {copied ? (
                                                <>
                                                    <CheckCircle className="w-4 h-4" />
                                                    <span>Copied!</span>
                                                </>
                                            ) : (
                                                <>
                                                    <Copy className="w-4 h-4" />
                                                    <span>Copy</span>
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                )}

                {/* Meal Plan Grid */}
                {mealPlan && mealTargets && targets && (
                    <>
                        {/* Daily Summary */}
                        {(() => {
                            const dailyTotals = calculateDailyTotals();
                            if (!dailyTotals) return null;
                            
                            // Determine what adjustments are needed
                            const calorieRatio = dailyTotals.calories / targets.calories;
                            const proteinRatio = dailyTotals.protein / targets.protein;
                            const carbsRatio = dailyTotals.carbs / targets.carbs;
                            const fatRatio = dailyTotals.fat / targets.fat;
                            
                            const needsAdjustment = 
                                calorieRatio < 0.85 || calorieRatio > 1.15 ||
                                proteinRatio < 0.85 || proteinRatio > 1.15 ||
                                carbsRatio < 0.85 || carbsRatio > 1.15 ||
                                fatRatio < 0.85 || fatRatio > 1.15;
                            
                            return (
                                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-2xl font-bold text-gray-900 flex items-center">
                                            <TrendingUp className="w-6 h-6 mr-2 text-primary-600" />
                                            Today's Nutrition Summary
                                        </h3>
                                        {needsAdjustment && (
                                            <div className="flex items-center text-sm text-amber-600 bg-amber-50 px-3 py-1 rounded-full border border-amber-200">
                                                <span className="mr-1">💡</span>
                                                <span className="font-medium">Regenerate meals to balance nutrients</span>
                                            </div>
                                        )}
                                    </div>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                                        {/* Calories */}
                                        <div className={`p-4 rounded-lg border-2 ${getStatusColor(dailyTotals.calories, targets.calories)}`}>
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="flex items-center">
                                                    <Flame className="w-5 h-5 mr-2" />
                                                    <span className="font-semibold">Calories</span>
                                                </div>
                                                <span className="text-xl">{getStatusIcon(dailyTotals.calories, targets.calories)}</span>
                                            </div>
                                            <div className="text-2xl font-bold">{Math.round(dailyTotals.calories)}</div>
                                            <div className="text-sm opacity-75">Target: {targets.calories}</div>
                                            <div className="text-xs mt-1 font-medium">
                                                {((dailyTotals.calories / targets.calories) * 100).toFixed(0)}% of target
                                            </div>
                                            {calorieRatio < 0.85 && (
                                                <div className="text-xs mt-2 opacity-90 italic">
                                                    Regenerate for heartier meals
                                                </div>
                                            )}
                                            {calorieRatio > 1.15 && (
                                                <div className="text-xs mt-2 opacity-90 italic">
                                                    Regenerate for lighter meals
                                                </div>
                                            )}
                                        </div>

                                        {/* Protein */}
                                        <div className={`p-4 rounded-lg border-2 ${getStatusColor(dailyTotals.protein, targets.protein)}`}>
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="flex items-center">
                                                    <TrendingUp className="w-5 h-5 mr-2" />
                                                    <span className="font-semibold">Protein</span>
                                                </div>
                                                <span className="text-xl">{getStatusIcon(dailyTotals.protein, targets.protein)}</span>
                                            </div>
                                            <div className="text-2xl font-bold">{Math.round(dailyTotals.protein)}g</div>
                                            <div className="text-sm opacity-75">Target: {targets.protein}g</div>
                                            <div className="text-xs mt-1 font-medium">
                                                {((dailyTotals.protein / targets.protein) * 100).toFixed(0)}% of target
                                            </div>
                                            {proteinRatio < 0.85 && (
                                                <div className="text-xs mt-2 opacity-90 italic">
                                                    Regenerate for high-protein options
                                                </div>
                                            )}
                                            {proteinRatio > 1.15 && (
                                                <div className="text-xs mt-2 opacity-90 italic">
                                                    Regenerate for lower-protein meals
                                                </div>
                                            )}
                                        </div>

                                        {/* Carbs */}
                                        <div className={`p-4 rounded-lg border-2 ${getStatusColor(dailyTotals.carbs, targets.carbs)}`}>
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="flex items-center">
                                                    <Utensils className="w-5 h-5 mr-2" />
                                                    <span className="font-semibold">Carbs</span>
                                                </div>
                                                <span className="text-xl">{getStatusIcon(dailyTotals.carbs, targets.carbs)}</span>
                                            </div>
                                            <div className="text-2xl font-bold">{Math.round(dailyTotals.carbs)}g</div>
                                            <div className="text-sm opacity-75">Target: {targets.carbs}g</div>
                                            <div className="text-xs mt-1 font-medium">
                                                {((dailyTotals.carbs / targets.carbs) * 100).toFixed(0)}% of target
                                            </div>
                                            {carbsRatio < 0.85 && (
                                                <div className="text-xs mt-2 opacity-90 italic">
                                                    Regenerate for more carb-rich meals
                                                </div>
                                            )}
                                            {carbsRatio > 1.15 && (
                                                <div className="text-xs mt-2 opacity-90 italic">
                                                    Regenerate for lower-carb options
                                                </div>
                                            )}
                                        </div>

                                        {/* Fat */}
                                        <div className={`p-4 rounded-lg border-2 ${getStatusColor(dailyTotals.fat, targets.fat)}`}>
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="flex items-center">
                                                    <Scale className="w-5 h-5 mr-2" />
                                                    <span className="font-semibold">Fat</span>
                                                </div>
                                                <span className="text-xl">{getStatusIcon(dailyTotals.fat, targets.fat)}</span>
                                            </div>
                                            <div className="text-2xl font-bold">{Math.round(dailyTotals.fat)}g</div>
                                            <div className="text-sm opacity-75">Target: {targets.fat}g</div>
                                            <div className="text-xs mt-1 font-medium">
                                                {((dailyTotals.fat / targets.fat) * 100).toFixed(0)}% of target
                                            </div>
                                            {fatRatio < 0.85 && (
                                                <div className="text-xs mt-2 opacity-90 italic">
                                                    Regenerate for meals with healthy fats
                                                </div>
                                            )}
                                            {fatRatio > 1.15 && (
                                                <div className="text-xs mt-2 opacity-90 italic">
                                                    Regenerate for lower-fat options
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            );
                        })()}

                        {/* Global Regenerate Button */}
                        <div className="mb-6 flex justify-center">
                            <button
                                onClick={regenerateAllMeals}
                                disabled={loading}
                                className="btn-primary px-6 py-3 text-base flex items-center space-x-2 shadow-lg hover:shadow-xl transition-all"
                            >
                                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                                <span>{loading ? 'Regenerating All Meals...' : 'Regenerate All Meals'}</span>
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {(['breakfast', 'lunch', 'dinner', 'snacks'] as MealType[]).map(mealType => {
                            const mealRecipes = mealPlan[mealType];
                            const mealNutrition = calculateMealNutrition(mealRecipes);
                            const mealTarget = mealTargets[mealType];
                            
                            return (
                                <div key={mealType} className="bg-white rounded-lg shadow-lg overflow-hidden">
                                    {/* Meal Header */}
                                    <div className="bg-gradient-to-r from-primary-600 to-orange-500 text-white p-4">
                                        <div className="flex items-center justify-between mb-3">
                                            <h3 className="text-xl font-bold flex items-center">
                                                {getMealIcon(mealType)}
                                                <span className="ml-2">{getMealTitle(mealType)}</span>
                                            </h3>
                                            <button
                                                onClick={() => regenerateMeal(mealType)}
                                                disabled={regeneratingMeal === mealType}
                                                className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors disabled:opacity-50"
                                                title="Regenerate this meal"
                                            >
                                                <RefreshCw className={`w-5 h-5 ${regeneratingMeal === mealType ? 'animate-spin' : ''}`} />
                                            </button>
                                        </div>
                                        
                                        {/* Nutrition Summary */}
                                        <div className="space-y-2 text-sm">
                                            <div className="flex justify-between items-center">
                                                <span className="flex items-center">
                                                    <Flame className="w-4 h-4 mr-1" />
                                                    Calories
                                                </span>
                                                <span className="font-bold">
                                                    {Math.round(mealNutrition.calories)} / {mealTarget.calories}
                                                </span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>Protein</span>
                                                <span className="font-semibold">
                                                    {Math.round(mealNutrition.protein)}g / {mealTarget.protein}g
                                                </span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>Carbs</span>
                                                <span className="font-semibold">
                                                    {Math.round(mealNutrition.carbs)}g / {mealTarget.carbs}g
                                                </span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>Fat</span>
                                                <span className="font-semibold">
                                                    {Math.round(mealNutrition.fat)}g / {mealTarget.fat}g
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Recipes */}
                                    <div className="p-4 space-y-4">
                                        {mealRecipes.length > 0 ? (
                                            mealRecipes.map(recipe => (
                                                <RecipeCard key={recipe.id} recipe={recipe} compact />
                                            ))
                                        ) : (
                                            <div className="text-center py-8 text-gray-500">
                                                <Utensils className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                                <p>No recipes found for this meal</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                    </>
                )}
            </div>
        </div>
    );
}

export default function MealPlannerPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gray-50 py-8 px-4 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading meal planner...</p>
                </div>
            </div>
        }>
            <MealPlannerContent />
        </Suspense>
    );
}
