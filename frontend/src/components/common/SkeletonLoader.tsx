import './SkeletonLoader.css';

interface SkeletonLoaderProps {
    variant?: 'card' | 'text' | 'circle' | 'rectangle';
    width?: string | number;
    height?: string | number;
    className?: string;
    count?: number;
}

export function SkeletonLoader({
    variant = 'rectangle',
    width,
    height,
    className = '',
    count = 1
}: SkeletonLoaderProps) {
    const skeletons = Array.from({ length: count }, (_, index) => (
        <div
            key={index}
            className={`skeleton skeleton-${variant} ${className}`}
            style={{
                width: width || (variant === 'circle' ? '40px' : '100%'),
                height: height || (variant === 'text' ? '1rem' : variant === 'circle' ? '40px' : '20px')
            }}
        />
    ));

    return count === 1 ? skeletons[0] : <div className="skeleton-group">{skeletons}</div>;
}

// Specific skeleton components for common use cases
export function SkeletonCard() {
    return (
        <div className="skeleton-card-container">
            <div className="skeleton-card-header">
                <SkeletonLoader variant="circle" width="48px" height="48px" />
                <div className="skeleton-card-title">
                    <SkeletonLoader variant="text" width="60%" height="1.2rem" />
                    <SkeletonLoader variant="text" width="40%" height="0.9rem" />
                </div>
            </div>
            <div className="skeleton-card-content">
                <SkeletonLoader variant="text" count={3} />
                <SkeletonLoader variant="rectangle" height="100px" />
            </div>
        </div>
    );
}

export function SkeletonResultCard() {
    return (
        <div className="skeleton-result-card">
            {/* Header */}
            <div className="skeleton-result-header">
                <SkeletonLoader variant="text" width="200px" height="1.5rem" />
                <SkeletonLoader variant="rectangle" width="80px" height="32px" />
            </div>

            {/* Summary Grid */}
            <div className="skeleton-summary-grid">
                {Array.from({ length: 4 }, (_, i) => (
                    <div key={i} className="skeleton-summary-item">
                        <SkeletonLoader variant="text" width="60px" height="0.75rem" />
                        <SkeletonLoader variant="text" width="40px" height="1rem" />
                    </div>
                ))}
            </div>

            {/* AI Explanation */}
            <div className="skeleton-ai-section">
                <SkeletonLoader variant="text" width="180px" height="1.2rem" />
                <div className="skeleton-cards-grid">
                    {Array.from({ length: 6 }, (_, i) => (
                        <div key={i} className="skeleton-evidence-card">
                            <div className="skeleton-card-header">
                                <SkeletonLoader variant="circle" width="8px" height="8px" />
                                <SkeletonLoader variant="text" width="120px" height="0.875rem" />
                            </div>
                            <SkeletonLoader variant="text" count={2} />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export function SkeletonVoiceCard() {
    return (
        <div className="skeleton-result-card">
            {/* Header */}
            <div className="skeleton-result-header">
                <SkeletonLoader variant="text" width="150px" height="1.5rem" />
                <SkeletonLoader variant="rectangle" width="100px" height="40px" />
            </div>

            {/* File Meta */}
            <div className="skeleton-file-meta">
                <SkeletonLoader variant="text" width="120px" height="0.875rem" />
                <SkeletonLoader variant="text" width="80px" height="0.875rem" />
                <SkeletonLoader variant="text" width="100px" height="0.875rem" />
            </div>

            {/* Audio Player */}
            <div className="skeleton-audio-section">
                <SkeletonLoader variant="text" width="140px" height="1rem" />
                <SkeletonLoader variant="rectangle" width="100%" height="40px" />
            </div>

            {/* AI Explanation */}
            <div className="skeleton-ai-section">
                <SkeletonLoader variant="text" width="200px" height="1.2rem" />
                <div className="skeleton-ai-card">
                    <SkeletonLoader variant="text" count={3} />
                </div>
            </div>

            {/* Artifacts Grid */}
            <div className="skeleton-artifacts-section">
                <SkeletonLoader variant="text" width="220px" height="1.2rem" />
                <div className="skeleton-artifacts-grid">
                    {Array.from({ length: 4 }, (_, i) => (
                        <div key={i} className="skeleton-artifact-card">
                            <div className="skeleton-card-header">
                                <SkeletonLoader variant="text" width="100px" height="0.875rem" />
                                <SkeletonLoader variant="rectangle" width="60px" height="20px" />
                            </div>
                            <SkeletonLoader variant="text" width="80px" height="1.5rem" />
                            <SkeletonLoader variant="text" width="120px" height="0.75rem" />
                        </div>
                    ))}
                </div>
            </div>

            {/* Technical Details */}
            <div className="skeleton-technical-section">
                <SkeletonLoader variant="text" width="180px" height="1rem" />
            </div>
        </div>
    );
}