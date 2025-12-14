import { ScanHistoryItem } from '../api/phishingApi'
import DOMPurify from 'dompurify'

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
            // Sanitize input
            const sanitizedItem = {
                ...item,
                subject: DOMPurify.sanitize(item.subject),
                sender: DOMPurify.sanitize(item.sender),
                original_input: item.original_input ? {
                    ...item.original_input,
                    subject: DOMPurify.sanitize(item.original_input.subject),
                    sender: DOMPurify.sanitize(item.original_input.sender),
                    body: DOMPurify.sanitize(item.original_input.body)
                } : undefined
            }

            const current = storage.getHistory()
            // Add new item to the beginning
            const updated = [sanitizedItem, ...current].slice(0, MAX_HISTORY_ITEMS)
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        } catch (error) {
            console.error('Failed to save scan result:', error)
        }
    },

    // Delete a single scan by ID
    deleteScan: (id: number) => {
        try {
            const current = storage.getHistory()
            const updated = current.filter(item => item.id !== id)
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        } catch (error) {
            console.error('Failed to delete scan:', error)
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
