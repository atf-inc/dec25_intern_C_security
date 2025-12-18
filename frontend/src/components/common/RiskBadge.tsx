import './RiskBadge.css'

interface RiskBadgeProps {
    score: number
    level: 'low' | 'medium' | 'high'
    size?: 'normal' | 'small'
}

export function RiskBadge({ score, level, size = 'normal' }: RiskBadgeProps) {
    const normalizedLevel = level.toLowerCase() as 'low' | 'medium' | 'high'

    const getIcon = (lvl: string) => {
        switch (lvl) {
            case 'high': return '🚨'
            case 'medium': return '⚠️'
            case 'low': return '✅'
            default: return '🛡️'
        }
    }

    return (
        <div className={`risk-badge risk-badge-${normalizedLevel} ${size === 'small' ? 'risk-badge-small' : ''}`}>
            {size !== 'small' && <span className="risk-icon">{getIcon(normalizedLevel)}</span>}
            <span className="risk-level">
                {size === 'small' && <span className="risk-icon-small">{getIcon(normalizedLevel)}</span>}
                {level.toUpperCase()}
            </span>
            <span className="risk-score">({score})</span>
        </div>
    )
}
