
import React from 'react';

const ElectrodeGuide = ({ protocol, mode }) => {
    // If we had real images, we'd map protocol.action to an image path
    // For now, we use a schematic visualization

    return (
        <div className={`
        relative w-full max-w-sm mx-auto aspect-square bg-gray-900 rounded-3xl border border-gray-700 p-6 flex flex-col items-center justify-center
        ${mode === 'confirmation' ? 'animate-pulse border-blue-500 shadow-[0_0_30px_rgba(59,130,246,0.2)]' : ''}
    `}>
            <h3 className="text-gray-400 text-xs font-bold tracking-widest uppercase mb-4">Electrode Placement Guide</h3>

            {/* Schematic Arm */}
            <div className="relative w-48 h-64 bg-gray-800 rounded-2xl border-4 border-gray-700 flex items-center justify-center">
                {/* Simple representations of arm segments */}

                {/* Upper Arm */}
                <div className="absolute top-0 w-32 h-24 bg-gray-700/50 rounded-t-xl border-b border-gray-600"></div>

                {/* Forearm (Where most electrodes go) */}
                <div className="absolute bottom-0 w-28 h-36 bg-gray-700/50 rounded-b-xl border-t border-gray-600"></div>

                {/* Electrodes Overlay - Random positioning logic for demo purposes or mapped if possible */}
                {/* We'll use the 'muscles' array to decide roughly where to show dots */}

                {protocol?.muscles.map((muscle, i) => (
                    <div
                        key={muscle}
                        className="absolute flex items-center justify-center w-8 h-8 rounded-full bg-blue-500/20 border-2 border-blue-400 shadow-lg shadow-blue-500/50 animate-bounce"
                        style={{
                            // Pseudo-random positions based on index to differentiate muscles
                            top: `${30 + (i * 20)}%`,
                            left: `${20 + (i * 30)}%`
                        }}
                    >
                        <div className="w-2 h-2 bg-white rounded-full"></div>

                        {/* Label */}
                        <div className="absolute left-full ml-2 bg-gray-900 text-white text-[10px] px-2 py-1 rounded whitespace-nowrap border border-gray-700">
                            {muscle}
                        </div>
                    </div>
                ))}

            </div>

            <p className="mt-6 text-sm text-center text-blue-200 font-medium">
                Attach electrodes to the highlighted <span className="text-white font-bold">{protocol?.muscles.join(" & ")}</span> muscles.
            </p>
        </div>
    );
};

export default ElectrodeGuide;
