// import { CSSProperties } from 'react';
// import * as ReactWindow from 'react-window'; // Disabled due to Vite import issues
import { useTranslation } from 'react-i18next';
import { ScanHistoryItem } from '../../api/phishingApi';
import { RiskBadge } from '../common/RiskBadge';
import './HistoryComponents.css';

interface VirtualizedHistoryListProps {
    data: ScanHistoryItem[];
    onViewDetails?: (id: number) => void;
    onDelete?: (id: number) => void;
    height?: number;
}

export function VirtualizedHistoryList({ data, onViewDetails, onDelete, height = 600 }: VirtualizedHistoryListProps) {
    const { t } = useTranslation();

    // Standard list rendering fallback
    return (
        <div
            className="virtualized-list-container"
            style={{ height: height, overflowY: 'auto', width: '100%' }}
        >
            <div className="virtual-list-content">
                {data.map((item) => (
                    <div key={item.id} className="virtual-list-row-wrapper">
                        <div className="history-card-item">
                            <div className="history-card-header">
                                <div className="history-card-type">
                                    <span className="type-icon">{item.type === 'voice' ? '🎤' : '📧'}</span>
                                    <span className="history-date">{new Date(item.date).toLocaleDateString()}</span>
                                </div>
                                <RiskBadge level={item.risk_level} score={item.risk_score} size="small" />
                            </div>

                            <div className="history-card-body">
                                <div className="history-subject">{item.subject || t('history.noSubject', 'No Subject')}</div>
                                <div className="history-sender">{item.sender || t('history.unknownSender', 'Unknown Sender')}</div>
                            </div>

                            <div className="history-card-actions">
                                <button
                                    onClick={() => onViewDetails?.(item.id)}
                                    className="action-btn btn-view"
                                >
                                    {t('history.view', 'View')}
                                </button>
                                <button
                                    onClick={() => onDelete?.(item.id)}
                                    className="action-btn btn-delete"
                                >
                                    🗑️
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
                {data.length === 0 && (
                    <div className="empty-state" style={{ margin: '1rem', textAlign: 'center' }}>
                        {t('history.noScanHistory', 'No scan history available.')}
                    </div>
                )}
            </div>
        </div>
    );
}
