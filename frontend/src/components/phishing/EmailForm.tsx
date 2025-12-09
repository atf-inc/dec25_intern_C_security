import { useState, FormEvent } from 'react'
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
}

export function EmailForm({ onSubmit, loading }: EmailFormProps) {
    const [subject, setSubject] = useState('')
    const [sender, setSender] = useState('')
    const [body, setBody] = useState('')
    const [urls, setUrls] = useState('')

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
        })
    }

    const isFormValid = subject.trim() && sender.trim() && body.trim()

    return (
        <form className="email-form" onSubmit={handleSubmit}>
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

            <button
                type="submit"
                className="submit-button"
                disabled={!isFormValid || loading}
            >
                {loading ? 'Analyzing...' : 'Analyze Email'}
            </button>
        </form>
    )
}
