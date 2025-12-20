import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import './HistoryPage.css'
// Email Imports
import { getScanHistory, ScanHistoryItem, ScanHistoryParams } from '../api/phishingApi'
import { HistoryTable } from '../components/history/HistoryTable'
// New Imports
import { VirtualizedHistoryList } from '../components/history/VirtualizedHistoryList'
import { useMediaQuery } from '../hooks/useMediaQuery'

// Voice Imports
import { getVoiceHistory, VoiceAnalysisResponse, deleteScan } from '../api/voiceApi'
import { VoiceHistoryTable } from '../components/history/VoiceHistoryTable'

import { Suspense, lazy } from 'react'

// Lazy Load Chart to reduce initial bundle size
const HistoryChart = lazy(() => import('../components/history/HistoryChart').then(module => ({ default: module.HistoryChart })))
import { HistoryFilters } from '../components/history/HistoryFilters'
import { storage } from '../utils/storage'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { ConfirmationModal } from '../components/common/ConfirmationModal'
import { SkeletonCard } from '../components/common/SkeletonLoader'

type TabType = 'email' | 'voice'

export function HistoryPage() {
    const { t } = useTranslation()
    const isMobile = useMediaQuery('(max-width: 768px)')
    const [activeTab, setActiveTab] = useState<TabType>('email')
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Fallback function for translations
    const getText = (key: string, fallback: string) => {
        const translated = t(key)
        return translated === key ? fallback : translated
    }

    // Data States
    const [emailData, setEmailData] = useState<ScanHistoryItem[]>([])
    const [voiceData, setVoiceData] = useState<VoiceAnalysisResponse[]>([])

    const [filters, setFilters] = useState<ScanHistoryParams>({})

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [deleteTarget, setDeleteTarget] = useState<{ id: number, type: 'email' | 'voice' } | null>(null)

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
            setError(getText('dashboard.failedToLoadHistory', 'Failed to load scan history.'))
        } finally {
            setIsLoading(false)
        }
    }

    const handleEmailView = (id: number) => {
        window.location.href = `/phishing?historyId=${id}`
    }

    const handleVoiceView = (item: VoiceAnalysisResponse) => {
        if (item.id) {
            window.location.href = `/voice?id=${item.id}`
        }
    }

    const handleEmailDelete = (id: number) => {
        setDeleteTarget({ id, type: 'email' })
        setIsModalOpen(true)
    }

    const handleVoiceDelete = (id: number) => {
        setDeleteTarget({ id, type: 'voice' })
        setIsModalOpen(true)
    }

    const confirmDelete = async () => {
        if (!deleteTarget) return

        try {
            if (deleteTarget.type === 'email') {
                storage.deleteScan(deleteTarget.id)
            } else {
                await deleteScan(deleteTarget.id)
            }
            fetchData() // Refresh list
        } catch (err) {
            console.error('Delete failed', err)
            alert(getText('dashboard.failedToDelete', 'Failed to delete scan'))
        } finally {
            setIsModalOpen(false)
            setDeleteTarget(null)
        }
    }

    return (
        <div className="history-page">
            <div className="page-title-section">
                <h1 className="page-title">{getText('dashboard.pageTitle', 'Security Scan History')}</h1>
                <p className="page-description">{getText('dashboard.pageDescription', 'View and analyze past email and voice security scans.')}</p>
            </div>

            {/* Tab Navigation */}
            <div className="tabs-nav">
                <button
                    onClick={() => setActiveTab('email')}
                    className={`tab-button ${activeTab === 'email' ? 'active' : ''}`}
                >
                    📧 {getText('dashboard.emailScans', 'Email Scans')}
                </button>
                <button
                    onClick={() => setActiveTab('voice')}
                    className={`tab-button ${activeTab === 'voice' ? 'active' : ''}`}
                >
                    🎙️ {getText('dashboard.voiceScans', 'Voice Scans')}
                </button>
            </div>

            {error && <ErrorAlert message={error} />}

            {/* Only show Filters/Chart for Email tab currently as Voice stats are different */}
            {activeTab === 'email' && (
                <>
                    <div className="chart-section">
                        <Suspense fallback={<SkeletonCard />}>
                            <HistoryChart data={emailData} />
                        </Suspense>
                    </div>
                    <HistoryFilters filters={filters} onFilterChange={setFilters} />
                </>
            )}

            {activeTab === 'voice' && (
                <div className="chart-section">
                    <Suspense fallback={<SkeletonCard />}>
                        <HistoryChart title={getText('dashboard.deepfakeConfidenceTrend', 'Deepfake Confidence Trend')} data={voiceData.map(item => ({
                            id: item.id || 0,
                            date: item.created_at || new Date().toISOString(),
                            type: 'voice',
                            // Check range: if < 1 assume 0.0-1.0 and multiply by 100. If > 1 assume 0-100.
                            risk_score: item.confidence > 1 ? item.confidence : item.confidence * 100,
                            risk_level: item.risk_level,
                            subject: item.file_name, // Map filename to subject for the tooltip
                            sender: getText('history.voiceScan', 'Voice Scan') // Placeholder for sender
                        }))} />
                    </Suspense>
                </div>
            )}

            {isLoading ? (
                <div className="skeleton-grid">
                    {/* Render 6 skeletons grid/list based on view */}
                    {Array.from({ length: 6 }).map((_, i) => (
                        <div key={i} className="skeleton-wrapper" style={{ marginBottom: '1rem' }}>
                            <SkeletonCard />
                        </div>
                    ))}
                </div>
            ) : (
                <>
                    {activeTab === 'email' ? (
                        isMobile ? (
                            <VirtualizedHistoryList
                                data={emailData}
                                onViewDetails={handleEmailView}
                                onDelete={handleEmailDelete}
                                height={600}
                            />
                        ) : (
                            <HistoryTable
                                data={emailData}
                                onViewDetails={handleEmailView}
                                onDelete={handleEmailDelete}
                            />
                        )
                    ) : (
                        <VoiceHistoryTable
                            data={voiceData}
                            onViewDetails={handleVoiceView}
                            onDelete={handleVoiceDelete}
                        />
                    )}
                </>
            )}

            <ConfirmationModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onConfirm={confirmDelete}
                title={getText('dashboard.deleteScan', 'Delete Scan')}
                message={getText('dashboard.deleteScanConfirmation', 'Are you sure you want to delete this scan log? This action cannot be undone.')}
            />
        </div>
    )
}
