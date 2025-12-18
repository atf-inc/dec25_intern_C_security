import { Routes, Route, Navigate } from 'react-router-dom'
import { PhishingPage } from '../pages/PhishingPage'
import { VoicePage } from '../pages/VoicePage'
import { HistoryPage } from '../pages/HistoryPage'

export function AppRouter() {
    return (
        <Routes>
            <Route path="/" element={<Navigate to="/phishing" replace />} />
            <Route path="/phishing" element={<PhishingPage />} />
            <Route path="/voice" element={<VoicePage />} />
            <Route path="/history" element={<HistoryPage />} />
        </Routes>
    )
}