import { useState, useRef, useEffect, ChangeEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { WaveformVisualizer } from './WaveformVisualizer'
import './AudioUpload.css'

interface AudioUploadProps {
    onAnalyze: (file: File, useCache: boolean) => Promise<void>
    loading: boolean
}

const ALLOWED_FORMATS = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB
const MAX_DURATION = 30 // seconds

export function AudioUpload({ onAnalyze, loading }: AudioUploadProps) {
    const { t } = useTranslation()
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [isDragging, setIsDragging] = useState(false)
    const [useCache, setUseCache] = useState(true)
    const [validationError, setValidationError] = useState<string | null>(null)
    const [audioUrl, setAudioUrl] = useState<string | null>(null)

    // Playback State
    const [isPlaying, setIsPlaying] = useState(false)
    const [currentTime, setCurrentTime] = useState(0)
    const [duration, setDuration] = useState(0)

    const fileInputRef = useRef<HTMLInputElement>(null)
    const audioRef = useRef<HTMLAudioElement>(new Audio())

    // Fallback function for translations
    const getText = (key: string, fallback: string) => {
        const translated = t(key)
        return translated === key ? fallback : translated
    }

    // Cleanup audio URL on unmount
    useEffect(() => {
        return () => {
            if (audioUrl) URL.revokeObjectURL(audioUrl)
        }
    }, [])

    // Setup Audio Listeners
    useEffect(() => {
        const audio = audioRef.current

        const updateTime = () => setCurrentTime(audio.currentTime)
        const updateDuration = () => setDuration(audio.duration)
        const onEnded = () => setIsPlaying(false)

        audio.addEventListener('timeupdate', updateTime)
        audio.addEventListener('loadedmetadata', updateDuration)
        audio.addEventListener('ended', onEnded)

        return () => {
            audio.removeEventListener('timeupdate', updateTime)
            audio.removeEventListener('loadedmetadata', updateDuration)
            audio.removeEventListener('ended', onEnded)
            audio.pause()
        }
    }, [])

    const handleFileSelect = (file: File) => {
        setValidationError(null)

        // 1. Size Validation
        if (file.size > MAX_FILE_SIZE) {
            setValidationError(getText('voice.fileSizeExceeds', 'File size exceeds 10MB limit'))
            return
        }

        // 2. Format Validation
        const ext = '.' + file.name.split('.').pop()?.toLowerCase()
        if (!ALLOWED_FORMATS.includes(ext)) {
            setValidationError(getText('voice.unsupportedFormat', 'Unsupported file format'))
            return
        }

        // 3. Create URL and Verify Duration
        const url = URL.createObjectURL(file)
        const tempAudio = new Audio(url)

        tempAudio.onloadedmetadata = () => {
            if (tempAudio.duration > MAX_DURATION) {
                setValidationError(getText('voice.durationExceeds', 'Audio duration ({duration}s) exceeds 30s limit').replace('{duration}', tempAudio.duration.toFixed(1)))
                URL.revokeObjectURL(url)
            } else {
                // Success
                setSelectedFile(file)
                setAudioUrl(url)

                // Reset player
                audioRef.current.src = url
                audioRef.current.load()
                setIsPlaying(false)
                setCurrentTime(0)
            }
        }
    }

    const togglePlay = () => {
        if (!audioRef.current.src) return

        if (isPlaying) {
            audioRef.current.pause()
        } else {
            audioRef.current.play()
        }
        setIsPlaying(!isPlaying)
    }

    const handleSeek = (time: number) => {
        if (audioRef.current) {
            audioRef.current.currentTime = time
            setCurrentTime(time)
        }
    }

    const removeFile = () => {
        setSelectedFile(null)
        setAudioUrl(null)
        setValidationError(null)
        setIsPlaying(false)
        if (fileInputRef.current) fileInputRef.current.value = ''
        audioRef.current.pause()
        audioRef.current.src = ''
    }

    // Drag & Drop handlers (unchanged mostly)
    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }
    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
    }
    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
        if (e.dataTransfer.files?.[0]) handleFileSelect(e.dataTransfer.files[0])
    }
    const handleBrowse = () => fileInputRef.current?.click()
    const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files?.[0]) handleFileSelect(e.target.files[0])
    }

    return (
        <div className="audio-upload-container">
            {/* 1. Upload Zone (Only show if no file selected) */}
            {!selectedFile ? (
                <div
                    className={`upload-zone ${isDragging ? 'drag-active' : ''} ${loading ? 'disabled' : ''}`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={!loading ? handleBrowse : undefined}
                >
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileInput}
                        accept={ALLOWED_FORMATS.join(',')}
                        hidden
                    />
                    <div className="upload-content">
                        <span className="upload-icon">☁️</span>
                        <h3>{getText('voice.dropAudioFile', 'Drop audio file here or click to browse')}</h3>
                        <div className="upload-formats">
                            {ALLOWED_FORMATS.map(fmt => (
                                <span key={fmt} className="format-badge">{fmt.toUpperCase()}</span>
                            ))}
                        </div>
                        <p className="upload-limits">{getText('voice.maxSize', 'Max size: 10MB')} | {getText('voice.maxDuration', 'Max duration: 30s')}</p>
                    </div>
                </div>
            ) : (
                /* 2. File Preview & Waveform (Show when file selected) */
                <div className="file-preview-section">
                    <div className="file-header">
                        <div className="file-info">
                            <span className="file-icon">🎵</span>
                            <div>
                                <h4 className="file-name">{selectedFile.name}</h4>
                                <span className="file-meta">
                                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • {duration.toFixed(1)}s
                                </span>
                            </div>
                        </div>
                        <button onClick={removeFile} className="remove-btn" disabled={loading}>×</button>
                    </div>

                    {/* The Waveform Visualizer */}
                    {audioUrl && (
                        <WaveformVisualizer
                            audioUrl={audioUrl}
                            isPlaying={isPlaying}
                            currentTime={currentTime}
                            duration={duration}
                            onSeek={handleSeek}
                        />
                    )}

                    {/* Playback Controls */}
                    <div className="playback-controls">
                        <button
                            className={`play-btn ${isPlaying ? 'playing' : ''}`}
                            onClick={togglePlay}
                        >
                            {isPlaying ? `⏸ ${getText('voice.pause', 'Pause')}` : `▶ ${getText('voice.playPreview', 'Play Preview')}`}
                        </button>
                        <span className="time-display">
                            {formatTime(currentTime)} / {formatTime(duration)}
                        </span>
                    </div>
                </div>
            )}

            {validationError && (
                <div className="validation-error">
                    <span className="error-icon">⚠️</span>
                    {validationError}
                </div>
            )}

            {/* Cache & Analyze Options */}
            {selectedFile && !validationError && (
                <div className="action-footer">
                    <div className="cache-toggle">
                        <label className="switch">
                            <input
                                type="checkbox"
                                checked={useCache}
                                onChange={(e) => setUseCache(e.target.checked)}
                                disabled={loading}
                            />
                            <span className="slider round"></span>
                        </label>
                        <span className="cache-text">{getText('voice.enableCaching', 'Enable Result Caching')}</span>
                    </div>

                    <button
                        className="analyze-btn-large"
                        onClick={() => onAnalyze(selectedFile, useCache)}
                        disabled={loading}
                    >
                        {loading ? getText('voice.processing', 'Processing...') : `🛡️ ${getText('voice.analyzeAudio', 'Analyze Audio')}`}
                    </button>
                </div>
            )}
        </div>
    )
}

function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
}
