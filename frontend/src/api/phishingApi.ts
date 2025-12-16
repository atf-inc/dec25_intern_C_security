import apiClient from './client'
import { storage } from '../utils/storage'

export interface EmailAnalysisRequest {
    subject: string
    body: string
    sender: string
    urls?: string[]
    pdfFile?: File  // Supports EML and PDF
}

export interface PhishingResponse {
    request_id: string
    label: string
    score: number
    reasons: string[]
    evidence?: any[]
    suggested_action?: string
    suggested_reply?: string
    ai_explanation?: {
        summary: string
        suspicious_indicators: string[]
        ai_reasoning: string
        technical_indicators: string[]
        final_assessment: string
        recommended_action: string
        full_explanation: string
    }
    model_meta?: any
}

export interface ScanHistoryItem {
    id: number
    date: string
    type: 'email' | 'voice'
    subject: string
    sender: string
    risk_score: number
    risk_level: 'low' | 'medium' | 'high'
    analysis_result?: PhishingResponse
    original_input?: {
        subject: string
        body: string
        sender: string
    }
}

// ------------------------------------------------------------
// Main Email Analyzer (Merged version)
// ------------------------------------------------------------

export async function analyzeEmail(data: EmailAnalysisRequest): Promise<PhishingResponse> {
    console.log('analyzeEmail called with data:', data)

    // CASE 1: File provided → upload first → then analyze
    if (data.pdfFile) {
        console.log('File detected, preparing FormData...')

        if (data.pdfFile.size === 0) {
            throw new Error('Selected file is empty (0 bytes). Please select a valid file.')
        }

        const formData = new FormData()
        formData.append('file', data.pdfFile, data.pdfFile.name)

        const isEmlFile = data.pdfFile.name.toLowerCase().endsWith('.eml')
        const isPdfFile =
            data.pdfFile.type === 'application/pdf' ||
            data.pdfFile.name.toLowerCase().endsWith('.pdf')

        let uploadEndpoint: string
        if (isEmlFile) uploadEndpoint = '/upload/eml'
        else if (isPdfFile) uploadEndpoint = '/upload/pdf'
        else throw new Error('Unsupported file type. Please upload EML or PDF.')

        console.log('Uploading to:', uploadEndpoint)

        const uploadResponse = await apiClient.post(uploadEndpoint, formData)

        // After upload → call Akash's /analyze endpoint
        const analyzeRequest = {
            subject: uploadResponse.data.subject || '',
            from_email: uploadResponse.data.from_email || '',
            raw_text: uploadResponse.data.raw_text || '',
            visible_links: uploadResponse.data.visible_links || [],
            hidden_links: uploadResponse.data.hidden_links || [],
            meta: { consent: true }
        }

        const response = await apiClient.post<PhishingResponse>('/analyze/', analyzeRequest)
        const result = response.data

        // Save to local history
        saveToHistory(
            result,
            analyzeRequest.subject,
            analyzeRequest.from_email,
            analyzeRequest.raw_text
        )

        return result
    }

    // CASE 2: No file → manual JSON input (develop branch structure)
    const requestData = {
        subject: data.subject,
        from_email: data.sender,
        raw_text: data.body,
        visible_links:
            data.urls?.map(url => ({
                uri: url,
                anchor_text: url
            })) || [],
        meta: { consent: true }
    }

    const response = await apiClient.post<PhishingResponse>('/analyze/', requestData)
    const result = response.data

    // Save to history (from feature/scan-history-dashboard)
    saveToHistory(result, data.subject, data.sender, data.body)

    return result
}

// ------------------------------------------------------------
// Save Scan History Utility
// ------------------------------------------------------------
function saveToHistory(response: PhishingResponse, subject: string, sender: string, body: string) {
    const historyItem: ScanHistoryItem = {
        id: Date.now(),
        date: new Date().toISOString(),
        type: 'email',
        subject,
        sender,
        risk_score: response.score,
        risk_level: response.label as 'low' | 'medium' | 'high',
        analysis_result: response,
        original_input: { subject, body, sender }
    }

    storage.saveScan(historyItem)
}

// ------------------------------------------------------------
// Local Scan History Filters
// ------------------------------------------------------------
export interface ScanHistoryParams {
    risk_level?: string
    start_date?: string
    end_date?: string
    search_query?: string
}

export async function getScanHistory(params?: ScanHistoryParams): Promise<ScanHistoryItem[]> {
    let history = storage.getHistory()

    if (params) {
        if (params.risk_level) {
            history = history.filter(item => item.risk_level === params.risk_level)
        }

        if (params.start_date) {
            const startDate = new Date(params.start_date)
            startDate.setHours(0, 0, 0, 0)
            history = history.filter(item => new Date(item.date) >= startDate)
        }

        if (params.end_date) {
            const endDate = new Date(params.end_date)
            endDate.setHours(23, 59, 59, 999)
            history = history.filter(item => new Date(item.date) <= endDate)
        }

        if (params.search_query) {
            const query = params.search_query.toLowerCase()
            history = history.filter(item =>
                (item.subject && item.subject.toLowerCase().includes(query)) ||
                (item.sender && item.sender.toLowerCase().includes(query))
            )
        }
    }

    return Promise.resolve(history)
}
