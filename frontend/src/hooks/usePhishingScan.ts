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
            setResult(response)
        } catch (err: any) {
            const errorMessage =
                err.response?.data?.detail ||
                err.message ||
                'Failed to analyze email. Please try again.'
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
