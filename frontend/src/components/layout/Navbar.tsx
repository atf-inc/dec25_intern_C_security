import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ThemeToggle } from '../common/ThemeToggle'
import LanguageToggle from '../common/LanguageToggle'
import './Navbar.css'

export function Navbar() {
    const { t } = useTranslation();

    return (
        <nav className="navbar">
            <div className="navbar-container">
                <Link to="/" className="navbar-brand">
                    🛡️ ATF CyberX
                </Link>
                <div className="navbar-links">
                    <Link to="/phishing" className="nav-link">
                        {t('navigation.phishing')}
                    </Link>
                    <Link to="/voice" className="nav-link">
                        {t('navigation.voice')}
                    </Link>
                    <Link to="/history" className="nav-link">
                        {t('navigation.dashboard')}
                    </Link>
                    <div className="navbar-toggles">
                        <LanguageToggle size="sm" />
                        <ThemeToggle className="sm" />
                    </div>
                </div>
            </div>
        </nav>
    )
}
