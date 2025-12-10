import apiClient from './client'

export interface EmailAnalysisRequest {
    subject: string
    body: string
    sender: string
    urls?: string[]
    pdfFile?: File
}

export interface PhishingResponse {
    id: number
    risk_score: number
    risk_level: 'low' | 'medium' | 'high'
    explanation: string
    highlights: string[]
    created_at: string
}

export async function analyzeEmail(data: EmailAnalysisRequest): Promise<PhishingResponse> {
    // If PDF file is provided, use multipart/form-data
    if (data.pdfFile) {
        const formData = new FormData()
        formData.append('pdf_file', data.pdfFile)

        // Add other fields if they exist (for hybrid mode)
        if (data.subject) formData.append('subject', data.subject)
        if (data.sender) formData.append('sender', data.sender)
        if (data.body) formData.append('body', data.body)
        if (data.urls && data.urls.length > 0) {
            formData.append('urls', JSON.stringify(data.urls))
        }

        const response = await apiClient.post<PhishingResponse>(
            '/api/v1/phishing/analyze-pdf',
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        )
        const result = response.data
        saveToHistory(result, data.subject || 'PDF Scan', 'PDF Upload')
        return result
    } else {
        // Regular JSON request for manual input

        const response = await apiClient.post<PhishingResponse>('/api/v1/phishing/analyze', data)
        const result = response.data

        // Save to local history
        saveToHistory(result, data.subject || 'No Subject', data.sender || 'Unknown Sender')

        return result
    }
}

// Helper to save history
import { storage } from '../utils/storage'
function saveToHistory(response: PhishingResponse, subject: string, sender: string) {
    const historyItem: ScanHistoryItem = {
        id: response.id || Date.now(), // Fallback ID if server doesn't provide one unique enough for local
        date: response.created_at || new Date().toISOString(),
        subject: subject,
        sender: sender,
        risk_score: response.risk_score,
        risk_level: response.risk_level,
        analysis_result: response,
        original_input: {
            subject: subject,
            sender: sender,
            body: '' // We might not have body here easily unless passed, for now leaving empty or we need to pass it
        }
    }
    storage.saveScan(historyItem)
}

export interface ScanHistoryItem {
    id: number
    date: string
    subject: string
    sender: string
    risk_score: number
    risk_level: 'low' | 'medium' | 'high'
    // Optional fields for replay
    analysis_result?: PhishingResponse
    original_input?: {
        subject: string
        body: string
        sender: string
    }
}

export interface ScanHistoryParams {
    risk_level?: string
    start_date?: string
    end_date?: string
}

export async function getScanHistory(params?: ScanHistoryParams): Promise<ScanHistoryItem[]> {
    // Read from local storage instead of API
    let history = storage.getHistory()

    // Apply filters locally
    if (params) {
        if (params.risk_level) {
            history = history.filter(item => item.risk_level === params.risk_level)
        }

        if (params.start_date) {
            const startDate = new Date(params.start_date)
            // Reset time to start of day for accurate comparison
            startDate.setHours(0, 0, 0, 0)
            history = history.filter(item => new Date(item.date) >= startDate)
        }

        if (params.end_date) {
            const endDate = new Date(params.end_date)
            // Set time to end of day
            endDate.setHours(23, 59, 59, 999)
            history = history.filter(item => new Date(item.date) <= endDate)
        }
    }

    // Simulate async for compatibility
    return Promise.resolve(history)
}
