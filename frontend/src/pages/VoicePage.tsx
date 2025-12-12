
import { useState } from 'react'
import { AudioUpload } from '../components/voice/AudioUpload'
import { VoiceAnalysisResult } from '../components/voice/VoiceAnalysisResult'
import { analyzeAudio, VoiceResponse } from '../api/voiceApi'
import { Loader } from '../components/common/Loader'
import { ErrorAlert } from '../components/common/ErrorAlert'
import '../components/voice/VoicePage.css'

export function VoicePage() {
    const [file, setFile] = useState<File | null>(null)
    const [result, setResult] = useState<VoiceResponse | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleFileSelect = (selectedFile: File) => {
        setFile(selectedFile)
        setResult(null)
        setError(null)
    }

    const handleClearFile = () => {
        setFile(null)
        setResult(null)
        setError(null)
    }

    const handleAnalyze = async () => {
        if (!file) return

        setLoading(true)
        setError(null)

        try {
            const data = await analyzeAudio(file)
            setResult(data)
        } catch (err: any) {
            console.error('Analysis failed:', err)
            // Extract error message from axios error
            const message = err.response?.data?.detail || 'Failed to analyze audio. Please try again.'
            setError(message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="voice-page">
            <div className="page-header">
                <h1>Voice Deepfake Detection</h1>
                <p>Analyze audio files for deepfake manipulation</p>
            </div>

            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                <AudioUpload
                    onFileSelect={handleFileSelect}
                    selectedFile={file}
                    onClearFile={handleClearFile}
                />

                {error && (
                    <div style={{ marginBottom: '2rem' }}>
                        <ErrorAlert message={error} onClose={() => setError(null)} />
                    </div>
                )}

                {file && !loading && !result && (
                    <button
                        className="analyze-btn"
                        onClick={handleAnalyze}
                        disabled={loading}
                    >
                        Analyze Audio
                    </button>
                )}

                {loading && (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '2rem' }}>
                        <Loader />
                        <p style={{ marginTop: '1rem', color: '#6b7280' }}>Analyzing audio patterns using AI...</p>
                    </div>
                )}

                {result && <VoiceAnalysisResult result={result} />}
            </div>
        </div>
    )
}
