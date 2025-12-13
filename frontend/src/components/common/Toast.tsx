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
        <div className={`toast toast-${type} ${isVisible ? 'show' : 'hide'}`}>
            <span className="toast-icon">
                {type === 'success' && '✅'}
                {type === 'error' && '❌'}
                {type === 'info' && 'ℹ️'}
            </span>
            <p className="toast-message">{message}</p>
            <button className="toast-close" onClick={() => setIsVisible(false)}>×</button>
        </div>
    )
}

// Simple hook for managing toasts in parent components
export function useToast() {
    const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null)

    const showToast = (message: string, type: ToastType = 'info') => {
        setToast({ message, type })
    }

    const closeToast = () => setToast(null)

    return { toast, showToast, closeToast }
}
