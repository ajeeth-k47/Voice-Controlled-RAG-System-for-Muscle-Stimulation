
EMS_PROTOCOLS = {
    "hand_open": {
        "action": "Hand Open",
        "description": "Full hand opening involves extension of all fingers and thumb.",
        "muscles": ["Extensor Digitorum Communis (EDC)", "Extensor Pollicis Longus (EPL)"],
        "opensim_muscles": ["EDCI", "EDCM", "EDCR", "EDCL", "EPL"],
        "electrodes": ["Forearm Dorsal", "Distal"],
        "electrode_placement_instruction": "Place one electrode on the back of your forearm, roughly 3 fingers below the elbow. Place the second electrode closer to the wrist on the same side.",
        "parameters": {
            "amplitude_mA": 18,
            "frequency_Hz": 35,
            "pulse_width_us": 250,
            "duration_s": 4
        },
        "simulation_channels": ["extensor_group"],
        "safety_warning": "Ensure electrodes are not directly on the ulnar bone pivot."
    },
    "palmar_grasp": {
        "action": "Palmar Grasp",
        "description": "Closing the hand to grasp a cylindrical object.",
        "muscles": ["Flexor Digitorum Superficialis (FDS)", "Flexor Digitorum Profundus (FDP)"],
        "opensim_muscles": ["FDSI", "FDSM", "FDSR", "FDSL", "FDPI", "FDPM", "FDPR", "FDPL"],
        "electrodes": ["Forearm Ventral", "Proximal"],
        "electrode_placement_instruction": "Place one electrode on the inner side of your forearm, near the elbow. Place the second electrode about 5cm lower towards the wrist.",
        "parameters": {
            "amplitude_mA": 20,
            "frequency_Hz": 40,
            "pulse_width_us": 300,
            "duration_s": 5
        },
        "simulation_channels": ["flexor_group"],
        "safety_warning": "Watch for prolonged contraction fatigue."
    },
    "lateral_pinch": {
        "action": "Lateral Pinch",
        "description": "Pinching with the thumb pad against the lateral aspect of the index finger.",
        "muscles": ["Adductor Pollicis", "First Dorsal Interosseous"],
        "opensim_muscles": ["FPL", "FDSI"],
        "electrodes": ["Thenar Eminence", "Dorsal Hand"],
        "electrode_placement_instruction": "Place one small electrode on the fleshy base of your thumb. Place the second one on the back of your hand, in the web space between thumb and index finger.",
        "parameters": {
            "amplitude_mA": 12,
            "frequency_Hz": 30,
            "pulse_width_us": 200,
            "duration_s": 3
        },
        "simulation_channels": ["lateral_pinch"],
        "safety_warning": "Use lower amplitude for hand muscles to avoid discomfort."
    },
    "wrist_extension": {
        "action": "Wrist Extension",
        "description": "Extension of the wrist joint to lift the hand.",
        "muscles": ["Extensor Carpi Radialis Longus/Brevis"],
        "opensim_muscles": ["ECRB", "ECRL", "ECU_pre-surgery"],
        "electrodes": ["Proximal Forearm Dorsal", "Lateral"],
        "electrode_placement_instruction": "Place one electrode on the outer back of the forearm near the elbow. Place the second one slightly below it along the muscle belly.",
        "parameters": {
            "amplitude_mA": 15,
            "frequency_Hz": 35,
            "pulse_width_us": 250,
            "duration_s": 3
        },
        "simulation_channels": ["extensor_group"],
        "safety_warning": "Do not place over the wrist joint itself."
    },
    "index_pointing": {
        "action": "Index Pointing",
        "description": "Isolated extension of the index finger.",
        "muscles": ["Extensor Indicis", "Extensor Digitorum Communis"],
        "opensim_muscles": ["EIP", "EDCI"],
        "electrodes": ["Distal Forearm Dorsal", "Lateral"],
        "electrode_placement_instruction": "Place one electrode on the back of the forearm, just above the wrist, aligned with the index finger. Place the reference spread apart on the forearm.",
        "parameters": {
            "amplitude_mA": 14,
            "frequency_Hz": 50,
            "pulse_width_us": 200,
            "duration_s": 2
        },
        "simulation_channels": ["index_group"],
        "safety_warning": "Precise placement required to avoid middle finger extension."
    },
    "thumb_opposition": {
        "action": "Thumb Opposition",
        "description": "Moving the thumb across the palm to touch fingertips.",
        "muscles": ["Opponens Pollicis", "Abductor Pollicis Brevis"],
        "opensim_muscles": ["EPL", "EPB", "APL"], 
        "electrodes": ["Thenar Eminence", "Dorsal Wrist"],
        "electrode_placement_instruction": "Place the active electrode on the fleshy pad at the base of your thumb (Thenar Eminence). Place the dispersive electrode on the back of your wrist.",
        "parameters": {
            "amplitude_mA": 12,
            "frequency_Hz": 30,
            "pulse_width_us": 250,
            "duration_s": 4
        },
        "simulation_channels": ["thumb_group"],
        "safety_warning": "Watch for thumb fatigue. Validated by Popovic et al."
    },
    "thumbs_up": {
        "action": "Thumbs Up",
        "description": "Thumb extended and abducted while fingers flexed.",
        "muscles": ["Extensor Pollicis Longus", "Extensor Pollicis Brevis", "Abductor Pollicis Longus"],
        "opensim_muscles": ["EPL", "EPB", "APL"],
        "electrodes": ["Dorsal Wrist", "Thumb Base"],
        "electrode_placement_instruction": "Place electrodes on the back of the thumb base and wrist to stimulate the extensors.",
        "parameters": {
            "amplitude_mA": 16,
            "frequency_Hz": 35,
            "pulse_width_us": 250,
            "duration_s": 5
        },
        "simulation_channels": ["thumbs_up"],
        "safety_warning": "Ensure precise placement to avoid index finger extension."
    },
    "wrist_flexion": {
        "action": "Wrist Flexion",
        "description": "Bending the wrist downwards (palm towards forearm).",
        "muscles": ["Flexor Carpi Radialis", "Flexor Carpi Ulnaris"],
        "opensim_muscles": ["FCR", "FCU"],
        "electrodes": ["Volar Forearm Proximal", "Mid-Forearm"],
        "electrode_placement_instruction": "Place one electrode on the inner forearm near the elbow (medial side). Place the second electrode about halfway down the inner forearm.",
        "parameters": {
            "amplitude_mA": 15,
            "frequency_Hz": 35,
            "pulse_width_us": 250,
            "duration_s": 3
        },
        "simulation_channels": ["flexor_group"],
        "safety_warning": "Avoid stimulating finger flexors too strongly (clenched fist)."
    }
}

def get_all_protocols():
    return list(EMS_PROTOCOLS.values())

def get_protocol_by_key(key):
    return EMS_PROTOCOLS.get(key)
