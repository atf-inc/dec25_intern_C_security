import { VoiceAnalysisResponse } from '../../api/voiceApi'
import { RiskBadge } from '../common/RiskBadge'
import './HistoryComponents.css'

interface VoiceHistoryTableProps {
    data: VoiceAnalysisResponse[]
    onViewDetails?: (item: VoiceAnalysisResponse) => void
    onDelete?: (id: number) => void
}

export function VoiceHistoryTable({ data, onViewDetails, onDelete }: VoiceHistoryTableProps) {
    if (!data || data.length === 0) {
        return (
            <div className="empty-state">
                No voice scan history available.
            </div>
        )
    }

    return (
        <div className="table-container">
            <table className="history-table">
                <thead className="table-head">
                    <tr>
                        <th className="table-header-cell">Date</th>
                        <th className="table-header-cell">File Name</th>
                        <th className="table-header-cell">Duration</th>
                        <th className="table-header-cell">Detection</th>
                        <th className="table-header-cell">Risk Level</th>
                        {/* <th className="table-header-cell">Confidence</th> In badge */}
                        <th className="table-header-cell">Actions</th>
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
                                    {item.is_deepfake ? '⚠️ Deepfake' : '✅ Real'}
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
                                        View
                                    </button>
                                    {onDelete && (
                                        <button
                                            onClick={() => item.id && onDelete(item.id)}
                                            className="action-btn btn-delete"
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
