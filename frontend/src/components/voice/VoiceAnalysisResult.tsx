
import React from 'react';
import './VoicePage.css';
import { RiskBadge } from '../common/RiskBadge';

interface VoiceAnalysisResultProps {
    result: {
        is_deepfake: boolean;
        confidence: number;
        risk_level: 'low' | 'medium' | 'high' | 'critical';
        explanation?: string;
    };
}

export const VoiceAnalysisResult: React.FC<VoiceAnalysisResultProps> = ({ result }) => {
    const { is_deepfake, confidence, risk_level, explanation } = result;

    return (
        <div className="analysis-result">
            <div className="result-header">
                <div>
                    <h2 className="result-title">
                        {is_deepfake ? '⚠️ Deepfake Detected' : '✅ Real Human Voice'}
                    </h2>
                    <RiskBadge level={risk_level === 'critical' ? 'high' : risk_level} score={Math.round(confidence * 100)} />
                </div>
                <div className="confidence-meter">
                    <span className="confidence-label">Confidence:</span>
                    <span className="confidence-value">{(confidence * 100).toFixed(1)}%</span>
                </div>
            </div>

            {explanation && (
                <div className="explanation-box">
                    <h3 className="explanation-title">AI Explanation</h3>
                    <div className="explanation-text">
                        {explanation}
                    </div>
                </div>
            )}
        </div>
    );
};
