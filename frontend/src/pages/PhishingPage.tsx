import { EmailForm } from '../components/phishing/EmailForm'
import { PhishingResultCard } from '../components/phishing/PhishingResultCard'
import { Loader } from '../components/common/Loader'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { usePhishingScan } from '../hooks/usePhishingScan'
import './PhishingPage.css'

export function PhishingPage() {
    const { analyze, loading, error, result } = usePhishingScan()

    return (
        <div className="phishing-page">
            <div className="page-header">
                <h1>Phishing Email Detection</h1>
                <p>
                    Analyze email content to detect potential phishing attempts and
                    security threats
                </p>
            </div>

            <EmailForm onSubmit={analyze} loading={loading} />

            {loading && <Loader />}

            {error && <ErrorAlert message={error} />}

            {result && <PhishingResultCard result={result} />}
        </div>
    )
}
