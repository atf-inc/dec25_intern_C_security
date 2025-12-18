import { useState, useEffect } from 'react';
import './ThemeToggle.css';

interface ThemeToggleProps {
    className?: string;
}

export function ThemeToggle({ className = '' }: ThemeToggleProps) {
    const [isDark, setIsDark] = useState(false);
    const [isAnimating, setIsAnimating] = useState(false);

    useEffect(() => {
        // Check for saved theme preference or default to light mode
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            setIsDark(true);
            document.documentElement.classList.add('dark');
        }
    }, []);

    const toggleTheme = () => {
        setIsAnimating(true);

        // 🔒 Transition Lock: Prevent layout thrashing during toggle
        document.documentElement.classList.add('no-transition');

        const newTheme = !isDark;
        setIsDark(newTheme);

        if (newTheme) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }

        // 🔓 Unlock transitions immediately after state change
        // Force reflow to ensure the new state is applied without transition
        void document.documentElement.offsetHeight;

        setTimeout(() => {
            document.documentElement.classList.remove('no-transition');
            setIsAnimating(false);
        }, 0);
    };

    return (
        <button
            className={`theme-toggle ${isDark ? 'dark' : 'light'} ${isAnimating ? 'animating' : ''} ${className}`}
            onClick={toggleTheme}
            aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
            disabled={isAnimating}
        >
            <div className="theme-toggle-track">
                <div className="theme-toggle-thumb">
                    <div className="theme-icon sun-icon">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="5" />
                            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                        </svg>
                    </div>
                    <div className="theme-icon moon-icon">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                        </svg>
                    </div>
                </div>
            </div>
        </button>
    );
}