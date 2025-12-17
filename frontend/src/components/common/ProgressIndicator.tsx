import { useEffect, useState } from 'react';
import './ProgressIndicator.css';

interface ProgressIndicatorProps {
    variant?: 'linear' | 'circular' | 'pulse' | 'scanning';
    progress?: number; // 0-100
    size?: 'sm' | 'md' | 'lg';
    color?: 'primary' | 'success' | 'warning' | 'danger';
    animated?: boolean;
    showPercentage?: boolean;
    className?: string;
}

export function ProgressIndicator({
    variant = 'linear',
    progress = 0,
    size = 'md',
    color = 'primary',
    animated = true,
    showPercentage = false,
    className = ''
}: ProgressIndicatorProps) {
    const [displayProgress, setDisplayProgress] = useState(0);

    useEffect(() => {
        if (animated) {
            const timer = setTimeout(() => {
                setDisplayProgress(progress);
            }, 100);
            return () => clearTimeout(timer);
        } else {
            setDisplayProgress(progress);
        }
    }, [progress, animated]);

    if (variant === 'circular') {
        return (
            <div className={`progress-circular progress-${size} progress-${color} ${className}`}>
                <svg className="progress-circular-svg" viewBox="0 0 36 36">
                    <path
                        className="progress-circular-bg"
                        d="M18 2.0845
              a 15.9155 15.9155 0 0 1 0 31.831
              a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                        className="progress-circular-fill"
                        strokeDasharray={`${displayProgress}, 100`}
                        d="M18 2.0845
              a 15.9155 15.9155 0 0 1 0 31.831
              a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                </svg>
                {showPercentage && (
                    <div className="progress-circular-text">
                        {Math.round(displayProgress)}%
                    </div>
                )}
            </div>
        );
    }

    if (variant === 'pulse') {
        return (
            <div className={`progress-pulse progress-${size} progress-${color} ${className}`}>
                <div className="progress-pulse-dot" />
                <div className="progress-pulse-dot" />
                <div className="progress-pulse-dot" />
            </div>
        );
    }

    if (variant === 'scanning') {
        return (
            <div className={`progress-scanning progress-${size} progress-${color} ${className}`}>
                <div className="progress-scanning-line" />
            </div>
        );
    }

    // Linear progress (default)
    return (
        <div className={`progress-linear progress-${size} progress-${color} ${className}`}>
            <div className="progress-linear-bg">
                <div
                    className="progress-linear-fill"
                    style={{ width: `${displayProgress}%` }}
                />
                {animated && (
                    <div className="progress-linear-shimmer" />
                )}
            </div>
            {showPercentage && (
                <span className="progress-linear-text">
                    {Math.round(displayProgress)}%
                </span>
            )}
        </div>
    );
}

// Success/Error Animation Components
export function SuccessAnimation({ size = 'md', className = '' }: { size?: 'sm' | 'md' | 'lg', className?: string }) {
    return (
        <div className={`success-animation success-${size} ${className}`}>
            <svg className="success-svg" viewBox="0 0 52 52">
                <circle className="success-circle" cx="26" cy="26" r="25" fill="none" />
                <path className="success-check" fill="none" d="m14.1 27.2l7.1 7.2 16.7-16.8" />
            </svg>
        </div>
    );
}

export function ErrorAnimation({ size = 'md', className = '' }: { size?: 'sm' | 'md' | 'lg', className?: string }) {
    return (
        <div className={`error-animation error-${size} ${className}`}>
            <svg className="error-svg" viewBox="0 0 52 52">
                <circle className="error-circle" cx="26" cy="26" r="25" fill="none" />
                <path className="error-cross" fill="none" d="m16 16 20 20 m0-20-20 20" />
            </svg>
        </div>
    );
}

// Analysis Progress Component
export function AnalysisProgress({
    stage = 'analyzing',
    className = ''
}: {
    stage?: 'analyzing' | 'processing' | 'complete' | 'error',
    className?: string
}) {
    const getStageText = () => {
        switch (stage) {
            case 'analyzing': return 'Analyzing email for threats...';
            case 'processing': return 'Processing security indicators...';
            case 'complete': return 'Analysis complete!';
            case 'error': return 'Analysis failed';
            default: return 'Processing...';
        }
    };

    const getStageIcon = () => {
        switch (stage) {
            case 'complete': return <SuccessAnimation size="sm" />;
            case 'error': return <ErrorAnimation size="sm" />;
            default: return <ProgressIndicator variant="pulse" color="primary" size="sm" />;
        }
    };

    return (
        <div className={`analysis-progress ${className}`}>
            <div className="analysis-progress-icon">
                {getStageIcon()}
            </div>
            <div className="analysis-progress-text">
                {getStageText()}
            </div>
        </div>
    );
}