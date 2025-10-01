import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Logo from '@/components/Logo';
import Navigation from '@/components/Navigation';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'Food Recipes - Discover Amazing Recipes',
    description: 'Discover and explore thousands of delicious recipes with detailed instructions, ingredients, and nutritional information. Your ultimate recipe search engine powered by AI.',
    keywords: ['recipes', 'cooking', 'food', 'ingredients', 'nutrition', 'chef', 'cuisine', 'search'],
    authors: [{ name: 'Maroš Bednár' }],
    openGraph: {
        title: 'Food Recipes - Discover Amazing Recipes',
        description: 'Discover and explore thousands of delicious recipes with detailed instructions, ingredients, and nutritional information. Your ultimate recipe search engine powered by AI.',
        type: 'website',
        locale: 'en_US',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'Food Recipes - Discover Amazing Recipes',
        description: 'Discover and explore thousands of delicious recipes with detailed instructions, ingredients, and nutritional information. Your ultimate recipe search engine powered by AI.',
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="scroll-smooth" data-scroll-behavior="smooth">
            <head>
                <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><text y='18' font-size='20'>🍳</text></svg>" />
            </head>
            <body className={`${inter.className} antialiased`}>
                <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
                    <Navigation />
                    <main className="flex-1">
                        {children}
                    </main>
                    <footer className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 text-white">
                        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                <div>
                                    <div className="flex items-center space-x-3 mb-4">
                                        <Logo size="sm" showText={false} />
                                        <h3 className="text-lg font-semibold">Food Recipes</h3>
                                    </div>
                                    <p className="text-gray-300 text-sm">
                                        Discover thousands of amazing recipes with detailed instructions,
                                        ingredients, and nutritional information. Your ultimate recipe search engine powered by AI.
                                    </p>
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold mb-4">🔍 Features</h3>
                                    <ul className="space-y-2 text-gray-300">
                                        <li>🔍 Advanced Recipe Search</li>
                                        <li>📊 Detailed Nutritional Info</li>
                                        <li>👨‍🍳 Cooking Instructions</li>
                                        <li>🥘 Ingredient Lists</li>
                                    </ul>
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold mb-4">👨‍💻 About</h3>
                                    <p className="text-gray-300">
                                        Built with Next.js and powered by a robust recipe search engine.
                                        <br />Part of a school project for Information Retrieval.
                                        <br /><span className="text-orange-400 font-medium">Maroš Bednár</span> | AIS ID: 116822
                                    </p>
                                </div>
                            </div>
                            <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-400">
                                <p>&copy; 2024 🍳 Food Recipes. Built for educational purposes. | Powered by AI & Machine Learning</p>
                            </div>
                        </div>
                    </footer>
                </div>
            </body>
        </html>
    );
}
