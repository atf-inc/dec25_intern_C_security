import { useEffect, useRef, useState } from 'react'
import './WaveformVisualizer.css'

interface WaveformVisualizerProps {
    audioUrl: string
    isPlaying: boolean
    currentTime: number
    duration: number
    onSeek: (time: number) => void
}

export function WaveformVisualizer({
    audioUrl,
    // isPlaying is available for future use (e.g., animation)
    currentTime,
    duration,
    onSeek
}: WaveformVisualizerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const containerRef = useRef<HTMLDivElement>(null)
    const [audioData, setAudioData] = useState<Float32Array | null>(null)

    // 1. Decode Audio Data to get Waveform points
    useEffect(() => {
        if (!audioUrl) return

        const fetchAudio = async () => {
            try {
                const response = await fetch(audioUrl)
                const arrayBuffer = await response.arrayBuffer()
                const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
                const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

                // We only need one channel for visualization
                setAudioData(audioBuffer.getChannelData(0))
            } catch (e) {
                console.error("Error generating waveform:", e)
            }
        }

        fetchAudio()
    }, [audioUrl])

    // 2. Draw the Waveform
    useEffect(() => {
        const canvas = canvasRef.current
        const container = containerRef.current
        if (!canvas || !container || !audioData) return

        const ctx = canvas.getContext('2d')
        if (!ctx) return

        // Handle high DPI displays
        const dpr = window.devicePixelRatio || 1
        const width = container.clientWidth
        const height = 120 // Fixed height

        canvas.width = width * dpr
        canvas.height = height * dpr
        canvas.style.width = `${width}px`
        canvas.style.height = `${height}px`

        ctx.scale(dpr, dpr)
        ctx.clearRect(0, 0, width, height)

        // Styling
        const barWidth = 3
        const gap = 1
        const totalBars = Math.floor(width / (barWidth + gap))
        const step = Math.ceil(audioData.length / totalBars)
        const amp = height / 2

        // Gradient for the played portion
        const playedGradient = ctx.createLinearGradient(0, 0, 0, height)
        playedGradient.addColorStop(0, '#3b82f6') // Blue-500
        playedGradient.addColorStop(1, '#60a5fa') // Blue-400

        // Color for the unplayed portion
        const unplayedColor = '#e2e8f0' // Slate-200

        // Draw loop
        for (let i = 0; i < totalBars; i++) {
            let min = 1.0
            let max = -1.0

            // Calculate peak in this chunk
            for (let j = 0; j < step; j++) {
                const datum = audioData[(i * step) + j]
                if (datum < min) min = datum
                if (datum > max) max = datum
            }

            // Calculate progress to determine color
            const progress = i / totalBars
            const currentPlayProgress = currentTime / duration

            ctx.fillStyle = progress <= currentPlayProgress ? playedGradient : unplayedColor

            // Draw rounded bar
            const barHeight = Math.max(2, (max - min) * amp)
            const x = i * (barWidth + gap)
            const y = (height - barHeight) / 2

            // Rounded rect implementation
            ctx.beginPath()
            ctx.roundRect(x, y, barWidth, barHeight, 2)
            ctx.fill()
        }

    }, [audioData, currentTime, duration, containerRef.current?.clientWidth])

    // 3. Handle Click to Seek
    const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (!duration) return

        const rect = canvasRef.current!.getBoundingClientRect()
        const x = e.clientX - rect.left
        const width = rect.width
        const percentage = Math.max(0, Math.min(1, x / width))

        onSeek(percentage * duration)
    }

    return (
        <div
            className="waveform-container"
            ref={containerRef}
        >
            <canvas
                ref={canvasRef}
                onClick={handleCanvasClick}
                className="waveform-canvas"
                style={{ cursor: 'pointer' }}
            />
            {/* Hover Time Indicator could go here */}
        </div>
    )
}
