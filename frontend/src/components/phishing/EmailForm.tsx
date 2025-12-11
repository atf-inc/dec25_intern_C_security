import { useState, FormEvent, useRef } from 'react'
import './EmailForm.css'

interface EmailFormProps {
    onSubmit: (data: EmailFormData) => void
    loading: boolean
}

export interface EmailFormData {
    subject: string
    sender: string
    body: string
    urls: string[]
    pdfFile?: File
}

export function EmailForm({ onSubmit, loading }: EmailFormProps) {
    const [subject, setSubject] = useState('')
    const [sender, setSender] = useState('')
    const [body, setBody] = useState('')
    const [urls, setUrls] = useState('')
    const [pdfFile, setPdfFile] = useState<File | null>(null)
    const [inputMode, setInputMode] = useState<'manual' | 'pdf'>('manual')
    const fileInputRef = useRef<HTMLInputElement>(null)

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]

        if (!file) {
            return
        }

        console.log('File selected:', {
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified
        })

        // Check file size - common issue with OneDrive/cloud placeholders
        if (file.size === 0) {
            alert('Selected file is empty (0 bytes). This often happens with OneDrive/cloud files. Try:\n1. Copy the file to Desktop\n2. Right-click → "Always keep on this device"\n3. Or recreate the file locally')
            if (fileInputRef.current) {
                fileInputRef.current.value = ''
            }
            return
        }

        // Check file type
        const isEmlFile = file.name.toLowerCase().endsWith('.eml')
        const isPdfFile = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')

        if (isEmlFile || isPdfFile) {
            // File is valid, set it directly
            setPdfFile(file)
            // Clear manual input when file is uploaded
            setSubject('')
            setSender('')
            setBody('')
            setUrls('')
            console.log('File accepted:', file.name, file.size, 'bytes')
        } else {
            alert('Please select a PDF or EML file only.')
            if (fileInputRef.current) {
                fileInputRef.current.value = ''
            }
        }
    }

    const handleRemovePdf = () => {
        setPdfFile(null)
        if (fileInputRef.current) {
            fileInputRef.current.value = ''
        }
    }

    const handleModeSwitch = (mode: 'manual' | 'pdf') => {
        setInputMode(mode)
        if (mode === 'manual') {
            setPdfFile(null)
            if (fileInputRef.current) {
                fileInputRef.current.value = ''
            }
        } else {
            // Clear manual inputs when switching to PDF mode
            setSubject('')
            setSender('')
            setBody('')
            setUrls('')
        }
    }

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault()

        // Parse URLs (split by newlines or commas)
        const urlList = urls
            .split(/[\n,]/)
            .map((url) => url.trim())
            .filter((url) => url.length > 0)

        onSubmit({
            subject,
            sender,
            body,
            urls: urlList,
            pdfFile: pdfFile || undefined,
        })
    }

    const isFormValid = inputMode === 'pdf'
        ? pdfFile !== null
        : subject.trim() && sender.trim() && body.trim()

    return (
        <form className="email-form" onSubmit={handleSubmit}>
            {/* Input Mode Selector */}
            <div className="input-mode-selector">
                <div className="mode-tabs">
                    <button
                        type="button"
                        className={`mode-tab ${inputMode === 'manual' ? 'active' : ''}`}
                        onClick={() => handleModeSwitch('manual')}
                        disabled={loading}
                    >
                        📝 Manual Input
                    </button>
                    <button
                        type="button"
                        className={`mode-tab ${inputMode === 'pdf' ? 'active' : ''}`}
                        onClick={() => handleModeSwitch('pdf')}
                        disabled={loading}
                    >
                        📄 Upload File
                    </button>
                </div>
                <p className="mode-description">
                    {inputMode === 'manual'
                        ? 'Manually enter email details below'
                        : 'Upload an email file (EML or PDF format)'
                    }
                </p>
            </div>

            {/* File Upload Mode */}
            {inputMode === 'pdf' && (
                <div className="pdf-upload-section">
                    <div className="form-group">
                        <label htmlFor="pdf-upload">Upload Email File *</label>
                        <div className="file-upload-area">
                            {!pdfFile && (
                                <input
                                    type="file"
                                    id="pdf-upload"
                                    ref={fileInputRef}
                                    accept=".pdf,.eml"
                                    onChange={handleFileChange}
                                    disabled={loading}
                                    className="file-input"
                                />
                            )}
                            <div className="file-upload-content">
                                {pdfFile ? (
                                    <div className="file-selected">
                                        <div className="file-info">
                                            <span className="file-icon">📄</span>
                                            <div className="file-details">
                                                <span className="file-name">{pdfFile.name}</span>
                                                <span className="file-size">
                                                    {(pdfFile.size / 1024 / 1024).toFixed(2)} MB
                                                </span>
                                            </div>
                                        </div>
                                        <button
                                            type="button"
                                            className="remove-file-btn"
                                            onClick={(e) => {
                                                e.preventDefault()
                                                e.stopPropagation()
                                                handleRemovePdf()
                                            }}
                                            disabled={loading}
                                            title="Remove file"
                                        >
                                            ✕
                                        </button>
                                    </div>
                                ) : (
                                    <div className="file-upload-prompt">
                                        <span className="upload-icon">📤</span>
                                        <p>Click to select email file or drag and drop</p>
                                        <small>EML or PDF files, max 10MB</small>
                                    </div>
                                )}
                            </div>
                        </div>
                        <small className="form-hint">
                            💡 Tip: Save as EML (File → Save As → EML) or PDF (Print → Save as PDF) from your email client
                        </small>
                    </div>
                </div>
            )}

            {/* Manual Input Mode */}
            {inputMode === 'manual' && (
                <div className="manual-input-section">
                    <div className="form-group">
                        <label htmlFor="subject">Email Subject *</label>
                        <input
                            type="text"
                            id="subject"
                            value={subject}
                            onChange={(e) => setSubject(e.target.value)}
                            placeholder="e.g., Urgent: Verify your account"
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="sender">Sender Email *</label>
                        <input
                            type="email"
                            id="sender"
                            value={sender}
                            onChange={(e) => setSender(e.target.value)}
                            placeholder="e.g., noreply@example.com"
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="body">Email Body *</label>
                        <textarea
                            id="body"
                            value={body}
                            onChange={(e) => setBody(e.target.value)}
                            placeholder="Paste the email content here..."
                            rows={8}
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="urls">URLs (Optional)</label>
                        <textarea
                            id="urls"
                            value={urls}
                            onChange={(e) => setUrls(e.target.value)}
                            placeholder="Enter URLs found in the email (one per line or comma-separated)"
                            rows={3}
                            disabled={loading}
                        />
                        <small className="form-hint">
                            Enter any suspicious links found in the email
                        </small>
                    </div>
                </div>
            )}

            <button
                type="submit"
                className="submit-button"
                disabled={!isFormValid || loading}
            >
                {loading ? 'Analyzing...' : inputMode === 'pdf' ? 'Analyze File' : 'Analyze Email'}
            </button>
        </form>
    )
}
