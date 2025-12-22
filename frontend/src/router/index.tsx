import { Routes, Route } from 'react-router-dom'
import { Suspense, lazy } from 'react'

// 🚀 Lazy load pages for better performance (code splitting)
const HomePage = lazy(() => import('../pages/HomePage').then(m => ({ default: m.HomePage })))
const PhishingPage = lazy(() => import('../pages/PhishingPage').then(m => ({ default: m.PhishingPage })))
const VoicePage = lazy(() => import('../pages/VoicePage').then(m => ({ default: m.VoicePage })))
const HistoryPage = lazy(() => import('../pages/HistoryPage').then(m => ({ default: m.HistoryPage })))

// Loading fallback
function PageLoader() {
    return (
        <div className="page-loader" style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '50vh',
            fontSize: '1.25rem',
            color: 'var(--text-secondary)'
        }}>
            <div className="loader-spinner" />
        </div>
    )
}

export function AppRouter() {
    return (
        <Suspense fallback={<PageLoader />}>
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/phishing" element={<PhishingPage />} />
                <Route path="/voice" element={<VoicePage />} />
                <Route path="/history" element={<HistoryPage />} />
            </Routes>
        </Suspense>
    )
}