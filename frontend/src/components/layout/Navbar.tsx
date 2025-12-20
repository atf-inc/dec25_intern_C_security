import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ThemeToggle } from '../common/ThemeToggle'
import LanguageToggle from '../common/LanguageToggle'
import logoImage from '../image.png'
import './Navbar.css'

export function Navbar() {
    const { t } = useTranslation();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    return (
        <nav className="navbar">
            <div className="navbar-container">
                <Link to="/" className="navbar-brand">
                    <img src={logoImage} alt="ATF Shield" className="navbar-logo" />
                    <span className="brand-text">
                        <span className="brand-atf"></span>
                        <span className="brand-cyberx">CyberX</span>
                    </span>
                </Link>

                <button
                    className="navbar-toggle-btn"
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    aria-label="Toggle navigation menu"
                    aria-expanded={isMenuOpen}
                >
                    <span className={`hamburger ${isMenuOpen ? 'open' : ''}`}></span>
                </button>

                <div className={`navbar-links ${isMenuOpen ? 'active' : ''}`}>
                    <Link to="/phishing" className="nav-link" onClick={() => setIsMenuOpen(false)}>
                        {t('navigation.phishing')}
                    </Link>
                    <Link to="/voice" className="nav-link" onClick={() => setIsMenuOpen(false)}>
                        {t('navigation.voice')}
                    </Link>
                    <Link to="/history" className="nav-link" onClick={() => setIsMenuOpen(false)}>
                        {t('navigation.dashboard')}
                    </Link>
                    <div className="navbar-toggles">
                        <LanguageToggle size="sm" />
                        <ThemeToggle className="sm" />
                    </div>
                </div>

                {isMenuOpen && (
                    <div className="navbar-overlay" onClick={() => setIsMenuOpen(false)} aria-hidden="true" />
                )}
            </div>
        </nav>
    )
}
