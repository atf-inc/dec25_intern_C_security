import React, { useState, useRef, DragEvent } from 'react';
import { ProgressIndicator, SuccessAnimation, ErrorAnimation } from './ProgressIndicator';
import './AnimatedUploadZone.css';

interface AnimatedUploadZoneProps {
    onFileSelect: (files: FileList) => void;
    accept?: string;
    multiple?: boolean;
    maxSize?: number; // in MB
    className?: string;
    disabled?: boolean;
}

interface UploadState {
    isDragOver: boolean;
    isUploading: boolean;
    progress: number;
    status: 'idle' | 'uploading' | 'success' | 'error';
    error?: string;
}

export function AnimatedUploadZone({
    onFileSelect,
    accept = '.eml,.txt,.pdf',
    multiple = false,
    maxSize = 10,
    className = '',
    disabled = false
}: AnimatedUploadZoneProps) {
    const [uploadState, setUploadState] = useState<UploadState>({
        isDragOver: false,
        isUploading: false,
        progress: 0,
        status: 'idle'
    });

    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragEnter = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!disabled) {
            setUploadState(prev => ({ ...prev, isDragOver: true }));
        }
    };

    const handleDragLeave = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!disabled) {
            setUploadState(prev => ({ ...prev, isDragOver: false }));
        }
    };

    const handleDragOver = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();

        if (disabled) return;

        setUploadState(prev => ({ ...prev, isDragOver: false }));

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFiles(files);
        }
    };

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleFiles(files);
        }
    };

    const handleFiles = (files: FileList) => {
        // Validate file size
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (file.size > maxSize * 1024 * 1024) {
                setUploadState(prev => ({
                    ...prev,
                    status: 'error',
                    error: `File "${file.name}" is too large. Maximum size is ${maxSize}MB.`
                }));
                return;
            }
        }

        // Simulate upload progress
        setUploadState(prev => ({ ...prev, isUploading: true, status: 'uploading', progress: 0 }));

        const progressInterval = setInterval(() => {
            setUploadState(prev => {
                const newProgress = prev.progress + Math.random() * 30;
                if (newProgress >= 100) {
                    clearInterval(progressInterval);
                    setTimeout(() => {
                        setUploadState(current => ({ ...current, status: 'success', isUploading: false }));
                        onFileSelect(files);
                    }, 500);
                    return { ...prev, progress: 100 };
                }
                return { ...prev, progress: newProgress };
            });
        }, 200);
    };

    const handleClick = () => {
        if (!disabled && uploadState.status !== 'uploading') {
            fileInputRef.current?.click();
        }
    };

    const resetState = () => {
        setUploadState({
            isDragOver: false,
            isUploading: false,
            progress: 0,
            status: 'idle'
        });
    };

    const getZoneContent = () => {
        switch (uploadState.status) {
            case 'uploading':
                return (
                    <div className="upload-content">
                        <ProgressIndicator
                            variant="circular"
                            progress={uploadState.progress}
                            size="lg"
                            color="primary"
                            showPercentage
                        />
                        <div className="upload-text">
                            <h3>Uploading files...</h3>
                            <p>Please wait while we process your files</p>
                        </div>
                    </div>
                );

            case 'success':
                return (
                    <div className="upload-content">
                        <SuccessAnimation size="lg" />
                        <div className="upload-text">
                            <h3>Upload successful!</h3>
                            <p>Your files have been processed successfully</p>
                        </div>
                        <button className="upload-reset-btn" onClick={resetState}>
                            Upload Another File
                        </button>
                    </div>
                );

            case 'error':
                return (
                    <div className="upload-content">
                        <ErrorAnimation size="lg" />
                        <div className="upload-text">
                            <h3>Upload failed</h3>
                            <p>{uploadState.error || 'An error occurred during upload'}</p>
                        </div>
                        <button className="upload-reset-btn" onClick={resetState}>
                            Try Again
                        </button>
                    </div>
                );

            default:
                return (
                    <div className="upload-content">
                        <div className="upload-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                <polyline points="7,10 12,15 17,10" />
                                <line x1="12" y1="15" x2="12" y2="3" />
                            </svg>
                        </div>
                        <div className="upload-text">
                            <h3>Drop files here or click to browse</h3>
                            <p>Supports {accept.replace(/\./g, '').toUpperCase()} files up to {maxSize}MB</p>
                        </div>
                    </div>
                );
        }
    };

    return (
        <div className={`animated-upload-zone ${className}`}>
            <div
                className={`upload-zone ${uploadState.isDragOver ? 'drag-over' : ''} ${uploadState.status} ${disabled ? 'disabled' : ''}`}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={handleClick}
            >
                {getZoneContent()}
            </div>

            <input
                ref={fileInputRef}
                type="file"
                accept={accept}
                multiple={multiple}
                onChange={handleFileInput}
                style={{ display: 'none' }}
                disabled={disabled}
            />
        </div>
    );
}