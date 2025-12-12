
import React, { useRef, useState } from 'react';
import './VoicePage.css';

interface AudioUploadProps {
    onFileSelect: (file: File) => void;
    selectedFile: File | null;
    onClearFile: () => void;
}

export const AudioUpload: React.FC<AudioUploadProps> = ({ onFileSelect, selectedFile, onClearFile }) => {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [isDragging, setIsDragging] = useState(false);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            validateAndSelect(file);
        }
    };

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            validateAndSelect(e.target.files[0]);
        }
    };

    const validateAndSelect = (file: File) => {
        const allowedTypes = ['audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/x-m4a', 'audio/ogg', 'audio/flac'];
        // Simple check, backend does strict check
        if (file.type && !allowedTypes.includes(file.type) && !file.name.endsWith('.wav')) {
            // Basic fallback for some extensions
            // We'll let backend handle edge cases, but warn here if obvious
        }
        onFileSelect(file);
    };

    if (selectedFile) {
        return (
            <div className="selected-file">
                <div className="file-info">
                    <span role="img" aria-label="audio" style={{ fontSize: '1.5rem' }}>🎵</span>
                    <div>
                        <div className="file-name">{selectedFile.name}</div>
                        <div style={{ fontSize: '0.8rem', color: '#666' }}>
                            {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                        </div>
                    </div>
                </div>
                <button onClick={() => {
                    onClearFile();
                    if (fileInputRef.current) fileInputRef.current.value = '';
                }} className="remove-file">
                    Remove
                </button>
            </div>
        );
    }

    return (
        <div
            className={`audio-upload ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
        >
            <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                accept=".wav,.mp3,.m4a,.flac,.ogg"
                onChange={handleFileInput}
            />
            <div className="upload-icon">🎙️</div>
            <div className="upload-text">Click to upload or drag and drop</div>
            <div className="upload-subtext">WAV, MP3, M4A, FLAC, OGG (Max 10MB)</div>
        </div>
    );
};
