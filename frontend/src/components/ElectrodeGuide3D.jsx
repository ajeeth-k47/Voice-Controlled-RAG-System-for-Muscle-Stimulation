
import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Html } from '@react-three/drei';

// Coordinate Mapping for Electrode Positions
// Arm is roughly aligned along the Y-axis. 
// Shoulder at Top (Y+), Hand at Bottom (Y-).
// Center (0,0,0) is elbow.
const ELECTRODE_POSITIONS = {
    // Dorsal (Back of Forearm) - Z is positive
    "Forearm Dorsal": [0.5, -1.5, 0.9],
    "Proximal Forearm Dorsal": [0.4, -0.5, 1.0],
    "Distal Forearm Dorsal": [0.3, -3.5, 0.7],

    // Ventral (Inner Forearm) - Z is negative
    "Forearm Ventral": [0.3, -2.0, -0.9],
    "Volar Forearm Proximal": [0.2, -0.8, -1.0],
    "Mid-Forearm": [0.3, -2.5, -0.8],
    "Proximal": [0.2, -0.8, -1.0],

    // Specific
    "Distal": [0.3, -3.5, 0.7],
    "Lateral": [1.0, -1.0, 0], // Outer side
    "Ulnar Side": [-1.0, -1.0, 0], // Inner Edge (Pinky side)

    // Hand / Wrist
    "Dorsal Wrist": [0, -4.2, 0.8],
    "Dorsal Hand": [0, -5.5, 0.6],
    "Dorsal Web Space": [0.8, -5.2, 0.5],
    "Thenar Eminence": [0.8, -5.0, -0.5], // Thumb pad (Ventral side)
};

const ArmModel = () => {
    return (
        <group>
            {/* Upper Arm (Top cylinder) */}
            <mesh position={[0, 1.5, 0]}>
                <cylinderGeometry args={[0.9, 0.8, 3, 32]} />
                <meshStandardMaterial color="#334155" roughness={0.5} />
            </mesh>

            {/* Elbow Joint (Sphere) */}
            <mesh position={[0, -0.1, 0]}>
                <sphereGeometry args={[0.85, 32, 32]} />
                <meshStandardMaterial color="#475569" metalness={0.5} />
            </mesh>

            {/* Forearm (Main area of interest) */}
            <mesh position={[0, -2.2, 0]}>
                <cylinderGeometry args={[0.8, 0.6, 4, 32]} />
                <meshStandardMaterial color="#1e293b" />
            </mesh>

            {/* Wrist (Sphere) */}
            <mesh position={[0, -4.3, 0]}>
                <sphereGeometry args={[0.65, 32, 32]} />
                <meshStandardMaterial color="#475569" metalness={0.5} />
            </mesh>

            {/* Hand (Box approximation) */}
            <mesh position={[0, -5.5, 0]}>
                <boxGeometry args={[1.2, 1.8, 0.5]} />
                <meshStandardMaterial color="#334155" />
            </mesh>

            {/* Thumb (Small Cylinder) */}
            <mesh position={[0.8, -5.2, -0.2]} rotation={[0, 0, -0.5]}>
                <cylinderGeometry args={[0.3, 0.35, 1.2, 16]} />
                <meshStandardMaterial color="#334155" />
            </mesh>

            {/* Labels */}
            <Html position={[1.5, 2, 0]}>
                <div className="bg-gray-900/80 text-white text-xs px-2 py-1 rounded pointer-events-none">Shoulder</div>
            </Html>
            <Html position={[-1.5, 0, 0]}>
                <div className="bg-gray-900/80 text-white text-xs px-2 py-1 rounded pointer-events-none">Elbow</div>
            </Html>
            <Html position={[1.5, -5.5, 0]}>
                <div className="bg-gray-900/80 text-white text-xs px-2 py-1 rounded pointer-events-none">Hand</div>
            </Html>
        </group>
    );
}

const ElectrodeMarker = ({ position, label }) => {
    const ref = useRef();

    useFrame((state) => {
        const t = state.clock.getElapsedTime();
        ref.current.scale.setScalar(1 + Math.sin(t * 10) * 0.1); // Pulse effect
    });

    return (
        <group position={position}>
            {/* Glowing sphere */}
            <mesh ref={ref}>
                <sphereGeometry args={[0.15, 32, 32]} />
                <meshStandardMaterial color="#3b82f6" emissive="#60a5fa" emissiveIntensity={2} toneMapped={false} />
            </mesh>

            {/* Light emitter */}
            <pointLight color="#3b82f6" intensity={1} distance={1} />

            {/* Label */}
            <Html position={[0.2, 0.2, 0]}>
                <div className="bg-blue-600/90 text-white text-[10px] font-bold px-2 py-1 rounded border border-blue-400 whitespace-nowrap shadow-lg">
                    {label}
                </div>
            </Html>
        </group>
    )
}

const ElectrodeGuide3D = ({ protocol, mode }) => {

    // Determine positions based on protocol strings
    const markers = protocol?.electrodes.map(name => {
        // Fuzzy match or exact match from our map
        let pos = ELECTRODE_POSITIONS[name];

        // Fallback if not found (default to mid-forearm dorsal)
        if (!pos) {
            // Try searching for keywords
            if (name.includes("Thenar")) pos = ELECTRODE_POSITIONS["Thenar Eminence"];
            else if (name.includes("Dorsal")) pos = ELECTRODE_POSITIONS["Forearm Dorsal"];
            else if (name.includes("Ventral")) pos = ELECTRODE_POSITIONS["Forearm Ventral"];
            else pos = [0, -2, 1]; // Default
        }
        return { name, pos };
    }) || [];

    return (
        <div className={`
             relative w-full h-[400px] bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-3xl border border-gray-700 overflow-hidden shadow-2xl
             ${mode === 'confirmation' ? 'border-blue-500 shadow-blue-500/20' : ''}
        `}>
            {/* Instructions Overlay */}
            <div className="absolute top-4 left-4 z-10 pointer-events-none">
                <h3 className="text-gray-400 text-xs font-bold tracking-widest uppercase mb-1">
                    3D Interaction
                </h3>
                <p className="text-xs text-gray-500">
                    Left Click to Rotate • Scroll to Zoom
                </p>
            </div>

            <Canvas camera={{ position: [4, -2, 5], fov: 45 }}>
                <ambientLight intensity={0.5} />
                <directionalLight position={[5, 5, 5]} intensity={1} />
                <directionalLight position={[-5, 5, -5]} intensity={0.5} />

                <ArmModel />

                {markers.map((m, i) => (
                    <ElectrodeMarker key={i} position={m.pos} label={m.name} />
                ))}

                <OrbitControls
                    target={[0, -2, 0]}
                    minDistance={3}
                    maxDistance={10}
                    enablePan={false}
                />
            </Canvas>
        </div>
    );
};

export default ElectrodeGuide3D;
