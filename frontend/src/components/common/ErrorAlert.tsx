import './ErrorAlert.css'

interface ErrorAlertProps {
    message: string
    onClose?: () => void
}

export function ErrorAlert({ message, onClose }: ErrorAlertProps) {
    return (
        <div className="error-alert">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="error-icon">⚠️</span>
                <span>{message}</span>
            </div>
            {onClose && (
                <button
                    onClick={onClose}
                    style={{
                        background: 'none',
                        border: 'none',
                        color: 'currentColor',
                        cursor: 'pointer',
                        fontSize: '1.2rem',
                        padding: '0 0.5rem',
                        opacity: 0.7
                    }}
                >
                    &times;
                </button>
            )}
        </div>
    )
}
