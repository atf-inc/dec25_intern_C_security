import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { AudioUpload } from '../components/voice/AudioUpload'
import { VoiceResultCard } from '../components/voice/VoiceResultCard'
import { VoiceStats } from '../components/voice/VoiceStats'

import { ForensicScanner } from '../components/common/ForensicScanner'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { useToast } from '../components/common/ToastContext'
import {
    analyzeVoice,
    getVoiceStatistics,
    VoiceAnalysisResponse,
    VoiceStatistics as VoiceStatsType
} from '../api/voiceApi'
import './VoicePage.css'

export function VoicePage() {
    const { t } = useTranslation()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [result, setResult] = useState<VoiceAnalysisResponse | null>(null)

    // Stats State
    const [stats, setStats] = useState<VoiceStatsType | null>(null)
    const [refreshTrigger, setRefreshTrigger] = useState(0) // To trigger re-fetches of stats

    // Feedback
    const { showToast } = useToast()

    // Fallback function for translations
    const getText = (key: string, fallback: string) => {
        const translated = t(key)
        return translated === key ? fallback : translated
    }

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

    // Handle History View (Load specific scan from URL param)
    const [searchParams] = useSearchParams()

    useEffect(() => {
        const id = searchParams.get('id')
        if (id) {
            loadScan(Number(id))
        }
    }, [searchParams])

    const loadScan = async (id: number) => {
        setLoading(true)
        try {
            // Dynamically import to avoid circular dependencies if any, or just use the API
            const { getVoiceScan } = await import('../api/voiceApi')
            const data = await getVoiceScan(id)
            setResult(data)
            // Optional: Scroll to results
            setTimeout(() => {
                document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth' })
            }, 500)
        } catch (err: any) {
            console.error("Failed to load historical scan:", err)
            setError(getText('voice.scanLoadError', 'Could not load the requested scan. It may have been deleted.'))
        } finally {
            setLoading(false)
        }
    }

    const handleAnalyze = async (file: File, _useCache: boolean) => {
        setLoading(true)
        setError(null)
        setResult(null)

        try {
            const response = await analyzeVoice(file, true)
            setResult(response)
            showToast(getText('voice.analysisComplete', 'Analysis complete!'), 'success')
            setRefreshTrigger(prev => prev + 1) // Refresh stats
        } catch (err: any) {
            console.error('Analysis error:', err)
            const errorMsg = err.message || getText('voice.analysisFailed', 'Analysis failed')
            setError(errorMsg)
            showToast(errorMsg, 'error')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="voice-page">
            <div className="page-header">
                <h1>🎙️ {getText('voice.pageTitle', 'Voice Deepfake Detection')}</h1>
                <p>
                    {getText('voice.pageDescription', 'Advanced AI-powered audio analysis to detect synthetic voices using WavLM embeddings and spectral artifact detection.')}
                </p>
            </div>

            {/* Statistics Dashboard (Kept as it's useful context) */}
            <VoiceStats stats={stats} loading={!stats && loading} />

            {/* Main Analysis Section (Centered Single Column) */}
            <div className="analysis-container">
                <div className="upload-section-container">
                    <AudioUpload onAnalyze={handleAnalyze} loading={loading} />
                </div>

                {loading && <ForensicScanner type="voice" />}

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
