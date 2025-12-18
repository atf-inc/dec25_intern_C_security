import { useState, useEffect } from 'react'
import './ForensicScanner.css'

const EMAIL_SCAN_STEPS = [
    "Initializing security protocols...",
    "Extracting email metadata & headers...",
    "Scanning for deceptive patterns...",
    "Analyzing URL reputation pools...",
    "Querying threat intelligence databases...",
    "Executing LLM inference engine...",
    "Compiling risk assessment report..."
]

const VOICE_SCAN_STEPS = [
    "Initializing deepfake detection protocols...",
    "Loading WavLM neural network models...",
    "Extracting acoustic embeddings & features...",
    "Analyzing spectral artifacts & anomalies...",
    "Running vocoder detection algorithms...",
    "Processing AI-generated voice signatures...",
    "Compiling authenticity assessment..."
]

interface ForensicScannerProps {
    type?: 'email' | 'voice'
}

export function ForensicScanner({ type = 'email' }: ForensicScannerProps) {
    const [currentStep, setCurrentStep] = useState(0)
    const [logs, setLogs] = useState<string[]>([])

    const SCAN_STEPS = type === 'voice' ? VOICE_SCAN_STEPS : EMAIL_SCAN_STEPS

    useEffect(() => {
        // Reset state on mount
        setCurrentStep(0)
        setLogs([])

        const stepInterval = setInterval(() => {
            setCurrentStep(prev => {
                if (prev < SCAN_STEPS.length - 1) {
                    return prev + 1
                }
                return prev // Stay on last step
            })
        }, 800) // Advance step every 800ms

        return () => clearInterval(stepInterval)
    }, [type])

    useEffect(() => {
        if (currentStep < SCAN_STEPS.length) {
            setLogs(prev => [...prev, `> ${SCAN_STEPS[currentStep]}`])
        }
    }, [currentStep, SCAN_STEPS])

    return (
        <div className="forensic-scanner-overlay">
            <div className="forensic-terminal">
                <div className="terminal-header">
                    <div className="terminal-dot red"></div>
                    <div className="terminal-dot yellow"></div>
                    <div className="terminal-dot green"></div>
                    <span className="terminal-title">
                        CYBER_X_FORENSICS // {type === 'voice' ? 'DEEPFAKE_SCAN' : 'ACTIVE_SCAN'}
                    </span>
                </div>
                <div className="terminal-content">
                    <div className="scan-grid">
                        <div className="scan-visualizer">
                            <div className="radar-circle"></div>
                            <div className="radar-sweep"></div>
                        </div>
                        <div className="scan-logs">
                            {logs.map((log, idx) => (
                                <div key={idx} className="log-line">
                                    <span className="log-timestamp">[{new Date().toLocaleTimeString().split(' ')[0]}]</span>
                                    <span className="log-text">{log}</span>
                                </div>
                            ))}
                            <div className="log-line blinking-cursor">
                                <span className="log-prefix">_</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="terminal-footer">
                    <span className="status-text">STATUS: PROCESSING</span>
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{ width: `${((currentStep + 1) / SCAN_STEPS.length) * 100}%` }}
                        ></div>
                    </div>
                </div>
            </div>
        </div>
    )
}
