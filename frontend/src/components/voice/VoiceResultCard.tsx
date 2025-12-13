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
    // Thresholds derived from backend/app/ml/deepfake_model.py
    const getArtifactStatus = (key: string, value: number) => {
        switch (key) {
            case 'spectral_flatness':
                // Higher flatness > 0.5 is suspicious (synthetic)
                return value > 0.5 ? 'suspicious' : 'safe'
            case 'high_freq_energy':
                // Higher energy > 0.3 is suspicious
                return value > 0.3 ? 'suspicious' : 'safe'
            case 'zcr_variance':
                // Lower variance < 0.01 is suspicious (too regular)
                return value < 0.01 ? 'suspicious' : 'safe'
            case 'autocorr_peak':
                // Higher peak > 500 is suspicious (periodicity)
                return value > 500 ? 'suspicious' : 'safe'
            default:
                return 'neutral'
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

            {/* AI Explanation Section */}
            {result.explanation && (
                <div className="ai-explanation-card">
                    <div className="ai-header">
                        <span className="ai-icon">🤖</span>
                        <h3>AI Security Assessment</h3>
                    </div>
                    <p className="ai-text">{result.explanation}</p>
                </div>
            )}

            {/* Highlights Section */}
            {result.highlights && result.highlights.length > 0 && (
                <div className="highlights-section">
                    <h3>📌 Key Findings</h3>
                    <ul className="highlights-list">
                        {result.highlights.map((highlight, idx) => (
                            <li key={idx} className="highlight-item">
                                {highlight}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Artifacts Grid */}
            {result.artifacts && (
                <div className="artifacts-section">
                    <h3>🔬 Acoustic Artifact Analysis</h3>
                    <div className="artifacts-grid">
                        {Object.entries(result.artifacts).map(([key, value]) => {
                            const status = getArtifactStatus(key, value as number)
                            return (
                                <div key={key} className={`artifact-card status-${status}`}>
                                    <div className="artifact-header">
                                        <span className="artifact-label">{formatMetricName(key)}</span>
                                        <span className={`status-dot ${status}`}></span>
                                    </div>
                                    <div className="artifact-value">
                                        {(value as number).toFixed(4)}
                                    </div>
                                    <div className="artifact-status-text">
                                        {status === 'suspicious' ? '⚠️ Anomaly Detected' : '✅ Within Normal Range'}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {/* Technical Details Toggle */}
            <div className="technical-section">
                <button 
                    className="technical-toggle"
                    onClick={() => setShowTechnical(!showTechnical)}
                >
                    {showTechnical ? 'Hide Technical Details' : 'Show Technical Details'}
                    <span className="toggle-icon">{showTechnical ? '▲' : '▼'}</span>
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
                            <div className="tech-item">
                                <label>Result Cached</label>
                                <code>{result.cached ? 'Yes' : 'No'}</code>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
