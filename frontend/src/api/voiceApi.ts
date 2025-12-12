import apiClient from './client'

export interface VoiceResponse {
    id?: number
    is_deepfake: boolean
    confidence: number
    risk_level: 'low' | 'medium' | 'high' | 'critical'
    explanation?: string
    created_at?: string
    file_name?: string
    duration?: number
}

export async function analyzeAudio(file: File): Promise<VoiceResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<VoiceResponse>('/api/v1/voice/analyze', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    })

    return response.data
}
