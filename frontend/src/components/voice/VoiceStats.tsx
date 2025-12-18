import { useTranslation } from 'react-i18next'
import { VoiceStatistics } from '../../api/voiceApi'
import './VoiceStats.css'

interface VoiceStatsProps {
    stats: VoiceStatistics | null
    loading: boolean
}

export function VoiceStats({ stats, loading }: VoiceStatsProps) {
    const { t } = useTranslation()

    // Fallback function for translations
    const getText = (key: string, fallback: string) => {
        const translated = t(key)
        return translated === key ? fallback : translated
    }

    if (loading) {
        return <div className="stats-skeleton">{getText('voice.loadingStats', 'Loading stats...')}</div>
    }

    if (!stats) return null

    return (
        <div className="voice-stats-container">
            <div className="stat-card total">
                <div className="stat-icon">📊</div>
                <div className="stat-info">
                    <h3>{getText('voice.totalScans', 'Total Scans')}</h3>
                    <div className="stat-value">{stats.total_scans}</div>
                </div>
            </div>

            <div className="stat-card deepfake">
                <div className="stat-icon">🎭</div>
                <div className="stat-info">
                    <h3>{getText('voice.deepfakesDetected', 'Deepfakes Detected')}</h3>
                    <div className="stat-value">{stats.deepfake_count}</div>
                    <small className="stat-sub">
                        {stats.deepfake_percentage.toFixed(1)}% {getText('voice.ofTotal', 'of total')}
                    </small>
                </div>
            </div>

            <div className="stat-card real">
                <div className="stat-icon">👤</div>
                <div className="stat-info">
                    <h3>{getText('voice.realVoices', 'Real Voices')}</h3>
                    <div className="stat-value">{stats.real_count}</div>
                </div>
            </div>

            <div className="stat-card risk">
                <div className="stat-icon">🛡️</div>
                <div className="stat-info">
                    <h3>{getText('voice.highRiskAlerts', 'High Risk Alerts')}</h3>
                    <div className="stat-value text-red">{stats.high_risk_count}</div>
                </div>
            </div>
        </div>
    )
}
