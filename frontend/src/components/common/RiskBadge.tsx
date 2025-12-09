import './RiskBadge.css'

interface RiskBadgeProps {
    score: number
    level: 'low' | 'medium' | 'high'
}

export function RiskBadge({ score, level }: RiskBadgeProps) {
    return (
        <div className={`risk-badge risk-badge-${level}`}>
            <span className="risk-score">{score}</span>
            <span className="risk-level">{level.toUpperCase()}</span>
        </div>
    )
}
