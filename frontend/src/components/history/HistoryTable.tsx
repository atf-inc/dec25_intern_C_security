import { ScanHistoryItem } from '../../api/phishingApi'
import { RiskBadge } from '../common/RiskBadge'
import './HistoryComponents.css'

interface HistoryTableProps {
    data: ScanHistoryItem[]
    onViewDetails?: (id: number) => void
    onDelete?: (id: number) => void
}

export function HistoryTable({ data, onViewDetails, onDelete }: HistoryTableProps) {
    if (!data || data.length === 0) {
        return (
            <div className="empty-state">
                No scan history available.
            </div>
        )
    }

    return (
        <div className="table-container">
            <table className="history-table">
                <thead className="table-head">
                    <tr>
                        <th className="table-header-cell">Type</th>
                        <th className="table-header-cell">Date</th>
                        <th className="table-header-cell">Subject/File</th>
                        <th className="table-header-cell">Sender</th>
                        <th className="table-header-cell">Detection</th>
                        <th className="table-header-cell">Risk Level</th>
                        {/* <th className="table-header-cell">Score</th> Removed as it's in badge */}
                        <th className="table-header-cell">Actions</th>
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
                                <td className="table-cell">
                                    <span title={item.type === 'voice' ? 'Voice Scan' : 'Email Scan'}>
                                        {item.type === 'voice' ? '🎤' : '📧'}
                                    </span>
                                </td>
                                <td className="table-cell">{new Date(item.date).toLocaleDateString()}</td>
                                <td className="table-cell">{item.subject || 'N/A'}</td>
                                <td className="table-cell">{item.sender || 'N/A'}</td>
                                <td className="table-cell">
                                    {(() => {
                                        const raw = item.risk_level.toLowerCase();
                                        const isSafe = ['safe', 'low', 'clean', 'legit'].includes(raw);
                                        return (
                                            <span className={`detection-badge ${isSafe ? 'safe' : 'phishing'}`}>
                                                {isSafe ? '✅ Safe' : '⚠️ Phishing'}
                                            </span>
                                        );
                                    })()}
                                </td>
                                <td className="table-cell">
                                    <RiskBadge level={item.risk_level} score={item.risk_score} size="small" />
                                </td>
                                {/* Score is now included in RiskBadge */}
                                <td className="table-cell">
                                    <div className="action-buttons">
                                        <button
                                            onClick={() => onViewDetails?.(item.id)}
                                            className="action-btn btn-view"
                                        >
                                            View
                                        </button>
                                        <button
                                            onClick={() => onDelete?.(item.id)}
                                            className="action-btn btn-delete"
                                            title="Delete Scan"
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
