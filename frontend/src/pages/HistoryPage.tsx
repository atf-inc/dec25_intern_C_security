import { useState, useEffect } from 'react'
// Email Imports
import { getScanHistory, ScanHistoryItem, ScanHistoryParams } from '../api/phishingApi'
import { HistoryTable } from '../components/history/HistoryTable'
// Voice Imports
import { getVoiceHistory, VoiceAnalysisResponse, deleteScan } from '../api/voiceApi'
import { VoiceHistoryTable } from '../components/history/VoiceHistoryTable'

import { HistoryChart } from '../components/history/HistoryChart'
import { HistoryFilters } from '../components/history/HistoryFilters'
import { Loader } from '../components/common/Loader'
import { ErrorAlert } from '../components/common/ErrorAlert'

type TabType = 'email' | 'voice'

export function HistoryPage() {
    const [activeTab, setActiveTab] = useState<TabType>('email')
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    
    // Data States
    const [emailData, setEmailData] = useState<ScanHistoryItem[]>([])
    const [voiceData, setVoiceData] = useState<VoiceAnalysisResponse[]>([])
    
    const [filters, setFilters] = useState<ScanHistoryParams>({})

    useEffect(() => {
        fetchData()
    }, [activeTab, filters])

    const fetchData = async () => {
        setIsLoading(true)
        setError(null)
        try {
            if (activeTab === 'email') {
                const history = await getScanHistory(filters)
                setEmailData(history)
            } else {
                // Voice API doesn't support the same filters yet, so we pass default pagination
                const response = await getVoiceHistory(0, 100)
                setVoiceData(response.scans)
            }
        } catch (err) {
            console.error('Failed to fetch history:', err)
            setError('Failed to load scan history.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleEmailView = (id: number) => {
        window.location.href = `/phishing?historyId=${id}`
    }

    const handleVoiceView = (item: VoiceAnalysisResponse) => {
        // Assuming VoicePage can handle a query param or state to load a specific result
        // For now, we might just redirect to /voice, or you can implement a view mode there
        console.log("View voice scan:", item)
        // Implementation depend on VoicePage: window.location.href = `/voice?id=${item.id}`
    }

    const handleVoiceDelete = async (id: number) => {
        if(!confirm('Are you sure you want to delete this scan log?')) return;
        try {
            await deleteScan(id)
            fetchData() // Refresh list
        } catch (err) {
            alert('Failed to delete scan')
        }
    }

    return (
        <div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
            <div style={{ marginBottom: "2rem" }}>
                <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem", color: "#2c3e50" }}>Security Scan History</h1>
                <p style={{ color: "#7f8c8d" }}>View and analyze past email and voice security scans.</p>
            </div>

            {/* Tab Navigation */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', borderBottom: '1px solid #e5e7eb' }}>
                <button
                    onClick={() => setActiveTab('email')}
                    style={{
                        padding: '1rem 1.5rem',
                        border: 'none',
                        background: 'none',
                        borderBottom: activeTab === 'email' ? '2px solid #3b82f6' : '2px solid transparent',
                        color: activeTab === 'email' ? '#3b82f6' : '#64748b',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}
                >
                    📧 Email Scans
                </button>
                <button
                    onClick={() => setActiveTab('voice')}
                    style={{
                        padding: '1rem 1.5rem',
                        border: 'none',
                        background: 'none',
                        borderBottom: activeTab === 'voice' ? '2px solid #3b82f6' : '2px solid transparent',
                        color: activeTab === 'voice' ? '#3b82f6' : '#64748b',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}
                >
                    🎙️ Voice Scans
                </button>
            </div>

            {error && <ErrorAlert message={error} />}

            {/* Only show Filters/Chart for Email tab currently as Voice stats are different */}
            {activeTab === 'email' && (
                <>
                    <div style={{ marginBottom: "2rem" }}>
                        <HistoryChart data={emailData} />
                    </div>
                    <HistoryFilters filters={filters} onFilterChange={setFilters} />
                </>
            )}

            {isLoading ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                    <Loader />
                </div>
            ) : (
                <>
                    {activeTab === 'email' ? (
                        <HistoryTable data={emailData} onViewDetails={handleEmailView} />
                    ) : (
                        <VoiceHistoryTable 
                            data={voiceData} 
                            onViewDetails={handleVoiceView}
                            onDelete={handleVoiceDelete}
                        />
                    )}
                </>
            )}
        </div>
    )
}
