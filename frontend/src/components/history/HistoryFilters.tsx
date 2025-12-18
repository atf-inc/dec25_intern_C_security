import { ScanHistoryParams } from '../../api/phishingApi'
import './HistoryFilters.css'

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

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onFilterChange({ ...filters, search_query: e.target.value || undefined })
    }

    return (
        <div className="history-filters">
            <div className="filter-group search-group">
                <label className="filter-label">Search</label>
                <input
                    type="text"
                    className="filter-input search-input"
                    value={filters.search_query || ''}
                    onChange={handleSearchChange}
                    placeholder="Search by subject or sender..."
                />
            </div>

            <div className="filter-group">
                <label className="filter-label">Risk Level</label>
                <select
                    className="filter-select risk-select"
                    value={filters.risk_level || ''}
                    onChange={handleRiskChange}
                >
                    <option value="">All Levels</option>
                    <option value="high">High Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="low">Low Risk</option>
                </select>
            </div>

            <div className="filter-group">
                <label className="filter-label">Start Date</label>
                <input
                    type="date"
                    className="filter-input date-input"
                    value={filters.start_date || ''}
                    onChange={handleStartDateChange}
                />
            </div>

            <div className="filter-group">
                <label className="filter-label">End Date</label>
                <input
                    type="date"
                    className="filter-input date-input"
                    value={filters.end_date || ''}
                    onChange={handleEndDateChange}
                />
            </div>

            {(filters.risk_level || filters.start_date || filters.end_date || filters.search_query) && (
                <button
                    className="clear-filters-btn"
                    onClick={() => onFilterChange({})}
                >
                    Clear Filters
                </button>
            )}
        </div>
    )
}
