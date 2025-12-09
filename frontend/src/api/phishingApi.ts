import apiClient from './client'

export interface EmailAnalysisRequest {
    subject: string
    body: string
    sender: string
    urls?: string[]
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
    const response = await apiClient.post<PhishingResponse>('/api/v1/phishing/analyze', data)
    return response.data
}
