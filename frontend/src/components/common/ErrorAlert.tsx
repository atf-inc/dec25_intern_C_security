import './ErrorAlert.css'

interface ErrorAlertProps {
    message: string
}

export function ErrorAlert({ message }: ErrorAlertProps) {
    return (
        <div className="error-alert">
            <span className="error-icon">⚠️</span>
            <span>{message}</span>
        </div>
    )
}
