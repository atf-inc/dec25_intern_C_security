import React from 'react';
import { useTranslation } from 'react-i18next';
import './LanguageToggle.css';

interface LanguageToggleProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

const LanguageToggle: React.FC<LanguageToggleProps> = ({ size = 'md', className = '' }) => {
    const { i18n } = useTranslation();

    const changeLanguage = (lng: string) => {
        i18n.changeLanguage(lng);
        localStorage.setItem('language', lng);
    };

    const currentLanguage = i18n.language;
    const isJapanese = currentLanguage === 'ja';



    return (
        <div className={`language-toggle-container ${className}`}>
            {/* Modern Toggle Switch Design */}
            <div className={`language-toggle-switch ${size}`}>
                <div
                    className={`toggle-track ${isJapanese ? 'active' : ''}`}
                    onClick={() => changeLanguage(isJapanese ? 'en' : 'ja')}
                >
                    <div className={`toggle-thumb ${isJapanese ? 'active' : ''}`}>
                        <span className="toggle-flag">
                            {isJapanese ? '🇯🇵' : '🇺🇸'}
                        </span>
                    </div>
                    <div className="toggle-labels">
                        <span className={`label-left ${!isJapanese ? 'active' : ''}`}>EN</span>
                        <span className={`label-right ${isJapanese ? 'active' : ''}`}>JP</span>
                    </div>
                </div>
            </div>

            {/* Alternative: Modern Dropdown Design (commented out) */}
            {/* 
            <div className="language-dropdown">
                <button 
                    className="language-button"
                    onClick={() => setIsOpen(!isOpen)}
                    onBlur={() => setTimeout(() => setIsOpen(false), 150)}
                >
                    <div className="language-current">
                        <span className="language-flag">{currentLang.flag}</span>
                        <span className="language-code">{currentLang.short}</span>
                        <svg 
                            className={`language-arrow ${isOpen ? 'open' : ''}`} 
                            width="12" 
                            height="12" 
                            viewBox="0 0 12 12"
                        >
                            <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                        </svg>
                    </div>
                </button>
                
                {isOpen && (
                    <div className="language-menu">
                        {languages.map((lang) => (
                            <button
                                key={lang.code}
                                className={`language-option ${currentLanguage === lang.code ? 'active' : ''}`}
                                onClick={() => changeLanguage(lang.code)}
                            >
                                <span className="language-flag">{lang.flag}</span>
                                <span className="language-name">{lang.name}</span>
                                {currentLanguage === lang.code && (
                                    <svg className="check-icon" width="16" height="16" viewBox="0 0 16 16">
                                        <path d="M13.5 4.5L6 12 2.5 8.5" stroke="currentColor" strokeWidth="2" fill="none"/>
                                    </svg>
                                )}
                            </button>
                        ))}
                    </div>
                )}
            </div>
            */}
        </div>
    );
};

export default LanguageToggle;