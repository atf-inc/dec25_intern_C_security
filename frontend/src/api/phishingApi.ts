
import apiClient from './client'
import { storage } from '../utils/storage'

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
    // If file is provided (EML or PDF), first upload to parse, then analyze
    let requestData: any;

    if (data.pdfFile) {
        const formData = new FormData()
        formData.append('file', data.pdfFile)

        // Determine endpoint based on file type
        const isEmlFile = data.pdfFile.name.endsWith('.eml')
        const isPdfFile = data.pdfFile.type === 'application/pdf'

        let uploadEndpoint: string
        if (isEmlFile) {
            uploadEndpoint = '/api/v1/upload/eml'
        } else if (isPdfFile) {
            uploadEndpoint = '/api/v1/upload/pdf'
        } else {
            throw new Error('Unsupported file type. Please upload EML or PDF files only.')
        }

        // Step 1: Upload and parse file
        const uploadResponse = await apiClient.post<any>( // Returns UploadPreview
            uploadEndpoint,
            formData
        )
        const parsed = uploadResponse.data

        // Step 2: Prepare data for analysis
        requestData = {
            subject: parsed.subject,
            from_email: parsed.from_email,
            raw_text: parsed.raw_text,
            visible_links: parsed.visible_links?.map((url: string) => ({
                uri: url,
                anchor_text: url
            })) || [],
            // Fallback for manual inputs if parsing failed to get them but they were somehow provided?
            // For now, we trust the parser output.
        }

    } else {
        // Regular manual input
        requestData = {
            subject: data.subject,
            from_email: data.sender,
            raw_text: data.body,
            visible_links: data.urls?.map(url => ({
                uri: url,
                anchor_text: url
            })) || []
        }
    }

    // Step 3: Perform Analysis
    const response = await apiClient.post<PhishingResponse>('/api/v1/phishing/analyze', requestData)
    const result = response.data

    saveToHistory(result, requestData.subject || 'No Subject', requestData.from_email || 'Unknown Sender', requestData.raw_text || '')

    return result
}

// Helper to save history
function saveToHistory(response: PhishingResponse, subject: string, sender: string, body: string) {
    const historyItem: ScanHistoryItem = {
        id: Date.now(), // Use timestamp for local ID
        date: new Date().toISOString(), // Use current time
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
