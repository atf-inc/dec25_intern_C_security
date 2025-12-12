import { VoiceStatistics } from '../../api/voiceApi'
import './VoiceStats.css'

interface VoiceStatsProps {
    stats: VoiceStatistics | null
    loading: boolean
}

export function VoiceStats({ stats, loading }: VoiceStatsProps) {
    if (loading) {
        return <div className="stats-skeleton">Loading stats...</div>
    }

    if (!stats) return null

    return (
        <div className="voice-stats-container">
            <div className="stat-card total">
                <div className="stat-icon">📊</div>
                <div className="stat-info">
                    <h3>Total Scans</h3>
                    <div className="stat-value">{stats.total_scans}</div>
                </div>
            </div>

            <div className="stat-card deepfake">
                <div className="stat-icon">🎭</div>
                <div className="stat-info">
                    <h3>Deepfakes Detected</h3>
                    <div className="stat-value">{stats.deepfake_count}</div>
                    <small className="stat-sub">
                        {stats.deepfake_percentage.toFixed(1)}% of total
                    </small>
                </div>
            </div>

            <div className="stat-card real">
                <div className="stat-icon">👤</div>
                <div className="stat-info">
                    <h3>Real Voices</h3>
                    <div className="stat-value">{stats.real_count}</div>
                </div>
            </div>

            <div className="stat-card risk">
                <div className="stat-icon">🛡️</div>
                <div className="stat-info">
                    <h3>High Risk Alerts</h3>
                    <div className="stat-value text-red">{stats.high_risk_count}</div>
                </div>
            </div>
        </div>
    )
}
