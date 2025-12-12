import { useState } from 'react'
import { analyzeEmail, PhishingResponse, EmailAnalysisRequest } from '../api/phishingApi'

export function usePhishingScan() {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [result, setResult] = useState<PhishingResponse | null>(null)

    const analyze = async (data: EmailAnalysisRequest) => {
        setLoading(true)
        setError(null)
        setResult(null)

        try {
            const response = await analyzeEmail(data)
            console.log('Analysis response:', response)

            // Ensure we have a valid response object
            if (response && typeof response === 'object' && response.request_id) {
                // Validate that all required fields are safe for React rendering
                const validatedResponse = {
                    ...response,
                    reasons: Array.isArray(response.reasons) ? response.reasons.filter(r => typeof r === 'string') : [],
                    evidence: Array.isArray(response.evidence) ? response.evidence : [],
                    suggested_action: typeof response.suggested_action === 'string' ? response.suggested_action : undefined,
                    suggested_reply: typeof response.suggested_reply === 'string' ? response.suggested_reply : undefined,
                    model_meta: response.model_meta && typeof response.model_meta === 'object' ? response.model_meta : {}
                }
                setResult(validatedResponse)
            } else {
                throw new Error('Invalid response format from server')
            }
        } catch (err: any) {
            console.error('Analysis error:', err)
            console.error('Error response:', err.response)
            console.error('Error data:', err.response?.data)

            let errorMessage: string

            if (err.response?.data?.detail) {
                // Backend validation error
                errorMessage = typeof err.response.data.detail === 'string'
                    ? err.response.data.detail
                    : `Server validation error: ${JSON.stringify(err.response.data.detail)}`
            } else if (err.response?.data) {
                // Other backend error
                errorMessage = `Server error: ${JSON.stringify(err.response.data)}`
            } else if (err.message) {
                // Network or other error
                errorMessage = err.message
            } else if (typeof err === 'string') {
                // String error
                errorMessage = err
            } else {
                // Unknown error object
                errorMessage = 'Failed to analyze email. Please try again.'
            }

            setError(errorMessage)
        } finally {
            setLoading(false)
        }
    }

    const reset = () => {
        setLoading(false)
        setError(null)
        setResult(null)
    }

    return { analyze, loading, error, result, reset, setResult }
}
