
import { ScanHistoryParams } from '../../api/phishingApi'

interface HistoryFiltersProps {
    filters: ScanHistoryParams
    onFilterChange: (newFilters: ScanHistoryParams) => void
}

export function HistoryFilters({ filters, onFilterChange }: HistoryFiltersProps) {
    const handleRiskChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        onFilterChange({ ...filters, risk_level: e.target.value || undefined })
    }

    // const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    //     // Implementation for date filtering
    // }

    return (
        <div style={{
            display: 'flex',
            gap: '1rem',
            marginBottom: '1.5rem',
            padding: '1rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px'
        }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label style={{ marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 600 }}>Filter by Risk</label>
                <select
                    value={filters.risk_level || ''}
                    onChange={handleRiskChange}
                    style={{
                        padding: '8px',
                        borderRadius: '4px',
                        border: '1px solid #ced4da',
                        minWidth: '150px'
                    }}
                >
                    <option value="">All Levels</option>
                    <option value="high">High Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="low">Low Risk</option>
                </select>
            </div>

            {/* Additional filters can go here */}
        </div>
    )
}
