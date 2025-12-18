import { Link } from 'react-router-dom'
import { ThemeToggle } from '../common/ThemeToggle'
import './Navbar.css'

export function Navbar() {
    return (
        <nav className="navbar">
            <div className="navbar-container">
                <Link to="/" className="navbar-brand">
                    🛡️ ATF CyberX
                </Link>
                <div className="navbar-links">
                    <Link to="/phishing" className="nav-link">
                        Phishing Detection
                    </Link>
                    <Link to="/voice" className="nav-link">
                        Voice Analysis
                    </Link>
                    <Link to="/history" className="nav-link">
                        History
                    </Link>
                    <ThemeToggle />
                </div>
            </div>
        </nav>
    )
}
