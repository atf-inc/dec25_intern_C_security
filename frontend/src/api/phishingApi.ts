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
    suggested_reply?: string
    model_meta?: any
}

export async function analyzeEmail(data: EmailAnalysisRequest): Promise<PhishingResponse> {
    console.log('analyzeEmail called with data:', data)
    console.log('pdfFile:', data.pdfFile)
    console.log('pdfFile type:', typeof data.pdfFile)
    console.log('pdfFile instanceof File:', data.pdfFile instanceof File)

    // If file is provided (EML or PDF), use multipart/form-data with upload endpoints first
    if (data.pdfFile) {
        console.log('Creating FormData for file upload...')
        console.log('File details:', {
            name: data.pdfFile.name,
            size: data.pdfFile.size,
            type: data.pdfFile.type,
            lastModified: data.pdfFile.lastModified
        })

        // Validate file size
        if (data.pdfFile.size === 0) {
            throw new Error('Selected file is empty (0 bytes). Please select a valid file.')
        }

        const formData = new FormData()
        formData.append('file', data.pdfFile, data.pdfFile.name)

        console.log('FormData created, file appended:', data.pdfFile.name, data.pdfFile.size, 'bytes')

        // Determine endpoint based on file type
        const isEmlFile = data.pdfFile.name.toLowerCase().endsWith('.eml')
        const isPdfFile = data.pdfFile.type === 'application/pdf' || data.pdfFile.name.toLowerCase().endsWith('.pdf')

        let uploadEndpoint: string
        if (isEmlFile) {
            uploadEndpoint = '/upload/eml'
        } else if (isPdfFile) {
            uploadEndpoint = '/upload/pdf'
        } else {
            throw new Error('Unsupported file type. Please upload EML or PDF files only.')
        }

        console.log('Using upload endpoint:', uploadEndpoint)

        // First upload and extract the file content
        const uploadResponse = await apiClient.post<any>(
            uploadEndpoint,
            formData
            // Note: Don't set any headers - the interceptor will handle Content-Type properly
        )

        // Then analyze using the extracted content with Akash's /analyze endpoint
        const analyzeRequest = {
            subject: uploadResponse.data.subject || '',
            from_email: uploadResponse.data.from_email || '',
            raw_text: uploadResponse.data.raw_text || '',
            visible_links: uploadResponse.data.visible_links || [],
            hidden_links: uploadResponse.data.hidden_links || [],
            meta: {
                consent: true  // Required by Akash's endpoint
            }
        }

        const response = await apiClient.post<PhishingResponse>('/analyze/', analyzeRequest)
        return response.data
    } else {
        // Regular JSON request for manual input using Akash's /analyze endpoint
        const requestData = {
            subject: data.subject,
            from_email: data.sender,
            raw_text: data.body,
            visible_links: data.urls?.map(url => ({
                uri: url,
                anchor_text: url
            })) || [],
            meta: {
                consent: true  // Required by Akash's endpoint
            }
        }

        const response = await apiClient.post<PhishingResponse>('/analyze/', requestData)
        return response.data
    }
}
