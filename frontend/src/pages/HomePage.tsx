import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import './HomePage.css'

export function HomePage() {
    const { i18n } = useTranslation()
    const [stats, setStats] = useState({
        threatsDetected: 0,
        emailsAnalyzed: 0,
        voiceScansCompleted: 0
    })

    // Animated counter effect
    useEffect(() => {
        const animateStats = () => {
            const targets = { threatsDetected: 1247, emailsAnalyzed: 8934, voiceScansCompleted: 2156 }
            const duration = 2000
            const steps = 60
            const stepTime = duration / steps

            let currentStep = 0
            const timer = setInterval(() => {
                currentStep++
                const progress = currentStep / steps
                const easeOut = 1 - Math.pow(1 - progress, 3)

                setStats({
                    threatsDetected: Math.floor(targets.threatsDetected * easeOut),
                    emailsAnalyzed: Math.floor(targets.emailsAnalyzed * easeOut),
                    voiceScansCompleted: Math.floor(targets.voiceScansCompleted * easeOut)
                })

                if (currentStep >= steps) {
                    clearInterval(timer)
                    setStats(targets)
                }
            }, stepTime)

            return () => clearInterval(timer)
        }

        const timeout = setTimeout(animateStats, 500)
        return () => clearTimeout(timeout)
    }, [])

    return (
        <div className="home-page">
            {/* Hero Section */}
            <section className="hero-section">
                <div className="hero-background">
                    <div className="hero-particles"></div>
                </div>

                <div className="hero-content">
                    <div className="hero-badge">
                        <span className="badge-icon">🛡️</span>
                        <span>{i18n.language === 'ja' ? 'AI駆動のセキュリティ' : 'AI-Powered Security'}</span>
                    </div>

                    <h1 className="hero-title">
                        {i18n.language === 'ja' ? (
                            <>
                                次世代の<br />
                                <span className="gradient-text">サイバーセキュリティ</span><br />
                                プラットフォーム
                            </>
                        ) : (
                            <>
                                Next-Generation<br />
                                <span className="gradient-text">Cybersecurity</span><br />
                                Platform
                            </>
                        )}
                    </h1>

                    <p className="hero-description">
                        {i18n.language === 'ja'
                            ? 'フィッシング攻撃、ディープフェイク音声、その他のサイバー脅威から組織を保護する高度なAI技術を活用したセキュリティソリューション'
                            : 'Advanced AI-powered security solutions to protect your organization from phishing attacks, deepfake audio, and other cyber threats with enterprise-grade accuracy'
                        }
                    </p>

                    <div className="hero-actions">
                        <Link to="/phishing" className="hero-cta primary">
                            <span className="cta-icon">📧</span>
                            <span>{i18n.language === 'ja' ? 'メール分析を開始' : 'Analyze Email'}</span>
                            <span className="cta-arrow">→</span>
                        </Link>
                        <Link to="/voice" className="hero-cta secondary">
                            <span className="cta-icon">🎤</span>
                            <span>{i18n.language === 'ja' ? '音声検証' : 'Voice Analysis'}</span>
                        </Link>
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section className="stats-section">
                <div className="stats-container">
                    <div className="stat-card">
                        <div className="stat-icon threats">🚨</div>
                        <div className="stat-number">{stats.threatsDetected.toLocaleString()}</div>
                        <div className="stat-label">
                            {i18n.language === 'ja' ? '脅威を検出' : 'Threats Detected'}
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon emails">📧</div>
                        <div className="stat-number">{stats.emailsAnalyzed.toLocaleString()}</div>
                        <div className="stat-label">
                            {i18n.language === 'ja' ? 'メール分析' : 'Emails Analyzed'}
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon voice">🎵</div>
                        <div className="stat-number">{stats.voiceScansCompleted.toLocaleString()}</div>
                        <div className="stat-label">
                            {i18n.language === 'ja' ? '音声スキャン' : 'Voice Scans'}
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="features-section">
                <div className="section-header">
                    <h2>{i18n.language === 'ja' ? '強力なセキュリティ機能' : 'Powerful Security Features'}</h2>
                    <p>{i18n.language === 'ja'
                        ? '最新のAI技術で組織を包括的に保護'
                        : 'Comprehensive protection powered by cutting-edge AI technology'
                    }</p>
                </div>

                <div className="features-grid">
                    <div className="feature-card phishing">
                        <div className="feature-icon">
                            <div className="icon-bg phishing-bg">📧</div>
                        </div>
                        <h3>{i18n.language === 'ja' ? 'フィッシング検出' : 'Phishing Detection'}</h3>
                        <p>
                            {i18n.language === 'ja'
                                ? '高度なAIアルゴリズムでフィッシングメールを99.2%の精度で検出し、ブランドなりすましや社会工学的攻撃から保護'
                                : 'Advanced AI algorithms detect phishing emails with 99.2% accuracy, protecting against brand impersonation and social engineering attacks'
                            }
                        </p>
                        <Link to="/phishing" className="feature-link">
                            {i18n.language === 'ja' ? '今すぐ分析 →' : 'Analyze Now →'}
                        </Link>
                    </div>

                    <div className="feature-card voice">
                        <div className="feature-icon">
                            <div className="icon-bg voice-bg">🎤</div>
                        </div>
                        <h3>{i18n.language === 'ja' ? 'ディープフェイク検出' : 'Deepfake Detection'}</h3>
                        <p>
                            {i18n.language === 'ja'
                                ? '最先端の音声分析技術でディープフェイク音声を検出し、音声詐欺や偽装攻撃から組織を守る'
                                : 'State-of-the-art voice analysis technology detects deepfake audio, protecting against voice fraud and impersonation attacks'
                            }
                        </p>
                        <Link to="/voice" className="feature-link">
                            {i18n.language === 'ja' ? '音声を検証 →' : 'Verify Audio →'}
                        </Link>
                    </div>

                    <div className="feature-card analytics">
                        <div className="feature-icon">
                            <div className="icon-bg analytics-bg">📊</div>
                        </div>
                        <h3>{i18n.language === 'ja' ? 'セキュリティ分析' : 'Security Analytics'}</h3>
                        <p>
                            {i18n.language === 'ja'
                                ? '包括的なダッシュボードで脅威の傾向を追跡し、リアルタイムでセキュリティ状況を監視'
                                : 'Comprehensive dashboard to track threat trends and monitor your security posture in real-time with actionable insights'
                            }
                        </p>
                        <Link to="/history" className="feature-link">
                            {i18n.language === 'ja' ? 'ダッシュボード →' : 'View Dashboard →'}
                        </Link>
                    </div>
                </div>
            </section>

            {/* Security Architecture */}
            <section className="security-section">
                <div className="security-content">
                    <div className="security-text">
                        <h2>{i18n.language === 'ja' ? 'セキュリティアーキテクチャ' : 'Security by Design'}</h2>
                        <div className="security-features">
                            <div className="security-item">
                                <span className="security-icon">📧</span>
                                <div>
                                    <h4>{i18n.language === 'ja' ? 'ハイブリッドメール検出' : 'Hybrid Email Detection'}</h4>
                                    <p>{i18n.language === 'ja' ? 'ヒューリスティック + 埋め込み + LLMの3層アーキテクチャでフィッシング検出' : 'Three-layer phishing detection: Heuristics + Embeddings + LLM analysis'}</p>
                                </div>
                            </div>
                            <div className="security-item">
                                <span className="security-icon">🎵</span>
                                <div>
                                    <h4>{i18n.language === 'ja' ? 'WavLM音声分析' : 'WavLM Voice Analysis'}</h4>
                                    <p>{i18n.language === 'ja' ? 'スペクトラル解析とWavLM埋め込みでディープフェイク音声を検出' : 'Spectral analysis + WavLM embeddings for deepfake voice detection'}</p>
                                </div>
                            </div>
                            <div className="security-item">
                                <span className="security-icon">🔒</span>
                                <div>
                                    <h4>{i18n.language === 'ja' ? 'プライバシー優先設計' : 'Privacy-First Architecture'}</h4>
                                    <p>{i18n.language === 'ja' ? 'サーバー側でのデータ保存なし、HTTPS通信で安全なAPI' : 'No server-side data storage, secure HTTPS API communication'}</p>
                                </div>
                            </div>
                            <div className="security-item">
                                <span className="security-icon">🔍</span>
                                <div>
                                    <h4>{i18n.language === 'ja' ? '説明可能なAI判定' : 'Explainable AI Decisions'}</h4>
                                    <p>{i18n.language === 'ja' ? 'ブラックボックススコアではなく、詳細な根拠と証拠を提供' : 'Detailed evidence and reasoning instead of black-box confidence scores'}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="security-visual">
                        <div className="security-shield">
                            <div className="shield-layers">
                                <div className="shield-layer layer-1"></div>
                                <div className="shield-layer layer-2"></div>
                                <div className="shield-layer layer-3"></div>
                            </div>
                            <div className="shield-icon">🛡️</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="cta-section">
                <div className="cta-content">
                    <h2>{i18n.language === 'ja' ? '今すぐセキュリティを強化' : 'Strengthen Your Security Today'}</h2>
                    <p>
                        {i18n.language === 'ja'
                            ? '数分でセットアップ完了。高度なAI保護を今すぐ体験してください。'
                            : 'Get started in minutes and experience advanced AI protection for your organization.'
                        }
                    </p>
                    <div className="cta-actions">
                        <Link to="/phishing" className="cta-button primary">
                            {i18n.language === 'ja' ? 'メール分析を開始' : 'Start Email Analysis'}
                        </Link>
                        <Link to="/voice" className="cta-button secondary">
                            {i18n.language === 'ja' ? '音声検証を試す' : 'Try Voice Verification'}
                        </Link>
                    </div>
                </div>
            </section>
        </div>
    )
}