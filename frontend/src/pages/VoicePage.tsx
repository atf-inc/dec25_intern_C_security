
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
            <div className="page-header-container">
                <div className="header-icon-wrapper">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                        <path d="M12 8v4" />
                        <path d="M12 16h.01" />
                    </svg>
                </div>
                <div>
                    <h1>Voice Deepfake Detection</h1>
                    <p>AI-powered audio authenticity verification</p>
                </div>
            </div>

            <div className="voice-content-grid">
                {/* Left Column: Upload */}
                <div className="upload-section">
                    <div className="section-header">
                        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ color: '#3b82f6', fontSize: '1.5rem' }}>≈</span>
                            Upload Audio File
                        </h2>
                    </div>
                    <p className="section-description">
                        Upload your audio file to analyze whether it contains deepfake or
                        synthetic voice patterns. Supports WAV, MP3, and other common formats.
                    </p>

                    <AudioUpload
                        onFileSelect={handleFileSelect}
                        selectedFile={file}
                        onClearFile={handleClearFile}
                    />

                    {error && (
                        <div style={{ marginBottom: '1.5rem' }}>
                            <ErrorAlert message={error} onClose={() => setError(null)} />
                        </div>
                    )}

                    <button
                        className="analyze-btn"
                        onClick={handleAnalyze}
                        disabled={!file || loading}
                    >
                        {loading ? 'Analyzing...' : 'Analyze Audio'}
                    </button>

                    <div className="info-cards">
                        <div className="info-card">
                            <h3>Supported Formats</h3>
                            <p>WAV, MP3, AAC, FLAC, OGG, and more</p>
                        </div>
                        <div className="info-card">
                            <h3>Analysis Time</h3>
                            <p>Typically 3-10 seconds per file</p>
                        </div>
                    </div>
                </div>

                {/* Right Column: Results */}
                <div className="results-section">
                    <h2>Analysis Results</h2>
                    <p className="results-description">
                        Our AI model analyzes audio patterns, frequency characteristics, and artifacts
                        to detect synthetic or manipulated voices.
                    </p>

                    <div className="results-container">
                        {loading ? (
                            <div className="loading-state">
                                <Loader />
                                <p>Processing audio file...</p>
                            </div>
                        ) : result ? (
                            <VoiceAnalysisResult result={result} />
                        ) : (
                            <div className="empty-state">
                                <div className="empty-icon-wrapper">
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                                        <path d="M9 12l2 2 4-4" />
                                    </svg>
                                </div>
                                <p>Upload and analyze a file to see results</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
