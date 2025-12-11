import apiClient from './client'

export interface EmailAnalysisRequest {
    subject: string
    body: string
    sender: string
    urls?: string[]
    pdfFile?: File  // Note: This handles both EML and PDF files despite the name
}

export interface PhishingResponse {
    request_id: string
    label: string
    score: number
    reasons: string[]
    evidence?: any[]
    suggested_action?: string
}

export async function analyzeEmail(data: EmailAnalysisRequest): Promise<PhishingResponse> {
    // If file is provided (EML or PDF), use multipart/form-data with appropriate endpoint
    if (data.pdfFile) {
        const formData = new FormData()
        formData.append('file', data.pdfFile)

        // Determine endpoint based on file type
        const isEmlFile = data.pdfFile.name.endsWith('.eml')
        const isPdfFile = data.pdfFile.type === 'application/pdf'

        let endpoint: string
        if (isEmlFile) {
            endpoint = '/api/v1/upload/eml'
        } else if (isPdfFile) {
            endpoint = '/api/v1/upload/pdf'
        } else {
            throw new Error('Unsupported file type. Please upload EML or PDF files only.')
        }

        const response = await apiClient.post<PhishingResponse>(
            endpoint,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        )
        const result = response.data
        saveToHistory(result, data.subject || 'PDF Scan', 'PDF Upload', '')
        return result
    } else {
        // Regular JSON request for manual input
        const requestData = {
            subject: data.subject,
            from_email: data.sender,
            raw_text: data.body,
            visible_links: data.urls?.map(url => ({
                uri: url,
                anchor_text: url
            })) || []
        }

        const response = await apiClient.post<PhishingResponse>('/api/v1/phishing/analyze', requestData)
        const result = response.data

        // Save to local history
        saveToHistory(result, data.subject || 'No Subject', data.sender || 'Unknown Sender', data.body || '')

        return result
    }
}

// Helper to save history
import { storage } from '../utils/storage'
function saveToHistory(response: PhishingResponse, subject: string, sender: string, body: string) {
    const historyItem: ScanHistoryItem = {
        id: Date.now(), // Use timestamp for local ID
        date: new Date().toISOString(),
        subject: subject,
        sender: sender,
        risk_score: response.score,
        risk_level: response.label as 'low' | 'medium' | 'high',
        analysis_result: response,
        original_input: {
            subject: subject,
            sender: sender,
            body: body
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
