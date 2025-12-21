import { BrowserRouter } from 'react-router-dom'
import { AppRouter } from './router'
import { Layout } from './components/layout/Layout'
import './i18n' // Initialize i18n

import { ToastProvider } from './components/common/ToastContext'

function App() {
    return (
        <BrowserRouter>
            <ToastProvider>
                <Layout>
                    <AppRouter />
                </Layout>
            </ToastProvider>
        </BrowserRouter>
    )
}

export default App
