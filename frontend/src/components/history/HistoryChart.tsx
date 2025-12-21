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
            <h3 className="chart-title">{chartTitle}</h3>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart
                    data={chartData}
                    margin={{
                        top: 5,
                        right: 30,
                        left: 20,
                        bottom: 5,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                    <XAxis
                        dataKey="date"
                        tickFormatter={(date) => new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        stroke="var(--text-color)"
                        tick={{ fill: 'var(--text-color)' }}
                    />
                    <YAxis
                        domain={[0, 100]}
                        stroke="var(--text-color)"
                        tick={{ fill: 'var(--text-color)' }}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.1)' }} />
                    <Legend />
                    <Bar dataKey="risk_score" name={getText('dashboard.riskScoreTrend', 'Risk Score')} fill="var(--primary-color)" radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}