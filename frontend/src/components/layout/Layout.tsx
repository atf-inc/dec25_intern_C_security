import { ReactNode } from 'react'
import { Navbar } from './Navbar'
import './Layout.css'

interface LayoutProps {
    children: ReactNode
}

export function Layout({ children }: LayoutProps) {
    return (
        <div className="app-layout">
            <Navbar />
            <main className="main-content">
                {children}
            </main>
        </div>
    )
}