export default function RecipeCardSkeleton() {
    return (
        <div className="recipe-card overflow-hidden">
            {/* Image Skeleton */}
            <div className="h-48 w-full bg-gray-200 shimmer"></div>

            {/* Content Skeleton */}
            <div className="p-4">
                {/* Title Skeleton */}
                <div className="h-6 bg-gray-200 rounded shimmer mb-2"></div>
                <div className="h-6 bg-gray-200 rounded shimmer w-3/4 mb-3"></div>

                {/* Description Skeleton */}
                <div className="h-4 bg-gray-100 rounded shimmer mb-1"></div>
                <div className="h-4 bg-gray-100 rounded shimmer w-5/6 mb-3"></div>

                {/* Meta Info Skeleton */}
                <div className="flex items-center justify-between mb-3">
                    <div className="flex space-x-4">
                        <div className="h-4 bg-gray-100 rounded shimmer w-16"></div>
                        <div className="h-4 bg-gray-100 rounded shimmer w-12"></div>
                    </div>
                    <div className="h-4 bg-gray-100 rounded shimmer w-10"></div>
                </div>

                {/* Tags Skeleton */}
                <div className="flex gap-1 mb-3">
                    <div className="h-5 bg-gray-100 rounded-full shimmer w-16"></div>
                    <div className="h-5 bg-gray-100 rounded-full shimmer w-12"></div>
                    <div className="h-5 bg-gray-100 rounded-full shimmer w-8"></div>
                </div>

                {/* Author Skeleton */}
                <div className="h-3 bg-gray-100 rounded shimmer w-20"></div>
            </div>
        </div>
    );
}

