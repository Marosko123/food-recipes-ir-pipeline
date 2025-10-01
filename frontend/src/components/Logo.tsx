import Link from 'next/link';

interface LogoProps {
    className?: string;
    showText?: boolean;
    size?: 'sm' | 'md' | 'lg';
}

export default function Logo({
    className = '',
    showText = true,
    size = 'md'
}: LogoProps) {
    const sizeClasses = {
        sm: {
            container: 'w-8 h-8',
            icon: 'w-4 h-4',
            text: 'text-lg'
        },
        md: {
            container: 'w-10 h-10 sm:w-12 sm:h-12',
            icon: 'w-6 h-6 sm:w-7 sm:h-7',
            text: 'text-xl sm:text-2xl'
        },
        lg: {
            container: 'w-16 h-16',
            icon: 'w-10 h-10',
            text: 'text-3xl'
        }
    };

    const currentSize = sizeClasses[size];

    return (
        <Link href="/" className={`flex items-center space-x-2 sm:space-x-3 group hover:opacity-80 transition-all duration-200 hover:scale-105 ${className}`}>
            <div className={`${currentSize.container} bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg group-hover:shadow-2xl transition-all duration-200 group-hover:rotate-3`}>
                <svg className={`${currentSize.icon} text-white drop-shadow-sm`} fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                </svg>
            </div>

            {showText && (
                <h1 className={`${currentSize.text} font-bold bg-gradient-to-r from-orange-600 via-red-600 to-pink-600 bg-clip-text text-transparent group-hover:from-orange-500 group-hover:via-red-500 group-hover:to-pink-500 transition-all duration-200`}>
                    Food Recipes
                </h1>
            )}
        </Link>
    );
}
