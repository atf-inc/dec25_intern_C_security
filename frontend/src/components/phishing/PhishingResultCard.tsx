import { RiskBadge } from '../common/RiskBadge'
import './PhishingResultCard.css'

interface PhishingResultCardProps {
    result: {
        request_id: string
        label: string
        score: number
        reasons: string[]
        suggested_action?: string
        model_meta?: {
            model: string
            heuristic_score?: number
            ai_used?: boolean
            cost_estimate?: number
            analysis_stages?: Array<{
                stage: string
                score?: number
                cost: number
                status: string
                reason?: string
            }>
        }
    }
}

export function PhishingResultCard({ result }: PhishingResultCardProps) {
    return (
        <div className="result-card">
            <div className="result-header">
                <h2>Analysis Results</h2>
                <RiskBadge score={result.score} level={result.label as 'low' | 'medium' | 'high'} />
            </div>

            {result.suggested_action && (
                <div className="result-section">
                    <h3>Recommended Action</h3>
                    <p className="suggested-action">{result.suggested_action}</p>
                </div>
            )}

            {result.reasons && result.reasons.length > 0 && (
                <div className="result-section">
                    <h3>Analysis Details</h3>
                    <ul className="highlights-list">
                        {result.reasons.map((reason, index) => (
                            <li key={index}>{reason}</li>
                        ))}
                    </ul>
                </div>
            )}

            {result.model_meta && (
                <div className="result-section">
                    <h3>Analysis Details</h3>
                    <div className="analysis-meta">
                        <div className="meta-item">
                            <span className="meta-label">Model:</span>
                            <span className="meta-value">{result.model_meta.model}</span>
                        </div>
                        {result.model_meta.heuristic_score && (
                            <div className="meta-item">
                                <span className="meta-label">Heuristic Score:</span>
                                <span className="meta-value">{result.model_meta.heuristic_score}/100</span>
                            </div>
                        )}
                        <div className="meta-item">
                            <span className="meta-label">AI Analysis:</span>
                            <span className={`meta-value ${result.model_meta.ai_used ? 'ai-used' : 'ai-skipped'}`}>
                                {result.model_meta.ai_used ? '🤖 Used' : '⚡ Skipped (heuristic sufficient)'}
                            </span>
                        </div>
                        {result.model_meta.cost_estimate !== undefined && (
                            <div className="meta-item">
                                <span className="meta-label">Cost:</span>
                                <span className="meta-value">${result.model_meta.cost_estimate.toFixed(3)}</span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="result-footer">
                <small>
                    Scan ID: {result.request_id} | Risk Score: {result.score}/100
                </small>
            </div>
        </div>
    )
}
