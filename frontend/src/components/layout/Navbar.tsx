<<<<<<< HEAD
import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
=======

import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'

>>>>>>> origin/develop
import { useTranslation } from 'react-i18next'
import { ThemeToggle } from '../common/ThemeToggle'
import LanguageToggle from '../common/LanguageToggle'
import logoImage from '../image.png'
import './Navbar.css'

export function Navbar() {
    const { t } = useTranslation();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
<<<<<<< HEAD
=======

>>>>>>> origin/develop
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
<<<<<<< HEAD
=======

>>>>>>> origin/develop

    return (
        <nav
            className={`navbar ${isScrolled ? 'scrolled' : ''}`}
            aria-label="Main navigation"
        >
            <div className="navbar-container">
                <NavLink to="/" className="navbar-brand">
                    <img src={logoImage} alt="ATF Shield" className="navbar-logo" />
                    <span className="brand-text">
                        <span className="brand-atf"></span>
                        <span className="brand-cyberx">CyberX</span>
                    </span>
<<<<<<< HEAD
                </NavLink>

=======

                </NavLink>


>>>>>>> origin/develop
                <button
                    className="navbar-toggle-btn"
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    aria-label="Toggle navigation menu"
                    aria-expanded={isMenuOpen}
<<<<<<< HEAD
                    aria-controls="navbar-menu"
=======

                    aria-controls="navbar-menu"

>>>>>>> origin/develop
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
<<<<<<< HEAD
=======

>>>>>>> origin/develop
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
