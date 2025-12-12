import { ScanHistoryItem } from '../api/phishingApi'

const STORAGE_KEY = 'scan_history'
const MAX_HISTORY_ITEMS = 50

export const storage = {
    // Get all scan history
    getHistory: (): ScanHistoryItem[] => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY)
            return stored ? JSON.parse(stored) : []
        } catch (error) {
            console.error('Failed to parse scan history:', error)
            return []
        }
    },

    // Save a new scan result
    saveScan: (item: ScanHistoryItem) => {
        try {
            const current = storage.getHistory()
            // Add new item to the beginning
            const updated = [item, ...current].slice(0, MAX_HISTORY_ITEMS)
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        } catch (error) {
            console.error('Failed to save scan result:', error)
        }
    },

    // Clear all history
    clearHistory: () => {
        localStorage.removeItem(STORAGE_KEY)
    },

    // Get a single scan by ID
    getScanById: (id: number): ScanHistoryItem | undefined => {
        const history = storage.getHistory()
        return history.find(item => item.id === id)
    }
}
