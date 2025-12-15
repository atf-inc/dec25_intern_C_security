import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { storage } from '../utils/storage'
import { EmailForm } from '../components/phishing/EmailForm'
import { PhishingResultCard } from '../components/phishing/PhishingResultCard'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { ForensicScanner } from '../components/common/ForensicScanner'
import { SkeletonResultCard } from '../components/common/SkeletonLoader'
import { usePhishingScan } from '../hooks/usePhishingScan'
import './PhishingPage.css'

export function PhishingPage() {
    const { analyze, loading, error, result, setResult } = usePhishingScan()
    const [searchParams] = useSearchParams()
    const [initialData, setInitialData] = useState<{ subject: string; body: string; sender: string } | undefined>(undefined)

    useEffect(() => {
        const historyId = searchParams.get('historyId')
        if (historyId) {
            const scan = storage.getScanById(Number(historyId))
            if (scan) {
                // Restore result view
                if (scan.analysis_result) {
                    setResult(scan.analysis_result)
                }
                // Restore form inputs
                if (scan.original_input) {
                    setInitialData(scan.original_input)
                }
            }
        }
    }, [searchParams])

    return (
        <div className="phishing-page">
            <div className="page-header">
                <div className="header-content">
                    <div>
                        <h1>Phishing Email Detection</h1>
                        <p>
                            Analyze email content to detect potential phishing attempts and
                            security threats
                        </p>
                    </div>
                </div>
            </div>

            <EmailForm onSubmit={analyze} loading={loading} initialData={initialData} />

            {loading && (
                <>
                    <ForensicScanner />
                    <SkeletonResultCard />
                </>
            )}

            {error && <ErrorAlert message={error} />}

            {result && <PhishingResultCard result={result} />}
        </div>
    )
}
