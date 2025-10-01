'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, X, Search } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface MultiSelectOption {
    value: string;
    label: string;
    count?: number;
}

interface MultiSelectProps {
    options: MultiSelectOption[];
    selected: string[];
    onSelectionChange: (selected: string[]) => void;
    placeholder?: string;
    searchable?: boolean;
    maxDisplay?: number;
    className?: string;
}

export default function MultiSelect({
    options,
    selected,
    onSelectionChange,
    placeholder = "Select options...",
    searchable = false,
    maxDisplay = 3,
    className = ""
}: MultiSelectProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const containerRef = useRef<HTMLDivElement>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Focus search input when dropdown opens
    useEffect(() => {
        if (isOpen && searchable && searchInputRef.current) {
            searchInputRef.current.focus();
        }
    }, [isOpen, searchable]);

    // Filter options based on search term
    const filteredOptions = options.filter(option =>
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleToggleOption = (value: string) => {
        const newSelected = selected.includes(value)
            ? selected.filter(item => item !== value)
            : [...selected, value];

        onSelectionChange(newSelected);
    };

    const handleRemoveOption = (value: string, event: React.MouseEvent) => {
        event.stopPropagation();
        onSelectionChange(selected.filter(item => item !== value));
    };

    const getDisplayText = () => {
        if (selected.length === 0) {
            return placeholder;
        }

        if (selected.length <= maxDisplay) {
            return selected.map(value => {
                const option = options.find(opt => opt.value === value);
                return option?.label || value;
            }).join(', ');
        }

        const displayItems = selected.slice(0, maxDisplay).map(value => {
            const option = options.find(opt => opt.value === value);
            return option?.label || value;
        });

        return `${displayItems.join(', ')} +${selected.length - maxDisplay} more`;
    };

    const selectedOptions = selected.map(value => options.find(opt => opt.value === value)).filter(Boolean);

    return (
        <div ref={containerRef} className={cn("relative", className)}>
            {/* Main Button */}
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className={cn(
                    "w-full input-field text-left flex items-center justify-between",
                    selected.length > 0 ? "text-gray-900" : "text-gray-500"
                )}
            >
                <span className="truncate">{getDisplayText()}</span>
                <ChevronDown
                    className={cn(
                        "w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ml-2",
                        isOpen && "transform rotate-180"
                    )}
                />
            </button>

            {/* Selected Items Display (when collapsed) */}
            {selected.length > 0 && !isOpen && (
                <div className="flex flex-wrap gap-1 mt-2">
                    {selectedOptions.slice(0, maxDisplay).map((option) => (
                        <span
                            key={option!.value}
                            className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-primary-100 text-primary-800"
                        >
                            {option!.label}
                            <button
                                onClick={(e) => handleRemoveOption(option!.value, e)}
                                className="ml-1 hover:text-primary-600"
                            >
                                <X className="w-3 h-3" />
                            </button>
                        </span>
                    ))}
                    {selected.length > maxDisplay && (
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-gray-100 text-gray-600">
                            +{selected.length - maxDisplay} more
                        </span>
                    )}
                </div>
            )}

            {/* Dropdown */}
            {isOpen && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-96 overflow-hidden">
                    {/* Search Input */}
                    {searchable && (
                        <div className="p-2 border-b border-gray-200">
                            <div className="relative">
                                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                                <input
                                    ref={searchInputRef}
                                    type="text"
                                    placeholder="Search options..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                                />
                            </div>
                        </div>
                    )}

                    {/* Options List */}
                    <div className="max-h-80 overflow-y-auto">
                        {filteredOptions.length === 0 ? (
                            <div className="p-3 text-sm text-gray-500 text-center">
                                {searchTerm ? 'No options found' : 'No options available'}
                            </div>
                        ) : (
                            filteredOptions.map((option) => {
                                const isSelected = selected.includes(option.value);
                                return (
                                    <button
                                        key={option.value}
                                        type="button"
                                        onClick={() => handleToggleOption(option.value)}
                                        className={cn(
                                            "w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center justify-between",
                                            isSelected && "bg-primary-50 text-primary-700"
                                        )}
                                    >
                                        <div className="flex items-center">
                                            <input
                                                type="checkbox"
                                                checked={isSelected}
                                                onChange={() => { }} // Handled by parent onClick
                                                className="mr-2"
                                            />
                                            <span>{option.label}</span>
                                        </div>
                                        {option.count !== undefined && (
                                            <span className="text-xs text-gray-500 ml-2">
                                                ({option.count})
                                            </span>
                                        )}
                                    </button>
                                );
                            })
                        )}
                    </div>

                    {/* Selected Count Footer */}
                    {selected.length > 0 && (
                        <div className="p-2 border-t border-gray-200 bg-gray-50">
                            <div className="flex items-center justify-between text-xs text-gray-600">
                                <span>{selected.length} selected</span>
                                <button
                                    type="button"
                                    onClick={() => onSelectionChange([])}
                                    className="text-primary-600 hover:text-primary-700 font-medium"
                                >
                                    Clear all
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}