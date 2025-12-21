import { useEffect, useMemo } from 'react'
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import { ScanHistoryItem } from '../../api/phishingApi'
import './HistoryComponents.css'

interface HistoryChartProps {
    data: ScanHistoryItem[]
    title?: string
}

export function HistoryChart({ data, title }: HistoryChartProps) {
    const { t } = useTranslation()
    const chartId = useMemo(() => `chart-${Math.random().toString(36).substr(2, 9)}`, [])

    // Force resize on mount to ensure Recharts measures correctly
    useEffect(() => {
        const timer = setTimeout(() => {
            window.dispatchEvent(new Event('resize'))
        }, 100)
        return () => clearTimeout(timer)
    }, [])

    // Fallback function for translations
    const getText = (key: string, fallback: string) => {
        const translated = t(key)
        return translated === key ? fallback : translated
    }

    const defaultTitle = getText('dashboard.riskScoreTrend', 'Risk Score Trend')
    const chartTitle = title || defaultTitle

    if (!data || data.length === 0) return null

    // Process data for the chart - sort by date
    const chartData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())

    // Customize tooltip
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="custom-tooltip">
                    <p className="tooltip-label">{label}</p>
                    <p className="tooltip-score">{getText('history.score', 'Score')}: {payload[0].value}</p>
                    <p className="tooltip-subject">{payload[0].payload.subject}</p>
                </div>
            )
        }
        return null
    }

    return (
        <div className="chart-container">
            <h2 className="chart-title">{chartTitle}</h2>
            <div style={{ flex: 1, minHeight: '300px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={chartData}
                        margin={{
                            top: 5,
                            right: 30,
                            left: 50,
                            bottom: 30,
                        }}
                    >
                        <defs>
                            <linearGradient id={`colorRisk-${chartId}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--brand-primary)" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="var(--brand-primary)" stopOpacity={0.1} />
                            </linearGradient>
                            <filter id={`shadow-${chartId}`}>
                                <feDropShadow dx="0" dy="4" stdDeviation="3" floodColor="var(--brand-primary)" floodOpacity="0.3" />
                            </filter>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
                        <XAxis
                            dataKey="date"
                            tickFormatter={(date) => new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                            stroke="var(--text-tertiary)"
                            tick={{ fill: 'var(--text-tertiary)', fontSize: 12 }}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            domain={[0, 100]}
                            stroke="var(--text-tertiary)"
                            tick={{ fill: 'var(--text-tertiary)', fontSize: 12 }}
                            tickLine={false}
                            axisLine={false}
                        />
                        <Tooltip
                            content={<CustomTooltip />}
                            cursor={{ fill: 'var(--brand-primary-light)' }}
                        />
                        <Legend wrapperStyle={{ paddingTop: '10px' }} />
                        <Bar
                            dataKey="risk_score"
                            name={getText('dashboard.riskScoreTrend', 'Risk Score')}
                            fill={`url(#colorRisk-${chartId})`}
                            filter={`url(#shadow-${chartId})`}
                            radius={[4, 4, 0, 0]}
                            animationDuration={1500}
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}