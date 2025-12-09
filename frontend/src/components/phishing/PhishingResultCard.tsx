import { RiskBadge } from '../common/RiskBadge'
import './PhishingResultCard.css'

interface PhishingResultCardProps {
    result: {
        id: number
        risk_score: number
        risk_level: 'low' | 'medium' | 'high'
        explanation: string
        highlights: string[]
        created_at: string
    }
}

export function PhishingResultCard({ result }: PhishingResultCardProps) {
    return (
        <div className="result-card">
            <div className="result-header">
                <h2>Analysis Results</h2>
                <RiskBadge score={result.risk_score} level={result.risk_level} />
            </div>

            <div className="result-section">
                <h3>Explanation</h3>
                <p className="explanation">{result.explanation}</p>
            </div>

            {result.highlights && result.highlights.length > 0 && (
                <div className="result-section">
                    <h3>Key Findings</h3>
                    <ul className="highlights-list">
                        {result.highlights.map((highlight, index) => (
                            <li key={index}>{highlight}</li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="result-footer">
                <small>
                    Scan ID: {result.id} | Analyzed at:{' '}
                    {new Date(result.created_at).toLocaleString()}
                </small>
            </div>
        </div>
    )
}
