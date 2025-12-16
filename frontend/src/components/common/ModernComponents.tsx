// Export all modern animated components for easy importing
export { SkeletonLoader, SkeletonCard, SkeletonResultCard } from './SkeletonLoader';
export { ProgressIndicator, SuccessAnimation, ErrorAnimation, AnalysisProgress } from './ProgressIndicator';
export { AnimatedUploadZone } from './AnimatedUploadZone';
export { ThemeToggle } from './ThemeToggle';

// Modern Button Component with animations
import React from 'react';

interface ModernButtonProps {
    children: React.ReactNode;
    variant?: 'primary' | 'secondary' | 'success' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    loading?: boolean;
    disabled?: boolean;
    onClick?: () => void;
    className?: string;
}

export function ModernButton({
    children,
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    onClick,
    className = ''
}: ModernButtonProps) {
    return (
        <button
            className={`modern-btn modern-btn-${variant} modern-btn-${size} ${loading ? 'loading' : ''} ${className}`}
            onClick={onClick}
            disabled={disabled || loading}
            style={{
                background: variant === 'primary' ? 'var(--gradient-primary)' :
                    variant === 'success' ? 'var(--gradient-safe)' :
                        variant === 'danger' ? 'var(--gradient-phishing)' : 'var(--color-slate-200)',
                color: variant === 'secondary' ? 'var(--color-slate-700)' : 'white',
                border: 'none',
                borderRadius: 'var(--radius-lg)',
                padding: size === 'sm' ? 'var(--space-2) var(--space-4)' :
                    size === 'lg' ? 'var(--space-4) var(--space-8)' : 'var(--space-3) var(--space-6)',
                fontSize: size === 'sm' ? 'var(--text-sm)' :
                    size === 'lg' ? 'var(--text-lg)' : 'var(--text-base)',
                fontWeight: 'var(--font-semibold)',
                cursor: disabled ? 'not-allowed' : 'pointer',
                transition: 'all var(--anim-duration-normal) var(--anim-ease)',
                boxShadow: 'var(--shadow-sm)',
                position: 'relative',
                overflow: 'hidden'
            }}
            onMouseEnter={(e) => {
                if (!disabled && !loading) {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
                }
            }}
            onMouseLeave={(e) => {
                if (!disabled && !loading) {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                }
            }}
        >
            {loading && (
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: '16px',
                    height: '16px',
                    border: '2px solid rgba(255,255,255,0.3)',
                    borderTop: '2px solid white',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                }} />
            )}
            <span style={{ opacity: loading ? 0 : 1 }}>
                {children}
            </span>
        </button>
    );
}

// Modern Card Component
interface ModernCardProps {
    children: React.ReactNode;
    variant?: 'default' | 'glass' | 'elevated';
    hover?: boolean;
    className?: string;
}

export function ModernCard({
    children,
    variant = 'default',
    hover = true,
    className = ''
}: ModernCardProps) {
    const getCardStyles = () => {
        const baseStyles = {
            borderRadius: 'var(--radius-xl)',
            padding: 'var(--space-6)',
            transition: 'all var(--anim-duration-normal) var(--anim-ease)',
            border: '1px solid var(--color-slate-200)'
        };

        switch (variant) {
            case 'glass':
                return {
                    ...baseStyles,
                    background: 'var(--glass-bg-light)',
                    backdropFilter: 'var(--glass-blur)',
                    border: '1px solid var(--glass-border)'
                };
            case 'elevated':
                return {
                    ...baseStyles,
                    background: 'white',
                    boxShadow: 'var(--shadow-lg)'
                };
            default:
                return {
                    ...baseStyles,
                    background: 'white',
                    boxShadow: 'var(--shadow-md)'
                };
        }
    };

    return (
        <div
            className={`modern-card ${className}`}
            style={getCardStyles()}
            onMouseEnter={(e) => {
                if (hover) {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                    e.currentTarget.style.boxShadow = 'var(--shadow-xl)';
                }
            }}
            onMouseLeave={(e) => {
                if (hover) {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = variant === 'elevated' ? 'var(--shadow-lg)' : 'var(--shadow-md)';
                }
            }}
        >
            {children}
        </div>
    );
}