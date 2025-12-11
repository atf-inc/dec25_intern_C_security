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
        return response.data
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
        return response.data
    }
}
