
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
import { ScanHistoryItem } from '../../api/phishingApi'

interface HistoryChartProps {
    data: ScanHistoryItem[]
    title?: string
}

export function HistoryChart({ data, title = "Risk Score Trend" }: HistoryChartProps) {
    if (!data || data.length === 0) return null

    // Process data for the chart - sort by date
    const chartData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())

    // Customize tooltip
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div style={{ backgroundColor: 'white', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}>
                    <p style={{ margin: 0, fontWeight: 'bold' }}>{label}</p>
                    <p style={{ margin: 0, color: '#8884d8' }}>Score: {payload[0].value}</p>
                    <p style={{ margin: 0, fontSize: '0.8em' }}>{payload[0].payload.subject}</p>
                </div>
            )
        }
        return null
    }

    return (
        <div style={{ height: '300px', width: '100%', marginBottom: '2rem' }}>
            <h3 style={{ marginBottom: '1rem', color: '#333' }}>{title}</h3>
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
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="date"
                        tickFormatter={(date) => new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                    />
                    <YAxis domain={[0, 100]} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Bar dataKey="risk_score" name="Risk Score" fill="#8884d8" radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}
