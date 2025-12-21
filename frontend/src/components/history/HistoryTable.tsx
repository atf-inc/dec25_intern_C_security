import { useTranslation } from 'react-i18next'
import { ScanHistoryItem } from '../../api/phishingApi'
import { RiskBadge } from '../common/RiskBadge'
import './HistoryComponents.css'

interface HistoryTableProps {
    data: ScanHistoryItem[]
    onViewDetails?: (id: number) => void
    onDelete?: (id: number) => void
}

export function HistoryTable({ data, onViewDetails, onDelete }: HistoryTableProps) {
    const { t } = useTranslation()

    // Fallback function for translations
    const getText = (key: string, fallback: string) => {
        const translated = t(key)
        return translated === key ? fallback : translated
    }

    if (!data || data.length === 0) {
        return (
            <div className="empty-state">
                {getText('history.noScanHistory', 'No scan history available.')}
            </div>
        )
    }

    return (
        <div className="table-container">
            <table className="history-table">
                <thead className="table-head">
                    <tr>
                        <th className="table-header-cell">{getText('history.type', 'Type')}</th>
                        <th className="table-header-cell">{getText('history.date', 'Date')}</th>
                        <th className="table-header-cell">{getText('history.subjectFile', 'Subject/File')}</th>
                        <th className="table-header-cell">{getText('history.sender', 'Sender')}</th>
                        <th className="table-header-cell">{getText('history.detection', 'Detection')}</th>
                        <th className="table-header-cell">{getText('history.riskLevel', 'Risk Level')}</th>
                        {/* <th className="table-header-cell">Score</th> Removed as it's in badge */}
                        <th className="table-header-cell">{getText('history.actions', 'Actions')}</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((item) => {
                        const normalizeRisk = (r: string) => {
                            const l = r.toLowerCase();
                            if (['safe', 'low'].includes(l)) return 'low';
                            if (['suspicious', 'medium'].includes(l)) return 'medium';
                            return 'high';
                        };
                        const riskStyle = normalizeRisk(item.risk_level);

                        return (
                            <tr key={item.id} className="table-row" data-risk={riskStyle}>
                                <td className="table-cell" data-label={getText('history.type', 'Type')}>
                                    <span title={item.type === 'voice' ? getText('history.voiceScan', 'Voice Scan') : getText('history.emailScan', 'Email Scan')}>
                                        {item.type === 'voice' ? '🎤' : '📧'}
                                    </span>
                                </td>
                                <td className="table-cell" data-label={getText('history.date', 'Date')}>{new Date(item.date).toLocaleDateString()}</td>
                                <td className="table-cell" data-label={getText('history.subjectFile', 'Subject/File')}>{item.subject || 'N/A'}</td>
                                <td className="table-cell" data-label={getText('history.sender', 'Sender')}>{item.sender || 'N/A'}</td>
                                <td className="table-cell" data-label={getText('history.detection', 'Detection')}>
                                    {(() => {
                                        const raw = item.risk_level.toLowerCase();
                                        const isSafe = ['safe', 'low', 'clean', 'legit'].includes(raw);
                                        return (
                                            <span className={`detection-badge ${isSafe ? 'safe' : 'phishing'}`}>
                                                {isSafe ? `✅ ${getText('history.safe', 'Safe')}` : `⚠️ ${getText('history.phishing', 'Phishing')}`}
                                            </span>
                                        );
                                    })()}
                                </td>
                                <td className="table-cell" data-label={getText('history.riskLevel', 'Risk')}>
                                    <RiskBadge level={item.risk_level} score={item.risk_score} size="small" />
                                </td>
                                {/* Score is now included in RiskBadge */}
                                <td className="table-cell" data-label={getText('history.actions', 'Actions')}>
                                    <div className="action-buttons">
                                        <button
                                            onClick={() => onViewDetails?.(item.id)}
                                            className="action-btn btn-view"
                                            aria-label={getText('history.view', 'View')}
                                        >
                                            {getText('history.view', 'View')}
                                        </button>
                                        <button
                                            onClick={() => onDelete?.(item.id)}
                                            className="action-btn btn-delete"
                                            title={getText('history.deleteScanTitle', 'Delete Scan')}
                                            aria-label={getText('history.deleteScanTitle', 'Delete Scan')}
                                        >
                                            🗑️
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    )
}