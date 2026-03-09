"use client";

import React, { useState } from 'react';

interface Evidence {
    extracted_text: string;
    source: string;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    evidence?: Evidence[];
}

export default function CopilotChat() {
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isTyping, setIsTyping] = useState(false);

    const handleAsk = async () => {
        if (!query.trim()) return;

        const userMessage: ChatMessage = { role: 'user', content: query };
        setMessages(prev => [...prev, userMessage]);
        setQuery('');
        setIsTyping(true);

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/copilot/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: query }),
            });

            if (response.ok) {
                const data = await response.json();
                const assistantMessage: ChatMessage = {
                    role: 'assistant',
                    content: data.report,
                    evidence: data.evidence_used
                };
                setMessages(prev => [...prev, assistantMessage]);
            } else {
                throw new Error('Copilot response error');
            }
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'I apologize, but I am unable to access the archival records at this moment. Please ensure the backend engine is running.'
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="glass-dark flex flex-col h-[600px] rounded-2xl border-white/10 shadow-2xl">
            <div className="p-6 border-b border-white/10 flex items-center justify-between">
                <h2 className="text-xl font-serif text-accent text-glow font-bold">DIRP Research Copilot</h2>
                <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Intelligence Active</span>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/10">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50">
                        <div className="w-12 h-12 rounded-full border border-accent/30 flex items-center justify-center">
                            <svg className="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                            </svg>
                        </div>
                        <p className="text-sm font-serif italic">Ask about lineages, plantations, or specific archival nodes.</p>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] rounded-2xl p-4 ${msg.role === 'user'
                            ? 'bg-accent/20 border border-accent/30 text-accent-foreground'
                            : 'glass border border-white/10 text-foreground'
                            }`}>
                            <p className="text-sm leading-relaxed">{msg.content}</p>

                            {msg.evidence && msg.evidence.length > 0 && (
                                <div className="mt-4 pt-4 border-t border-white/10 space-y-2">
                                    <p className="text-[10px] uppercase tracking-widest text-accent font-bold">Archival Evidence</p>
                                    {msg.evidence.map((ev, j) => (
                                        <div key={j} className="text-[11px] bg-white/5 p-2 rounded border border-white/5">
                                            <span className="text-muted-foreground mr-2">[{ev.source}]</span>
                                            <span className="italic">"{ev.extracted_text}"</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {isTyping && (
                    <div className="flex justify-start">
                        <div className="glass border border-white/10 p-4 rounded-2xl flex space-x-2">
                            <div className="w-2 h-2 bg-accent/50 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                            <div className="w-2 h-2 bg-accent/50 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                            <div className="w-2 h-2 bg-accent/50 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                        </div>
                    </div>
                )}
            </div>

            <div className="p-6 border-t border-white/10">
                <div className="relative flex items-center">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                        placeholder="Ask the archives..."
                        className="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-6 pr-16 focus:outline-none focus:border-accent/50 transition-colors text-sm"
                    />
                    <button
                        onClick={handleAsk}
                        className="absolute right-2 p-2 text-accent hover:text-accent-foreground hover:bg-accent rounded-lg transition-all"
                    >
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
}
