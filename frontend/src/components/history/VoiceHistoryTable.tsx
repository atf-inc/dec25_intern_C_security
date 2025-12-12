import { VoiceAnalysisResponse } from '../../api/voiceApi'
import { RiskBadge } from '../common/RiskBadge'

interface VoiceHistoryTableProps {
    data: VoiceAnalysisResponse[]
    onViewDetails?: (item: VoiceAnalysisResponse) => void
    onDelete?: (id: number) => void
}

export function VoiceHistoryTable({ data, onViewDetails, onDelete }: VoiceHistoryTableProps) {
    if (!data || data.length === 0) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                No voice scan history available.
            </div>
        )
    }

    return (
        <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid #eee' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead style={{ backgroundColor: '#f8f9fa' }}>
                    <tr>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Date</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>File Name</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Duration</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Detection</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Risk Level</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Confidence</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((item) => (
                        <tr key={item.id} style={{ borderBottom: '1px solid #eee' }}>
                            <td style={{ padding: '12px' }}>
                                {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                            </td>
                            <td style={{ padding: '12px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <span>🎵</span>
                                    {item.file_name}
                                </div>
                            </td>
                            <td style={{ padding: '12px' }}>{item.duration.toFixed(1)}s</td>
                            <td style={{ padding: '12px' }}>
                                <span style={{
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                    fontSize: '0.85rem',
                                    backgroundColor: item.is_deepfake ? '#fee2e2' : '#dcfce7',
                                    color: item.is_deepfake ? '#991b1b' : '#166534',
                                    fontWeight: 500
                                }}>
                                    {item.is_deepfake ? '⚠️ Deepfake' : '✅ Real'}
                                </span>
                            </td>
                            <td style={{ padding: '12px' }}>
                                <RiskBadge level={item.risk_level} score={Math.round(item.confidence * 100)} />
                            </td>
                            <td style={{ padding: '12px' }}>
                                {(item.confidence * 100).toFixed(1)}%
                            </td>
                            <td style={{ padding: '12px' }}>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button
                                        onClick={() => onViewDetails?.(item)}
                                        style={{
                                            padding: '6px 12px',
                                            backgroundColor: '#3b82f6',
                                            color: 'white',
                                            border: 'none',
                                            borderRadius: '4px',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        View
                                    </button>
                                    {onDelete && (
                                        <button
                                            onClick={() => item.id && onDelete(item.id)}
                                            style={{
                                                padding: '6px 12px',
                                                backgroundColor: '#ef4444',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '4px',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            Delete
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
