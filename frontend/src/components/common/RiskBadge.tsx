import './RiskBadge.css'

export interface RiskBadgeProps {
    score?: number
    level: 'safe' | 'low' | 'medium' | 'high' | 'critical'
    size?: 'normal' | 'small'
    showIcon?: boolean // New explicit prop
}

export function RiskBadge({ score, level, size = 'normal', showIcon = true }: RiskBadgeProps) {
    const normalizedLevel = level.toLowerCase() as 'safe' | 'low' | 'medium' | 'high' | 'critical'

    // 🛡️ Shape-coded icons for accessibility
    const getIcon = (lvl: string) => {
        switch (lvl) {
            case 'critical': return '🛑'
            case 'high': return '✕' // Cross for High
            case 'medium': return '⚠️'
            case 'low': return '✓'  // Check for Low/Safe
            case 'safe': return '✓'
            default: return '🛡️'
        }
    }

    return (
        <div
            className={`risk-badge risk-badge-${normalizedLevel} ${size === 'small' ? 'risk-badge-small' : ''}`}
            role="status"
            aria-label={`Risk level: ${level}${score ? `, Score: ${score}` : ''}`}
        >
            {showIcon && size !== 'small' && <span className="risk-icon" aria-hidden="true">{getIcon(normalizedLevel)}</span>}

            <span className="risk-level">
                {showIcon && size === 'small' && <span className="risk-icon-small" aria-hidden="true">{getIcon(normalizedLevel)}</span>}
                {level.toUpperCase()}
            </span>

            {score !== undefined && <span className="risk-score">({score})</span>}
        </div>
    )
}
