
import React from 'react';
import Hand3D from './Hand3D';

const SimulationView = ({ protocol, onConfirm, onCancel, isExecuting }) => {
    if (!protocol) return null;

    const { action, description, muscles, parameters, safety_warning, simulation_channels } = protocol;

    // Extract for animation
    const amplitude = parameters?.amplitude_mA || 0;
    const duration = parameters?.duration_s || 0;
    const activeChannels = simulation_channels || [];

    return (
        <div className="w-full max-w-6xl mx-auto mt-8 animate-fade-in-up">
            <div className="bg-gray-900 border border-gray-800 rounded-3xl overflow-hidden shadow-2xl">

                {/* Header */}
                <div className="bg-gradient-to-r from-blue-900/40 to-purple-900/40 border-b border-gray-800 p-6 flex justify-between items-center backdrop-blur">
                    <div>
                        <h2 className="text-2xl font-bold text-white tracking-tight">{action}</h2>
                        <p className="text-blue-300 text-sm mt-1 flex items-center gap-2">
                            <span className="block w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                            Protocol Optimized
                        </p>
                    </div>
                </div>

                <div className="p-8 grid grid-cols-1 lg:grid-cols-2 gap-8 h-[600px]">

                    {/* Left Column: 3D Visualization (The New Feature) */}
                    <div className="bg-black/50 rounded-2xl border border-gray-700 overflow-hidden relative">
                        <div className="absolute top-4 left-4 z-10 bg-black/60 px-2 py-1 rounded text-xs text-green-400 font-mono">
                            LIVE VISUALIZER
                        </div>
                        <Hand3D
                            activeChannels={activeChannels}
                            amplitude={amplitude}
                            duration={duration}
                        />
                    </div>

                    {/* Right Column: Parameters & Controls */}
                    <div className="flex flex-col h-full space-y-6 overflow-y-auto">

                        {/* Description */}
                        <div>
                            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Description</h3>
                            <p className="text-gray-300 font-light">{description}</p>
                        </div>

                        {/* Stim Parameters */}
                        <div className="bg-gray-800/30 rounded-xl p-6 border border-gray-800">
                            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">Stimulation Config</h3>
                            <div className="space-y-3">
                                <ParamRow label="Amplitude" value={parameters.amplitude_mA} unit="mA" />
                                <ParamRow label="Frequency" value={parameters.frequency_Hz} unit="Hz" />
                                <ParamRow label="Pulse Width" value={parameters.pulse_width_us} unit="µs" />
                            </div>
                        </div>

                        {/* Safety */}
                        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start gap-3">
                            <div className="text-red-500 mt-1">⚠️</div>
                            <p className="text-red-300/80 text-sm">{safety_warning}</p>
                        </div>

                        {/* Controls */}
                        <div className="mt-auto space-y-3 pt-4">
                            <button
                                onClick={onConfirm}
                                disabled={isExecuting}
                                className="w-full rounded-xl bg-white text-black font-bold py-4 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50"
                            >
                                {isExecuting ? 'Sending to Hardware...' : 'Execute Protocol'}
                            </button>

                            <button
                                onClick={onCancel}
                                disabled={isExecuting}
                                className="w-full py-3 text-gray-400 hover:text-white transition-colors text-sm hover:bg-white/5 rounded-xl border border-transparent hover:border-gray-700"
                            >
                                ← Back to Home
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const ParamRow = ({ label, value, unit }) => (
    <div className="flex justify-between items-end border-b border-gray-700/50 pb-2">
        <span className="text-gray-400 text-sm">{label}</span>
        <div className="text-right">
            <span className="text-white font-mono text-lg font-medium">{value}</span>
            <span className="text-gray-600 text-xs ml-1 font-bold">{unit}</span>
        </div>
    </div>
);

export default SimulationView;
