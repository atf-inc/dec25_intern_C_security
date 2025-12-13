import { useState, useEffect } from 'react'
import { AudioUpload } from '../components/voice/AudioUpload'
import { VoiceResultCard } from '../components/voice/VoiceResultCard'
import { VoiceStats } from '../components/voice/VoiceStats'
import { Loader } from '../components/common/Loader'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Toast, useToast } from '../components/common/Toast'
import { 
    analyzeVoice, 
    getVoiceStatistics, 
    VoiceAnalysisResponse, 
    VoiceStatistics as VoiceStatsType 
} from '../api/voiceApi'
import './VoicePage.css'

export function VoicePage() {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [result, setResult] = useState<VoiceAnalysisResponse | null>(null)
    
    // Stats State
    const [stats, setStats] = useState<VoiceStatsType | null>(null)
    const [refreshTrigger, setRefreshTrigger] = useState(0) // To trigger re-fetches of stats

    // Feedback
    const { toast, showToast, closeToast } = useToast()

    // Fetch Stats on Load and after analysis
    useEffect(() => {
        const fetchStats = async () => {
            try {
                const statsData = await getVoiceStatistics()
                setStats(statsData)
            } catch (err) {
                console.error("Failed to load statistics", err)
            }
        }
        fetchStats()
    }, [refreshTrigger])

    const handleAnalyze = async (file: File, useCache: boolean) => {
        setLoading(true)
        setError(null)
        setResult(null)

        try {
            const response = await analyzeVoice(file, true)
            setResult(response)
            showToast('Analysis complete!', 'success')
            setRefreshTrigger(prev => prev + 1) // Refresh stats
        } catch (err: any) {
            console.error('Analysis error:', err)
            const errorMsg = err.message || 'Analysis failed'
            setError(errorMsg)
            showToast(errorMsg, 'error')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="voice-page">
            {toast && (
                <Toast 
                    message={toast.message} 
                    type={toast.type} 
                    onClose={closeToast} 
                />
            )}

            <div className="page-header">
                <h1>🎙️ Voice Deepfake Detection</h1>
                <p>
                    Advanced AI-powered audio analysis to detect synthetic voices using
                    WavLM embeddings and spectral artifact detection.
                </p>
            </div>

            {/* Statistics Dashboard (Kept as it's useful context) */}
            <VoiceStats stats={stats} loading={!stats && loading} />

            {/* Main Analysis Section (Centered Single Column) */}
            <div className="analysis-container">
                <div className="upload-section-container">
                    <AudioUpload onAnalyze={handleAnalyze} loading={loading} />
                </div>

                {loading && (
                    <div className="loader-wrapper">
                        <Loader />
                        <p className="loading-text">Running deepfake detection models...</p>
                    </div>
                )}

                {error && (
                    <div className="error-container">
                        <ErrorAlert message={error} />
                    </div>
                )}

                {result && (
                    <div id="results-section">
                        <VoiceResultCard result={result} />
                    </div>
                )}
            </div>
        </div>
    )
}
