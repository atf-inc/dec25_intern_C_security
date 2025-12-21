import { useState, useEffect } from 'react'
import './Toast.css'

export type ToastType = 'success' | 'error' | 'info'

export interface ToastProps {
    message: string
    type?: ToastType
    duration?: number
    onClose: () => void
}

export function Toast({ message, type = 'info', duration = 3000, onClose }: ToastProps) {
    const [isVisible, setIsVisible] = useState(true)

    useEffect(() => {
        const timer = setTimeout(() => {
            setIsVisible(false)
            setTimeout(onClose, 300) // Wait for animation
        }, duration)

        return () => clearTimeout(timer)
    }, [duration, onClose])

    return (
        <div
            className={`toast toast-${type} ${isVisible ? 'show' : 'hide'}`}
            role="status"
            aria-live="polite"
            aria-atomic="true"
        >
            <span className="toast-icon" aria-hidden="true">
                {type === 'success' && '✅'}
                {type === 'error' && '❌'}
                {type === 'info' && 'ℹ️'}
            </span>
            <p className="toast-message">{message}</p>
            <button
                className="toast-close"
                onClick={() => setIsVisible(false)}
                aria-label="Dismiss notification"
            >×</button>
        </div>
    )
}


