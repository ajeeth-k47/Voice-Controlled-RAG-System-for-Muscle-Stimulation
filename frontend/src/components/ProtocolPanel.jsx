
import React from 'react';

const ProtocolPanel = ({ protocol, onExecute, isExecuting, errorMessage }) => {
    if (errorMessage) {
        return (
            <div className="h-full flex items-center justify-center border border-red-800 rounded-2xl bg-red-900/10 p-6 animate-fade-in">
                <div className="text-center">
                    <div className="text-5xl mb-4">⚠️</div>
                    <h3 className="text-2xl font-bold text-red-500 mb-2">Movement Not Possible</h3>
                    <p className="text-red-300 font-light text-sm max-w-sm mx-auto">{errorMessage}</p>
                </div>
            </div>
        );
    }

    if (!protocol) {
        return (
            <div className="h-full flex items-center justify-center text-gray-500 border border-gray-800 rounded-2xl bg-gray-900/50">
                <p>Select a movement to see protocol details</p>
            </div>
        );
    }

    const { action, description, parameters, safety_warning } = protocol;

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col h-full animate-fade-in">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-900/40 to-purple-900/40 border-b border-gray-800 p-6">
                <h2 className="text-2xl font-bold text-white tracking-tight">{action}</h2>
                <p className="text-blue-300 text-sm mt-1 flex items-center gap-2">
                    <span className="block w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                    Protocol Optimized
                </p>
            </div>

            {/* Content */}
            <div className="p-6 flex-1 flex flex-col space-y-6 overflow-y-auto">

                {/* Description */}
                <div>
                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Description</h3>
                    <p className="text-gray-300 font-light text-sm">{description}</p>
                </div>

                {/* Stim Parameters */}
                <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-800">
                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Stimulation Config</h3>
                    <div className="space-y-2">
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
                <div className="mt-auto pt-4">
                    <button
                        onClick={onExecute}
                        disabled={isExecuting}
                        className="w-full rounded-xl bg-white text-black font-bold py-4 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 shadow-lg shadow-blue-500/10"
                    >
                        {isExecuting ? 'Sending to Hardware...' : 'Execute Protocol'}
                    </button>
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

export default ProtocolPanel;
