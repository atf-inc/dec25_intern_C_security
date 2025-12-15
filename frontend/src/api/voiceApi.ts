import axios from 'axios'

const API_BASE_URL = '/api/v1'

export interface VoiceAnalysisResponse {
    file_name: string
    file_hash: string
    file_size: number
    duration: number
    is_deepfake: boolean
    confidence: number
    risk_level: 'low' | 'medium' | 'high'
    raw_model_confidence?: number
    artifact_score?: number
    artifacts?: {
        spectral_flatness: number
        autocorr_peak: number
        high_freq_energy: number
        zcr_variance: number
    }
    explanation?: string
    highlights?: string[]
    processing_time: number
    model_version: string
    cached: boolean
    id?: number
    created_at?: string
    audio_url?: string
}

export interface VoiceHistoryResponse {
    total: number
    scans: VoiceAnalysisResponse[]
}

export interface VoiceStatistics {
    total_scans: number
    deepfake_count: number
    real_count: number
    high_risk_count: number
    deepfake_percentage: number
}

export interface ModelInfo {
    model_version: string
    base_model: string
    framework: string
    device: string
    trained: boolean
}

/**
 * Analyze voice file for deepfake detection
 */
export async function analyzeVoice(
    file: File,
    includeExplanation: boolean = true
): Promise<VoiceAnalysisResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('include_explanation', String(includeExplanation))

    try {
        const response = await axios.post<VoiceAnalysisResponse>(
            `${API_BASE_URL}/voice/analyze`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                // Increase timeout for large files
                timeout: 60000, // 60 seconds
            }
        )
        return response.data
    } catch (error: any) {
        if (error.response) {
            // Server responded with error
            throw new Error(error.response.data.detail || 'Analysis failed')
        } else if (error.request) {
            // Request made but no response
            throw new Error('No response from server. Please check your connection.')
        } else {
            // Something else happened
            throw new Error(error.message || 'Failed to analyze voice')
        }
    }
}

/**
 * Get analysis history
 */
export async function getVoiceHistory(
    skip: number = 0,
    limit: number = 50
): Promise<VoiceHistoryResponse> {
    const response = await axios.get<VoiceHistoryResponse>(
        `${API_BASE_URL}/voice/history`,
        { params: { skip, limit } }
    )
    return response.data
    return response.data
}

/**
 * Get specific voice scan by ID
 */
export async function getVoiceScan(scanId: number): Promise<VoiceAnalysisResponse> {
    const response = await axios.get<VoiceAnalysisResponse>(
        `${API_BASE_URL}/voice/scan/${scanId}`
    )
    return response.data
}

/**
 * Get voice scan statistics
 */
export async function getVoiceStatistics(): Promise<VoiceStatistics> {
    const response = await axios.get<VoiceStatistics>(
        `${API_BASE_URL}/voice/statistics`
    )
    return response.data
}

/**
 * Get model information
 */
export async function getModelInfo(): Promise<ModelInfo> {
    const response = await axios.get<ModelInfo>(
        `${API_BASE_URL}/voice/model-info`
    )
    return response.data
}

/**
 * Delete a scan from history
 */
export async function deleteScan(scanId: number): Promise<void> {
    await axios.delete(`${API_BASE_URL}/voice/scan/${scanId}`)
}
