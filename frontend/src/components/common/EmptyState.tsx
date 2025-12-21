import './EmptyState.css'

interface EmptyStateProps {
    icon?: string
    title: string
    message?: string
    action?: {
        label: string
        onClick: () => void
    }
}

export function EmptyState({ icon = '📭', title, message, action }: EmptyStateProps) {
    return (
        <div className="empty-state-container" role="status">
            <div className="empty-state-icon">{icon}</div>
            <h3 className="empty-state-title">{title}</h3>
            {message && <p className="empty-state-message">{message}</p>}
            {action && (
                <button
                    className="empty-state-action primary-btn"
                    onClick={action.onClick}
                >
                    {action.label}
                </button>
            )}
        </div>
    )
}
