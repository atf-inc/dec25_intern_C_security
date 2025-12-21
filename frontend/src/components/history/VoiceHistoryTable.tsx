import { useTranslation } from 'react-i18next'
import { VoiceAnalysisResponse } from '../../api/voiceApi'
import { RiskBadge } from '../common/RiskBadge'
import './HistoryComponents.css'

interface VoiceHistoryTableProps {
    data: VoiceAnalysisResponse[]
    onViewDetails?: (item: VoiceAnalysisResponse) => void
    onDelete?: (id: number) => void
}

export function VoiceHistoryTable({ data, onViewDetails, onDelete }: VoiceHistoryTableProps) {
    const { t } = useTranslation()

    // Fallback function for translations
    const getText = (key: string, fallback: string) => {
        const translated = t(key)
        return translated === key ? fallback : translated
    }

    if (!data || data.length === 0) {
        return (
            <div className="empty-state">
                {getText('history.noVoiceScanHistory', 'No voice scan history available.')}
            </div>
        )
    }

    return (
        <div className="table-container">
            <table className="history-table">
                <thead className="table-head">
                    <tr>
                        <th className="table-header-cell">{getText('history.date', 'Date')}</th>
                        <th className="table-header-cell">{getText('history.fileName', 'File Name')}</th>
                        <th className="table-header-cell">{getText('history.duration', 'Duration')}</th>
                        <th className="table-header-cell">{getText('history.detection', 'Detection')}</th>
                        <th className="table-header-cell">{getText('history.riskLevel', 'Risk Level')}</th>
                        {/* <th className="table-header-cell">Confidence</th> In badge */}
                        <th className="table-header-cell">{getText('history.actions', 'Actions')}</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((item) => (
                        <tr key={item.id} className="table-row" data-risk={item.risk_level.toLowerCase()}>
                            <td className="table-cell">
                                {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                            </td>
                            <td className="table-cell">
                                <div className="file-cell">
                                    <span>🎵</span>
                                    {item.file_name}
                                </div>
                            </td>
                            <td className="table-cell">{item.duration.toFixed(1)}s</td>
                            <td className="table-cell">
                                <span className={`detection-badge ${item.is_deepfake ? 'deepfake' : 'real'}`}>
                                    {item.is_deepfake ? `⚠️ ${getText('history.deepfake', 'Deepfake')}` : `✅ ${getText('history.real', 'Real')}`}
                                </span>
                            </td>
                            <td className="table-cell">
                                <RiskBadge level={item.risk_level} score={Math.round(item.confidence * 100)} size="small" />
                            </td>
                            {/* Confidence is now in RiskBadge */}
                            <td className="table-cell">
                                <div className="action-buttons">
                                    <button
                                        onClick={() => onViewDetails?.(item)}
                                        className="action-btn btn-view"
                                    >
                                        {getText('history.view', 'View')}
                                    </button>
                                    {onDelete && (
                                        <button
                                            onClick={() => item.id && onDelete(item.id)}
                                            className="action-btn btn-delete"
                                            title={getText('history.deleteScanTitle', 'Delete Scan')}
                                        >
                                            🗑️
                                        </button>
                                    )}
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}