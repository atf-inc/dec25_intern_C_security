
import { ScanHistoryItem } from '../../api/phishingApi'
import { RiskBadge } from '../common/RiskBadge'

interface HistoryTableProps {
    data: ScanHistoryItem[]
    onViewDetails?: (id: number) => void
}

export function HistoryTable({ data, onViewDetails }: HistoryTableProps) {
    if (!data || data.length === 0) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                No scan history available.
            </div>
        )
    }

    return (
        <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid #eee' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead style={{ backgroundColor: '#f8f9fa' }}>
                    <tr>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Date</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Subject/File</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Sender</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Risk Level</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Score</th>
                        <th style={{ padding: '12px', borderBottom: '1px solid #ddd' }}>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((item) => (
                        <tr key={item.id} style={{ borderBottom: '1px solid #eee' }}>
                            <td style={{ padding: '12px' }}>{new Date(item.date).toLocaleDateString()}</td>
                            <td style={{ padding: '12px' }}>{item.subject || 'N/A'}</td>
                            <td style={{ padding: '12px' }}>{item.sender || 'N/A'}</td>
                            <td style={{ padding: '12px' }}>
                                <RiskBadge level={item.risk_level} score={item.risk_score} />
                            </td>
                            <td style={{ padding: '12px' }}>{item.risk_score}</td>
                            <td style={{ padding: '12px' }}>
                                <button
                                    onClick={() => onViewDetails?.(item.id)}
                                    style={{
                                        padding: '6px 12px',
                                        backgroundColor: '#007bff',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '4px',
                                        cursor: 'pointer'
                                    }}
                                >
                                    View
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}
