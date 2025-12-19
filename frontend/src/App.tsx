import { BrowserRouter } from 'react-router-dom'
import { AppRouter } from './router'
import { Layout } from './components/layout/Layout'
import './i18n' // Initialize i18n

function App() {
    return (
        <BrowserRouter>
            <Layout>
                <AppRouter />
            </Layout>
        </BrowserRouter>
    )
}

export default App
