import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ThemeToggle } from '../common/ThemeToggle'
import LanguageToggle from '../common/LanguageToggle'
import logoImage from '../image.png'
import './Navbar.css'

export function Navbar() {
    const { t } = useTranslation();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);

    // 🖱️ Track scroll for sticky navbar shadow
    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 10); // Show shadow early
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // Helper for NavLink class
    const getNavLinkClass = ({ isActive }: { isActive: boolean }) =>
        `nav-link ${isActive ? 'active' : ''}`;

    return (
        <nav
            className={`navbar ${isScrolled ? 'scrolled' : ''}`}
            aria-label="Main navigation"
        >
            <div className="navbar-container">
                <NavLink to="/" className="navbar-brand">
                    <img src={logoImage} alt="ATF Shield" className="navbar-logo" width="32" height="32" />
                    <span className="brand-text">
                        <span className="brand-atf"></span>
                        <span className="brand-cyberx">CyberX</span>
                    </span>
                </NavLink>

                <button
                    className="navbar-toggle-btn"
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    aria-label="Toggle navigation menu"
                    aria-expanded={isMenuOpen}
                    aria-controls="navbar-menu"
                >
                    <span className={`hamburger ${isMenuOpen ? 'open' : ''}`}></span>
                </button>

                <div
                    id="navbar-menu"
                    className={`navbar-links ${isMenuOpen ? 'active' : ''}`}
                >
                    <NavLink to="/phishing" className={getNavLinkClass} onClick={() => setIsMenuOpen(false)}>
                        {t('navigation.phishing')}
                    </NavLink>
                    <NavLink to="/voice" className={getNavLinkClass} onClick={() => setIsMenuOpen(false)}>
                        {t('navigation.voice')}
                    </NavLink>
                    <NavLink to="/history" className={getNavLinkClass} onClick={() => setIsMenuOpen(false)}>
                        {t('navigation.dashboard')}
                    </NavLink>
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
