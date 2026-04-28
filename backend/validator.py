
"""
EMS Parameter Validator
Acts as the "Scientific Verification Layer" for the thesis.
Checks if the generated EMS parameters (Amplitude, Pulse Width, Duration)
fall within physiologically valid and safe ranges for specific movements.

Sources:
- Popovic et al., "Functional Electrical Stimulation for Grasping"
- Doucet et al., "Neuromuscular Electrical Stimulation for Skeletal Muscle Function"
"""

MOVEMENT_CONSTRAINTS = {
    "hand_open": {
        "min_amplitude": 15.0, # EDC usually requires higher current
        "max_amplitude": 40.0,
        "optimal_pulse_width": 250,
        "max_duration": 10.0, # Fatigue limit
        "target_muscle": "Extensor Digitorum Communis"
    },
    "palmar_grasp": {
        "min_amplitude": 18.0, # Flexors are stronger/deeper
        "max_amplitude": 50.0,
        "optimal_pulse_width": 300,
        "max_duration": 15.0,
        "target_muscle": "Flexor Digitorum Superficialis"
    },
    "index_pointing": {
        "min_amplitude": 12.0, # Smaller muscle (Extensor Indicis)
        "max_amplitude": 30.0,
        "optimal_pulse_width": 200,
        "max_duration": 8.0,
        "target_muscle": "Extensor Indicis"
    },
    "thumb_opposition": {
        "min_amplitude": 10.0, # Thenar muscles are sensitive
        "max_amplitude": 25.0,
        "optimal_pulse_width": 250,
        "max_duration": 10.0,
        "target_muscle": "Opponens Pollicis"
    },
    "wrist_extension": {
        "min_amplitude": 14.0,
        "max_amplitude": 45.0,
        "optimal_pulse_width": 250,
        "max_duration": 12.0,
        "target_muscle": "Extensor Carpi Radialis"
    }
}

def validate_parameters(movement_key, parameters):
    """
    Validates if the parameters are scientifically plausible.
    Returns: (is_valid, message)
    """
    MOVENENT_CONSTRAINTS = MOVEMENT_CONSTRAINTS # Handle typo in original if present or just reference local dict
    
    # GLOBAL SAFETY LIMITS (Scientific Source: Doucet et al., 2012)
    # Frequency: 35-50Hz (Optimal balance for contraction/fatigue)
    # Pulse Width: 200-400us (Optimal for comfort/efficacy)
    
    MAX_SAFE_AMPLITUDE = 60.0 # Standard pain threshold buffer
    MAX_SAFE_FREQUENCY = 50.0 # Upper limit per Doucet et al.
    MAX_SAFE_WIDTH = 400.0    # Upper limit per Doucet et al.
    
    amp = parameters.get("amplitude_mA", 0)
    freq = parameters.get("frequency_Hz", 0)
    width = parameters.get("pulse_width_us", 0)
    dur = parameters.get("duration_s", 0)

    # 0. Global Safety Check (Applies to ALL movements, known or unknown)
    if amp > MAX_SAFE_AMPLITUDE:
        return False, f"CRITICAL SAFETY: Amplitude {amp}mA exceeds global safe limit of {MAX_SAFE_AMPLITUDE}mA."
        
    if freq > MAX_SAFE_FREQUENCY:
        return False, f"SCIENTIFIC LIMIT: Frequency {freq}Hz exceeds optimal range ({MAX_SAFE_FREQUENCY}Hz) defined by Doucet et al. (2012) to minimize fatigue."
        
    if width > MAX_SAFE_WIDTH:
        return False, f"SCIENTIFIC LIMIT: Pulse Width {width}us exceeds optimal range ({MAX_SAFE_WIDTH}us) defined by Doucet et al. (2012)."

    if movement_key not in MOVEMENT_CONSTRAINTS:
        # Fallback for generative movements - passed global check
        return True, "Generative Protocol: Checked against Doucet et al. (2012) limits."
        
    rules = MOVEMENT_CONSTRAINTS[movement_key]
    
    # 1. Amplitude Check
    if amp < rules["min_amplitude"]:
        return False, f"Amplitude {amp}mA is too low for {rules['target_muscle']}. Min required: {rules['min_amplitude']}mA."
    
    if amp > rules["max_amplitude"]:
        return False, f"Amplitude {amp}mA exceeds safety limit ({rules['max_amplitude']}mA) for this muscle."
        
    # 2. Duration Check
    if dur > rules["max_duration"]:
        return False, f"Duration {dur}s exceeds fatigue limit ({rules['max_duration']}s) for {movement_key}."
        
    return True, f"Parameters verified against {rules['target_muscle']} physiology."
