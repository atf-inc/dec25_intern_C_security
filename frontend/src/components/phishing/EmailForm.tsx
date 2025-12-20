import { useState, FormEvent, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import './EmailForm.css'

// Assuming EmailAnalysisRequest is defined elsewhere or will be defined.
// Based on the handleSubmit change, it seems to be:
export interface EmailAnalysisRequest {
    subject: string
    sender: string
    body: string
    urls?: string[] // Keeping urls as optional based on original EmailFormData
    pdfFile?: File // Keeping pdfFile as optional based on original EmailFormData
}

interface EmailFormProps {
    onSubmit: (data: EmailAnalysisRequest) => Promise<void> // Changed return type to Promise<void>
    loading: boolean
    initialData?: { // Added initialData prop
        subject: string
        body: string
        sender: string
    }
}

export interface EmailFormData { // This interface is still used internally for handleSubmit before calling onSubmit
    subject: string
    sender: string
    body: string
    urls: string[]
    pdfFile?: File
}

export function EmailForm({ onSubmit, loading, initialData }: EmailFormProps) { // Added initialData to props
    const { t } = useTranslation()
    const [subject, setSubject] = useState(initialData?.subject || '') // Initialized with initialData
    const [sender, setSender] = useState(initialData?.sender || '') // Initialized with initialData
    const [body, setBody] = useState(initialData?.body || '') // Initialized with initialData
    const [urls, setUrls] = useState('')
    const [pdfFile, setPdfFile] = useState<File | null>(null)
    const [inputMode, setInputMode] = useState<'manual' | 'pdf'>('manual')
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Validation State
    const [shouldValidate, setShouldValidate] = useState(false)
    const [errors, setErrors] = useState<{ [key: string]: string }>({})

    const validateEmail = (email: string) => {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    }

    // Real-time validation
    useEffect(() => {
        if (!shouldValidate && inputMode === 'manual') return

        const newErrors: { [key: string]: string } = {}

        if (inputMode === 'manual') {
            if (!subject.trim()) newErrors.subject = t('phishing.requiredField', 'This field is required')

            if (!sender.trim()) {
                newErrors.sender = t('phishing.requiredField', 'This field is required')
            } else if (!validateEmail(sender)) {
                newErrors.sender = t('phishing.invalidEmail', 'Please enter a valid email address')
            }

            if (!body.trim()) newErrors.body = t('phishing.requiredField', 'This field is required')
        }

        setErrors(newErrors)
    }, [subject, sender, body, inputMode, shouldValidate, t])

    // Update state if initialData changes (e.g. loading from history)
    useEffect(() => {
        if (initialData) {
            setSubject(initialData.subject)
            setSender(initialData.sender)
            setBody(initialData.body)
            setInputMode('manual') // Assuming 'manual' is the default for initialData
            setUrls('') // Clear other fields
            setPdfFile(null) // Clear other fields
            if (fileInputRef.current) {
                fileInputRef.current.value = ''
            }
        }
    }, [initialData])

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
                        📝 {t('phishing.manualInput')}
                    </button>
                    <button
                        type="button"
                        className={`mode-tab ${inputMode === 'pdf' ? 'active' : ''}`}
                        onClick={() => handleModeSwitch('pdf')}
                        disabled={loading}
                    >
                        📄 {t('phishing.uploadFile')}
                    </button>
                </div>
                <p className="mode-description">
                    {inputMode === 'manual'
                        ? t('phishing.manualInputDesc')
                        : t('phishing.uploadFileDesc')
                    }
                </p>
            </div>

            {/* File Upload Mode */}
            {inputMode === 'pdf' && (
                <div className="pdf-upload-section">
                    <div className="form-group">
                        <label htmlFor="pdf-upload">{t('phishing.uploadEmailFile')} *</label>
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
                                        <p>{t('phishing.clickToSelect')}</p>
                                        <small>{t('phishing.emlOrPdf')}</small>
                                    </div>
                                )}
                            </div>
                        </div>
                        <small className="form-hint">
                            💡 {t('phishing.tipSaveAs')}
                        </small>
                    </div>
                </div>
            )}

            {/* Manual Input Mode */}
            {inputMode === 'manual' && (
                <div className="manual-input-section">
                    <div className="form-group">
                        <label htmlFor="subject">{t('phishing.emailSubject')} *</label>
                        <input
                            type="text"
                            id="subject"
                            value={subject}
                            onChange={(e) => setSubject(e.target.value)}
                            placeholder={t('phishing.subjectPlaceholder')}
                            required
                            disabled={loading}
                            className={errors.subject ? 'error-input' : ''}
                            onBlur={() => setShouldValidate(true)}
                        />
                        {errors.subject && <span className="error-msg">{errors.subject}</span>}
                    </div>

                    <div className="form-group">
                        <label htmlFor="sender">{t('phishing.senderEmail')} *</label>
                        <input
                            type="email"
                            id="sender"
                            value={sender}
                            onChange={(e) => setSender(e.target.value)}
                            placeholder={t('phishing.senderPlaceholder')}
                            required
                            disabled={loading}
                            className={errors.sender ? 'error-input' : ''}
                            onBlur={() => setShouldValidate(true)}
                        />
                        {errors.sender && <span className="error-msg">{errors.sender}</span>}
                    </div>

                    <div className="form-group">
                        <label htmlFor="body">{t('phishing.emailBody')} *</label>
                        <textarea
                            id="body"
                            value={body}
                            onChange={(e) => setBody(e.target.value)}
                            placeholder={t('phishing.bodyPlaceholder')}
                            rows={8}
                            required
                            disabled={loading}
                            className={errors.body ? 'error-input' : ''}
                            onBlur={() => setShouldValidate(true)}
                        />
                        {errors.body && <span className="error-msg">{errors.body}</span>}
                    </div>

                    <div className="form-group">
                        <label htmlFor="urls">{t('phishing.urls')}</label>
                        <textarea
                            id="urls"
                            value={urls}
                            onChange={(e) => setUrls(e.target.value)}
                            placeholder={t('phishing.urlsPlaceholder')}
                            rows={3}
                            disabled={loading}
                        />
                        <small className="form-hint">
                            {t('phishing.urlsHint')}
                        </small>
                    </div>
                </div>
            )}

            <button
                type="submit"
                className="submit-button"
                disabled={!isFormValid || loading}
            >
                {loading ? t('phishing.analyzing') : inputMode === 'pdf' ? t('phishing.analyzeFile') : t('phishing.analyzeEmail')}
            </button>
        </form>
    )
}
