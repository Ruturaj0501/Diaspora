"use client";

import React, { useState } from 'react';

export default function UploadSection() {
    const [file, setFile] = useState<File | null>(null);
    const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setStatus('uploading');
        setMessage('Processing document through DIRP AI Pipeline...');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('https://diaspora-snh1.onrender.com/api/v1/pipeline/upload', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                setStatus('success');
                setMessage('Document ingested successfully. Pipeline running in background.');
            } else {
                setStatus('error');
                setMessage('Upload failed. Please check backend status.');
            }
        } catch (error) {
            setStatus('error');
            setMessage('Expertise connection failed. Ensure FastAPI is running.');
        }
    };

    return (
        <div className="glass-dark p-8 rounded-2xl border-white/10 shadow-2xl">
            <h2 className="text-2xl font-serif text-accent mb-6 text-glow">Archival Document Ingestion</h2>

            <div className="border-2 border-dashed border-white/20 rounded-xl p-12 text-center hover:border-accent/50 transition-colors cursor-pointer relative overflow-hidden group">
                <input
                    type="file"
                    onChange={handleFileChange}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <div className="space-y-4">
                    <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                        <svg className="w-8 h-8 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                    </div>
                    <div>
                        <p className="text-lg font-medium">{file ? file.name : "Select or drag archival image"}</p>
                        <p className="text-muted-foreground text-sm">Supported formats: JPG, PNG, TIFF (Max 20MB)</p>
                    </div>
                </div>
                {status === 'uploading' && <div className="absolute bottom-0 left-0 h-1 bg-accent shimmer w-full" />}
            </div>

            {file && status !== 'uploading' && (
                <button
                    onClick={handleUpload}
                    className="mt-6 w-full py-3 gold-gradient text-accent-foreground font-bold rounded-lg hover:opacity-90 transition-opacity uppercase tracking-widest text-sm shadow-[0_0_20px_rgba(212,175,55,0.3)]"
                >
                    Initialize Reconstruction Pipeline
                </button>
            )}

            {message && (
                <div className={`mt-6 p-4 rounded-lg text-sm border ${status === 'error' ? 'bg-red-500/10 border-red-500/50 text-red-400' :
                    status === 'success' ? 'bg-green-500/10 border-green-500/50 text-green-400' :
                        'bg-accent/10 border-accent/50 text-accent'
                    }`}>
                    {message}
                </div>
            )}
        </div>
    );
}
