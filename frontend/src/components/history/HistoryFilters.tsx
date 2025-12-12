
import { ScanHistoryParams } from '../../api/phishingApi'

interface HistoryFiltersProps {
    filters: ScanHistoryParams
    onFilterChange: (newFilters: ScanHistoryParams) => void
}

export function HistoryFilters({ filters, onFilterChange }: HistoryFiltersProps) {
    const handleRiskChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        onFilterChange({ ...filters, risk_level: e.target.value || undefined })
    }

    const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onFilterChange({ ...filters, start_date: e.target.value || undefined })
    }

    const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onFilterChange({ ...filters, end_date: e.target.value || undefined })
    }

    return (
        <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '1.5rem',
            marginBottom: '1.5rem',
            padding: '1.5rem',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
            border: '1px solid #eee',
            alignItems: 'flex-end'
        }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#4a5568' }}>Risk Level</label>
                <select
                    value={filters.risk_level || ''}
                    onChange={handleRiskChange}
                    style={{
                        padding: '10px 12px',
                        borderRadius: '6px',
                        border: '1px solid #e2e8f0',
                        minWidth: '160px',
                        backgroundColor: '#fff',
                        fontSize: '0.95rem',
                        cursor: 'pointer'
                    }}
                >
                    <option value="">All Levels</option>
                    <option value="high">High Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="low">Low Risk</option>
                </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#4a5568' }}>Start Date</label>
                <input
                    type="date"
                    value={filters.start_date || ''}
                    onChange={handleStartDateChange}
                    style={{
                        padding: '9px 12px',
                        borderRadius: '6px',
                        border: '1px solid #e2e8f0',
                        minWidth: '160px',
                        backgroundColor: '#fff',
                        fontSize: '0.95rem',
                        fontFamily: 'inherit'
                    }}
                />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#4a5568' }}>End Date</label>
                <input
                    type="date"
                    value={filters.end_date || ''}
                    onChange={handleEndDateChange}
                    style={{
                        padding: '9px 12px',
                        borderRadius: '6px',
                        border: '1px solid #e2e8f0',
                        minWidth: '160px',
                        backgroundColor: '#fff',
                        fontSize: '0.95rem',
                        fontFamily: 'inherit'
                    }}
                />
            </div>

            {(filters.risk_level || filters.start_date || filters.end_date) && (
                <button
                    onClick={() => onFilterChange({})}
                    style={{
                        padding: '10px 16px',
                        borderRadius: '6px',
                        border: '1px solid #cbd5e0',
                        backgroundColor: '#fff',
                        color: '#4a5568',
                        cursor: 'pointer',
                        fontWeight: 500,
                        fontSize: '0.95rem',
                        transition: 'all 0.2s',
                        marginBottom: '1px'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f7fafc'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#fff'}
                >
                    Clear Filters
                </button>
            )}
        </div>
    )
}
