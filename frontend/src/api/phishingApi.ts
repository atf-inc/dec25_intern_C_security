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
        return response.data
    } else {
        // Regular JSON request for manual input
        const response = await apiClient.post<PhishingResponse>('/api/v1/phishing/analyze', data)
        return response.data
    }
}
