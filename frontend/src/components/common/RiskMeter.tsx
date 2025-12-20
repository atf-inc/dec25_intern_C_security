import React, { useEffect, useState } from 'react';
import './RiskMeter.css';

interface RiskMeterProps {
    score: number;
    size?: number;
    strokeWidth?: number;
    color?: string; // Optional override
}

export const RiskMeter: React.FC<RiskMeterProps> = ({
    score,
    size = 120,
    strokeWidth = 8,
    color
}) => {
    const [animatedScore, setAnimatedScore] = useState(0);
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;

    // Animate score on mount
    useEffect(() => {
        // Simple animation to target score
        const duration = 1000;
        const steps = 60;
        const interval = duration / steps;
        const increment = score / steps;
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= score) {
                setAnimatedScore(score);
                clearInterval(timer);
            } else {
                setAnimatedScore(Math.round(current));
            }
        }, interval);

        return () => clearInterval(timer);
    }, [score]);

    // Determine color based on score if not provided
    const getScoreColor = (value: number) => {
        if (value >= 80) return 'var(--danger-color)';
        if (value >= 50) return 'var(--warning-color)';
        return 'var(--success-color)';
    };

    const displayColor = color || getScoreColor(score);
    const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

    return (
        <div className="risk-meter-container" style={{ width: size, height: size }}>
            <svg
                className="risk-meter-svg"
                width={size}
                height={size}
                viewBox={`0 0 ${size} ${size}`}
            >
                {/* Background Circle */}
                <circle
                    className="risk-meter-bg"
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    strokeWidth={strokeWidth}
                />
                {/* Progress Circle */}
                <circle
                    className="risk-meter-progress"
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    strokeWidth={strokeWidth}
                    stroke={displayColor}
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    transform={`rotate(-90 ${size / 2} ${size / 2})`}
                />

                {/* Text */}
                <text
                    x="50%"
                    y="55%"
                    dominantBaseline="middle"
                    textAnchor="middle"
                    className="risk-meter-text"
                    fill="var(--text-primary)"
                >
                    {Math.round(animatedScore)}
                </text>
            </svg>
        </div>
    );
};
