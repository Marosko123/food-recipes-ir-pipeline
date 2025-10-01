export interface Recipe {
  id: string;
  url: string;
  title: string;
  description: string;
  ingredients: string[];
  instructions: string[];
  times: {
    prep?: number;
    cook?: number;
    total?: number;
  };
  cuisine: string[];
  category: string[];
  tools: string[];
  yield: string;
  author: string;
  author_bio?: string;
  author_location?: string;
  author_stats?: Record<string, any>;
  keywords: string[];
  date_published?: string;
  image?: string;
  all_images: string[];
  difficulty?: string;
  serving_size?: string;
  nutrition?: {
    calories?: string;
    fat?: string;
    saturated_fat?: string;
    cholesterol?: string;
    sodium?: string;
    carbohydrates?: string;
    fiber?: string;
    sugar?: string;
    protein?: string;
  };
  ratings?: {
    rating?: string;
    review_count?: string;
  };
  score?: number;
}

export interface SearchFilters {
  // Time filters
  max_total_minutes?: number;
  max_prep_minutes?: number;
  max_cook_minutes?: number;
  min_total_minutes?: number;
  min_prep_minutes?: number;
  min_cook_minutes?: number;
  
  // Serving filters
  min_servings?: number;
  max_servings?: number;
  
  // Rating filters
  min_rating?: number;
  min_review_count?: number;
  
  // Category filters
  cuisine?: string[];
  category?: string[];
  difficulty?: string[];
  
  // New category filters
  meal_type?: string[];
  dietary?: string[];
  cooking_method?: string[];
  
  // Content filters
  ingredients?: string[];
  required_tools?: string[];
  keywords?: string[];
  
  // Author filters
  author?: string;
  author_location?: string;
  
  // Nutrition filters
  max_calories?: number;
  min_calories?: number;
  max_protein?: number;
  min_protein?: number;
  max_carbs?: number;
  min_carbs?: number;
  max_fat?: number;
  min_fat?: number;
  max_sodium?: number;
  min_sodium?: number;
  
  // Date filters
  date_from?: string;
  date_to?: string;
  
  // Image filter
  has_image?: boolean;
}

export interface SortOption {
  value: string;
  label: string;
  direction: 'asc' | 'desc';
}

export interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

export interface SearchResponse {
  results: Recipe[];
  recipes: Recipe[]; // Backend might use different field name
  total_results: number;
  page: number;
  per_page: number;
  total_pages: number;
  stats: {
    total_docs: number;
    total_terms: number;
    avg_doc_length: number;
  };
  query: string;
  metric: string;
  filters?: SearchFilters;
}

export interface ApiError {
  error: string;
}
