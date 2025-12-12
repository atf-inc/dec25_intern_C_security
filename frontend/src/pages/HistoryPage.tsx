import { useState, useEffect } from 'react'
import { getScanHistory, ScanHistoryItem, ScanHistoryParams } from '../api/phishingApi'
import { HistoryTable } from '../components/history/HistoryTable'
import { HistoryChart } from '../components/history/HistoryChart'
import { HistoryFilters } from '../components/history/HistoryFilters'
import { Loader } from '../components/common/Loader'
import { ErrorAlert } from '../components/common/ErrorAlert'

export function HistoryPage() {
    const [data, setData] = useState<ScanHistoryItem[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [filters, setFilters] = useState<ScanHistoryParams>({})

    useEffect(() => {
        fetchHistory()
    }, [filters])

    const fetchHistory = async () => {
        setIsLoading(true)
        setError(null)
        try {
            const history = await getScanHistory(filters)
            setData(history)
        } catch (err) {
            console.error('Failed to fetch history:', err)
            setError('Failed to load scan history.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleViewDetails = (id: number) => {
        // Navigate to the Phishing page with the historyId
        window.location.href = `/phishing?historyId=${id}`
    }

    return (
        <div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
            <div style={{ marginBottom: "2rem" }}>
                <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem", color: "#2c3e50" }}>Scan History</h1>
                <p style={{ color: "#7f8c8d" }}>View and analyze past security scan results.</p>
            </div>

            {error && <ErrorAlert message={error} />}

            <div style={{ marginBottom: "2rem" }}>
                <HistoryChart data={data} />
            </div>

            <HistoryFilters filters={filters} onFilterChange={setFilters} />

            {isLoading ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                    <Loader />
                </div>
            ) : (
                <HistoryTable data={data} onViewDetails={handleViewDetails} />
            )}
        </div>
    )
}
