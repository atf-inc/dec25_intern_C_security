import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { storage } from '../utils/storage'
import { EmailForm } from '../components/phishing/EmailForm'
import { PhishingResultCard } from '../components/phishing/PhishingResultCard'
import { ErrorAlert } from '../components/common/ErrorAlert'

import { ForensicScanner } from '../components/common/ForensicScanner'
import { usePhishingScan } from '../hooks/usePhishingScan'
import './PhishingPage.css'

export function PhishingPage() {
    const { analyze, loading, error, result, setResult } = usePhishingScan()
    const { t, i18n } = useTranslation()
    const [searchParams] = useSearchParams()
    const [initialData, setInitialData] = useState<
        { subject: string; body: string; sender: string } | undefined
    >(undefined)

    useEffect(() => {
        const historyId = searchParams.get('historyId')
        if (historyId) {
            const scan = storage.getScanById(Number(historyId))
            if (scan) {
                if (scan.analysis_result) {
                    setResult(scan.analysis_result)
                }
                if (scan.original_input) {
                    setInitialData(scan.original_input)
                }
            }
        }
    }, [searchParams])

    return (
        <div className="phishing-page">
            <div className="page-header">
                <h1>{t('phishing.title')}</h1>
                <p>
                    {i18n.language === 'ja'
                        ? 'メールコンテンツを分析して、潜在的なフィッシング攻撃やセキュリティ脅威を検出します'
                        : 'Analyze email content to detect potential phishing attempts and security threats'
                    }
                </p>
            </div>

            <EmailForm
                onSubmit={(data) => analyze({ ...data, language: i18n.language })}
                loading={loading}
                initialData={initialData}
            />

            {loading && <ForensicScanner />}

            {error && <ErrorAlert message={error} />}
            {result && <PhishingResultCard result={result} />}
        </div>
    )
}
