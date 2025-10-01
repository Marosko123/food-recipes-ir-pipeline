'use client';

interface SearchStatsProps {
    totalResults: number;
    searchTime?: number;
    currentPage: number;
    itemsPerPage: number;
    searchQuery?: string;
    metric?: string;
    activeFilters: number;
}

export default function SearchStats({
    totalResults,
    searchTime,
    currentPage,
    itemsPerPage,
    searchQuery,
    metric = 'bm25',
    activeFilters
}: SearchStatsProps) {
    const startItem = Math.min((currentPage - 1) * itemsPerPage + 1, totalResults);
    const endItem = Math.min(currentPage * itemsPerPage, totalResults);

    return (
        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
            {/* Results count */}
            <div className="flex items-center space-x-1">
                <span className="font-medium text-gray-900">
                    {totalResults.toLocaleString()}
                </span>
                <span>
                    recipe{totalResults !== 1 ? 's' : ''}
                </span>
                {totalResults > itemsPerPage && (
                    <span>
                        (showing {startItem}-{endItem})
                    </span>
                )}
            </div>

            {/* Search time */}
            {searchTime && (
                <div className="flex items-center space-x-1">
                    <span>•</span>
                    <span>{searchTime}ms</span>
                </div>
            )}

            {/* Search algorithm */}
            {searchQuery && (
                <div className="flex items-center space-x-1">
                    <span>•</span>
                    <span>Ranked by {metric.toUpperCase()}</span>
                </div>
            )}

            {/* Active filters */}
            {activeFilters > 0 && (
                <div className="flex items-center space-x-1">
                    <span>•</span>
                    <span>{activeFilters} filter{activeFilters !== 1 ? 's' : ''} active</span>
                </div>
            )}

            {/* Search query indicator */}
            {searchQuery && (
                <div className="flex items-center space-x-1">
                    <span>•</span>
                    <span>
                        Search: <span className="font-medium text-gray-900">"{searchQuery}"</span>
                    </span>
                </div>
            )}
        </div>
    );
}

