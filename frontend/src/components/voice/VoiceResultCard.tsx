import { useState } from 'react'
import { VoiceAnalysisResponse } from '../../api/voiceApi'
import { RiskBadge } from '../common/RiskBadge'
import './VoiceResultCard.css'

interface VoiceResultCardProps {
    result: VoiceAnalysisResponse
}

export function VoiceResultCard({ result }: VoiceResultCardProps) {
    const [showTechnical, setShowTechnical] = useState(false)

    // Helper to determine status color for artifacts based on backend thresholds
    const getArtifactStatus = (key: string, value: number) => {
        switch (key) {
            case 'spectral_flatness': return value > 0.5 ? 'suspicious' : 'safe'
            case 'high_freq_energy': return value > 0.3 ? 'suspicious' : 'safe'
            case 'zcr_variance': return value < 0.01 ? 'suspicious' : 'safe'
            case 'autocorr_peak': return value > 500 ? 'suspicious' : 'safe'
            default: return 'neutral'
        }
    }

    const formatMetricName = (key: string) => {
        return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
    }

    return (
        <div className="voice-result-card">
            {/* Header Section */}
            <div className="result-header">
                <div className="header-content">
                    <h2>Analysis Report</h2>
                    <div className="file-meta">
                        <span className="meta-tag">📄 {result.file_name}</span>
                        <span className="meta-tag">⏱️ {result.duration.toFixed(1)}s</span>
                        <span className="meta-tag">🧠 {result.model_version}</span>
                    </div>
                </div>
                <RiskBadge
                    score={Math.round(result.confidence * 100)}
                    level={result.risk_level}
                />
            </div>

            {/* Audio Player Section */}
            {result.audio_url && (
                <div className="voice-section audio-player-section">
                    <div className="audio-wrapper">
                        <span className="audio-label">🔊 Recorded Audio</span>
                        <audio controls className="custom-audio-player">
                            <source src={result.audio_url} type="audio/wav" />
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                </div>
            )}

            {/* AI Explanation Section - Premium Dark Card */}
            {result.explanation && (
                <div className="voice-section">
                    <div className="ai-explanation-card">
                        <div className="ai-header">
                            <div className="ai-icon-wrapper">
                                <span className="ai-icon">🤖</span>
                            </div>
                            <div className="ai-title-content">
                                <h3>AI Security Assessment</h3>
                                <span className="ai-subtitle">Deepfake Detection Engine Analysis</span>
                            </div>
                        </div>
                        <p className="ai-text">{result.explanation}</p>
                    </div>
                </div>
            )}

            {/* Key Findings */}
            {result.highlights && result.highlights.length > 0 && (
                <div className="voice-section">
                    <h3>📌 Key Findings</h3>
                    <div className="highlights-grid">
                        {result.highlights.map((highlight, idx) => (
                            <div key={idx} className="highlight-card">
                                <div className="highlight-icon">⚠️</div>
                                <p className="highlight-text">{highlight}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Acoustic Artifacts - Professional Grid */}
            {result.artifacts && (
                <div className="voice-section">
                    <h3>🔬 Acoustic Artifact Analysis</h3>
                    <div className="artifacts-grid">
                        {Object.entries(result.artifacts).map(([key, value]) => {
                            const status = getArtifactStatus(key, value as number)
                            const isSuspicious = status === 'suspicious'
                            return (
                                <div key={key} className={`artifact-card status-${status}`}>
                                    <div className="artifact-header">
                                        <span className="artifact-label">{formatMetricName(key)}</span>
                                        <div className={`status-badge ${status}`}>
                                            {isSuspicious ? 'Anomaly' : 'Normal'}
                                        </div>
                                    </div>
                                    <div className="artifact-metric-group">
                                        <span className="artifact-value">{(value as number).toFixed(4)}</span>
                                        <span className="artifact-unit">score</span>
                                    </div>
                                    <div className="artifact-footer">
                                        <div className={`status-indicator ${status}`}></div>
                                        <span className="artifact-context">
                                            {isSuspicious
                                                ? 'Outside expected range'
                                                : 'Within normal parameters'}
                                        </span>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {/* Technical Details Toggle */}
            <div className="voice-section technical-section">
                <button
                    className="technical-toggle"
                    onClick={() => setShowTechnical(!showTechnical)}
                >
                    <span className="toggle-text">{showTechnical ? 'Hide Technical Details' : 'View Technical Details'}</span>
                    <span className={`toggle-arrow ${showTechnical ? 'open' : ''}`}>▼</span>
                </button>

                {showTechnical && (
                    <div className="technical-content">
                        <div className="tech-grid">
                            <div className="tech-item">
                                <label>File Hash (MD5)</label>
                                <code>{result.file_hash}</code>
                            </div>
                            <div className="tech-item">
                                <label>Raw Model Confidence</label>
                                <code>{result.raw_model_confidence?.toFixed(4) ?? 'N/A'}</code>
                            </div>
                            <div className="tech-item">
                                <label>Artifact Score</label>
                                <code>{result.artifact_score?.toFixed(4) ?? 'N/A'}</code>
                            </div>
                            <div className="tech-item">
                                <label>Processing Time</label>
                                <code>{result.processing_time.toFixed(3)}s</code>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
