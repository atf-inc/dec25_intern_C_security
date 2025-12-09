import { ReactNode } from 'react'
import { Navbar } from './Navbar'

interface LayoutProps {
    children: ReactNode
}

export function Layout({ children }: LayoutProps) {
    return (
        <div>
            <Navbar />
            <main className="container">
                {children}
            </main>
        </div>
    )
}
