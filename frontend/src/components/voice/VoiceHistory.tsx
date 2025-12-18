import { VoiceAnalysisResponse } from '../../api/voiceApi'
import { RiskBadge } from '../common/RiskBadge'
import './VoiceHistory.css'

interface VoiceHistoryProps {
    history: VoiceAnalysisResponse[]
    onDelete: (id: number) => void
    onView: (scan: VoiceAnalysisResponse) => void
    loading: boolean
}

export function VoiceHistory({ history, onDelete, onView, loading }: VoiceHistoryProps) {
    if (loading) return <div className="history-loading">Loading history...</div>
    if (history.length === 0) return <div className="history-empty">No scan history available</div>

    return (
        <div className="voice-history-container">
            <h3 className="section-title">Recent Scans</h3>
            <div className="history-list">
                {history.map((scan) => (
                    <div key={scan.id} className="history-item">
                        <div className="history-main" onClick={() => onView(scan)}>
                            <div className="history-icon">
                                {scan.is_deepfake ? '🤖' : '👤'}
                            </div>
                            <div className="history-details">
                                <div className="history-name">{scan.file_name}</div>
                                <div className="history-meta">
                                    <span>{new Date(scan.created_at || '').toLocaleDateString()}</span>
                                    <span>•</span>
                                    <span>{scan.duration.toFixed(1)}s</span>
                                </div>
                            </div>
                        </div>

                        <div className="history-actions">
                            <div className="history-badge">
                                <RiskBadge
                                    score={Math.round(scan.confidence * 100)}
                                    level={scan.risk_level}
                                    size="small"
                                />
                            </div>
                            <button
                                className="delete-btn"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    if (scan.id) onDelete(scan.id)
                                }}
                                title="Delete scan"
                            >
                                🗑️
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
