
import React, { useState, useEffect, useRef } from 'react';
import { API_URL } from '../api';

const ControlPanel = ({ onCommandProcessed, onAudioComplete, isProcessing, isListeningExternal, onListeningChange }) => {
    const [input, setInput] = useState("");
    const [isListening, setIsListening] = useState(false);
    const transcriptBufferRef = useRef("");
    const recognitionRef = useRef(null);

    // Notify parent
    useEffect(() => {
        if (onListeningChange) onListeningChange(isListening);
    }, [isListening, onListeningChange]);

    // External Control
    useEffect(() => {
        if (isListeningExternal === true && !isListening) {
            // If something external wants to trigger, we just trigger the function
            startListening();
        }
        // Note: We cannot "stop" the server-side recording once started easily from here, 
        // so we ignore isListeningExternal === false
    }, [isListeningExternal]);

    const getBrowserSpeechRecognition = () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return null;
        return SpeechRecognition;
    };

    const startListening = async () => {
        if (isListening) return;
        setIsListening(true);
        setInput(""); // Clear previous text
        transcriptBufferRef.current = "";

        const SpeechRecognition = getBrowserSpeechRecognition();
        if (SpeechRecognition) {
            try {
                const recognition = new SpeechRecognition();
                recognitionRef.current = recognition;

                recognition.lang = "en-US";
                recognition.interimResults = true;
                recognition.maxAlternatives = 1;
                recognition.continuous = false;

                recognition.onresult = (event) => {
                    let fullText = "";
                    for (let i = 0; i < event.results.length; i++) {
                        fullText += event.results[i][0].transcript;
                    }
                    const clean = (fullText || "").trim();
                    transcriptBufferRef.current = clean;
                    setInput(clean);
                };

                recognition.onerror = (event) => {
                    console.error("Browser STT error:", event?.error || event);
                };

                recognition.onend = async () => {
                    const finalText = (transcriptBufferRef.current || "").trim();

                    if (onAudioComplete) {
                        onAudioComplete({
                            success: !!finalText,
                            transcribed_text: finalText,
                            message: finalText ? undefined : "No speech detected.",
                        });
                    } else if (finalText && onCommandProcessed) {
                        onCommandProcessed(finalText);
                    }

                    setIsListening(false);
                };

                recognition.start();
                return;
            } catch (e) {
                console.error("Browser STT init failed, falling back:", e);
            }
        }

        console.log("Falling back to server-side listening...");

        try {
            // Call Backend
            const response = await fetch(`${API_URL}/api/listen`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();
            console.log("Listen result:", data);

            // Filter out punctuation-only transcriptions (e.g., "." from silence)
            if (data.transcribed_text) {
                const cleanText = data.transcribed_text.trim();
                // Only show if it contains at least one letter or number
                if (/[a-zA-Z0-9]/.test(cleanText)) {
                    setInput(cleanText);
                } else {
                    console.log("Ignoring punctuation-only transcription:", cleanText);
                }
            }

            // Brief delay so user can see the text before the UI changes
            await new Promise(r => setTimeout(r, 300));

            // Pass the full result up to App.jsx
            if (onAudioComplete) {
                onAudioComplete(data);
            } else if (onCommandProcessed && data.transcribed_text) {
                // Fallback if no specific audio handler
                onCommandProcessed(data.transcribed_text);
            }

        } catch (e) {
            console.error("Listening failed:", e);
            alert("Failed to connect to backend voice service. Is the server running?");
        } finally {
            setIsListening(false);
        }
    };

    const toggleListening = () => {
        if (isListening) {
            try {
                recognitionRef.current?.stop?.();
            } catch {
                // ignore
            }
            return;
        }
        startListening();
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (input.trim()) {
            onCommandProcessed(input);
            setInput("");
        }
    };

    return (
        <div className="w-full max-w-2xl mx-auto z-50 relative">
            <form onSubmit={handleSubmit} className="relative group">
                <div className={`
          relative flex items-center bg-gray-900 border 
          ${isListening ? 'border-red-500 shadow-[0_0_30px_rgba(239,68,68,0.4)]' : 'border-gray-700 shadow-xl'} 
          rounded-2xl transition-all duration-300
        `}>

                    <textarea
                        className="w-full bg-transparent text-white placeholder-gray-400 px-6 py-4 pr-32 text-lg focus:outline-none resize-none font-light leading-relaxed"
                        rows="1"
                        style={{ minHeight: '70px' }}
                        placeholder={isListening ? "Listening... (Pause to send)" : "Ask SERCS+ to move your hand..."}
                        value={input}
                        onChange={(e) => {
                            setInput(e.target.value);
                            transcriptBufferRef.current = e.target.value;
                        }}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit(e);
                            }
                        }}
                        disabled={isProcessing}
                    />

                    <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                        <button
                            type="button"
                            onClick={toggleListening}
                            className={`
                p-3 rounded-xl transition-all duration-200
                ${isListening
                                    ? 'bg-red-500/20 text-red-500 animate-pulse'
                                    : 'hover:bg-gray-800 text-gray-400 hover:text-white'}
              `}
                        >
                            {isListening ? (
                                <div className="flex gap-1 h-5 items-center">
                                    <span className="w-1 h-3 bg-red-500 animate-bounce"></span>
                                    <span className="w-1 h-5 bg-red-500 animate-bounce delay-75"></span>
                                    <span className="w-1 h-3 bg-red-500 animate-bounce delay-150"></span>
                                </div>
                            ) : (
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
                                </svg>
                            )}
                        </button>

                        <button
                            type="submit"
                            disabled={isProcessing || !input.trim()}
                            className={`
                p-3 rounded-xl transition-all duration-200
                ${input.trim() ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' : 'bg-gray-800 text-gray-600'}
              `}
                        >
                            {isProcessing ? (
                                <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                            ) : (
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                                </svg>
                            )}
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
};

export default ControlPanel;
