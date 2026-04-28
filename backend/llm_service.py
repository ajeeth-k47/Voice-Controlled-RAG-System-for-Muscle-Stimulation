
import os
import json
from .database import EMS_PROTOCOLS
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Try to import OpenSim for dynamic model loading
try:
    import opensim as osim
    OPENSIM_AVAILABLE = True
except ImportError:
    OPENSIM_AVAILABLE = False
    print("Warning: OpenSim not found in current environment. Using fallback muscle list.")

# Load configured path from .env with fallback to wrist model
MODEL_PATH = os.environ.get("OPENSIM_MODEL_PATH", r"C:\OpenSim 4.5\Resources\Models\WristModel\wristmod2prueb2.osim")
llm_client = None
if "GROQ_API_KEY" not in os.environ:
    print("Warning: GROQ_API_KEY not found in environment. LLM features will be limited.")
else:
    print("GROQ_API_KEY found. Ready to use Groq LLM.")
    llm_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_live_model_data():
    """
    Dynamically loads the OpenSim model and returns actual muscle/joint names.
    Falls back to hardcoded list if model not found.
    """
    if OPENSIM_AVAILABLE and os.path.exists(MODEL_PATH):
        try:
            print(f"Loading OpenSim Model for LLM Context: {MODEL_PATH}")
            model = osim.Model(MODEL_PATH)
            model.initSystem()
            
            muscles = model.getMuscles()
            joints = model.getCoordinateSet()
            
            muscle_list = [muscles.get(i).getName() for i in range(muscles.getSize())]
            joint_list = [joints.get(i).getName() for i in range(joints.getSize())]
            
            return muscle_list, joint_list
        except Exception as e:
            print(f"Error loading OpenSim model: {e}")
    
    # FALLBACK LIST (If model fails)
    print("Using Fallback Muscle/Joint List")
    if "wrist" in MODEL_PATH.lower():
        fallback_muscles = [
            "FCR", "FCU", "PL", "ECRB", "ECRL", "ECU_pre-surgery", "ECU_post-surgery",
            "EDM", "EDCI", "EDCM", "EDCR", "EDCL", "EIP", "EPL", "EPB", "APL",
            "FDSI", "FDSM", "FDSR", "FDSL", "FDPI", "FDPM", "FDPR", "FDPL", "FPL"
        ]
        fallback_joints = [
            "flexion", "deviation", "thumb_abd", "thumb_flex", "TCP2M_flex", "TCP2M2_flex",
            "MCP2_flex", "PIP_flex", "DIP_flex", "MCP2M_flex", "MPIP_flex", "MDIP_flex",
            "RCP2M_flex", "RPIP_flex", "RDIP_flex", "LCP2M_flex", "LPIP_flex", "LDIP_flex"
        ]
    else:
        fallback_muscles = ['bflh_r', 'bfsh_r', 'ext_dig_r', 'ext_hal_r', 'flex_dig_r', 'flex_hal_r', 'gaslat_r']
        fallback_joints = ['hip_flexion_r', 'knee_angle_r', 'ankle_angle_r']
        
    return fallback_muscles, fallback_joints

# Load once at module level (or could be per request if model updates)
LIVE_MUSCLES, LIVE_JOINTS = get_live_model_data()


def _write_llm_debug_json(payload: dict) -> None:
    """Write last LLM result (debug)."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_path = os.path.join(project_root, "llm_last_result.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"[LLM DEBUG] Wrote: {out_path}")
    except Exception as e:
        print(f"[LLM DEBUG] Failed to write llm_last_result.json: {e}")

def translate_user_input_to_anatomy(user_input):
    """
    First pass LLM: Translates layman terms (like sign language or gestures) into explicit anatomical descriptions.
    """
    if not llm_client:
        return user_input
        
    prompt = f"""
    You are an expert Clinical Anatomist and Sign Language Translator.
    Your job is to translate the user's requested movement into an explicit, highly detailed anatomical description of exactly which fingers are extended/straight (0 degrees) and which are flexed/curled into the palm (90 degrees).

    User Request: "{user_input}"
    
    Rules:
    1. Focus on the thumb, index, middle, ring, and pinky fingers.
    2. If the user asks for a specific sign language letter (A, B, V, Y, etc.) or a common gesture ("I love you", "Call me", "OK Symbol"), explicitly describe the exact hand shape according to ASL or common knowledge.
       - A: Fist with thumb on side (thumb straight, all others curled).
       - B: Open hand, thumb curled across palm.
       - V: Peace sign (index/middle straight, ring/pinky curled, thumb curled over ring).
       - Y or 'Call me': Thumb and pinky straight, index, middle, ring curled.
       - 'I love you': Thumb, index, and pinky straight. Middle and ring curled.
       - 'Show ring finger': Ring finger straight. All other fingers and thumb curled.
       - 'OK Symbol': Thumb and index pinched together (45 deg). Middle, ring, pinky straight.
       - 'Thumbs down' or 'Thumb down': All fingers curled (90 deg). Thumb straight (0 deg). Wrist flexed downwards.
    3. Keep it purely descriptive of the physical state of the fingers (Straight vs Curled) and wrist.
    
    Output ONLY the anatomical description, nothing else.
    """
    try:
        response = llm_client.chat.completions.create(
            # Using 8B model for fast, cheap, and logical translation mapping
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Translation LLM Error: {e}")
        return user_input # Fallback

def parse_intent_with_llm(user_input):
    """
    Uses LLM API to parse the user input into a standardized intent.
    """
    if not llm_client:
        return {"error": "LLM client not available. Please set GROQ_API_KEY."}

    # FIRST PASS: Translate layman terms to anatomical descriptions
    print(f"Original Input: {user_input}")
    anatomical_description = translate_user_input_to_anatomy(user_input)
    print(f"Anatomical Translation: {anatomical_description}")

    # Choose highly-specific instructions based on the loaded model
    if "wrist" in MODEL_PATH.lower() or "hand" in MODEL_PATH.lower():
        special_instructions = """
    1. ANALYZE the movement: Which fingers move? Flexion or Extension?
    2. SELECT MUSCLES: Choose specific muscle slips from the available list.
       - IMPORTANT ABBREVIATIONS:
         FCR/FCU = Wrist Flexors. ECRB/ECRL/ECU = Wrist Extensors.
         FDS (Superficialis) / FDP (Profundus) = Finger Flexors. (I=Index, M=Middle, R=Ring, L=Little). Example: FDSI = Flex Index.
         EDC = Finger Extensors (I=Index, M=Middle, R=Ring, L=Little). Example: EDCI = Extend Index.
         Thumb: FPL = Flex Thumb. EPL/EPB = Extend Thumb. APL = Abduct Thumb.
         EIP = Extend Index finger only.
    3. ESTIMATE PARAMETERS: Provide a unique set of parameters (amplitude, frequency, pulse width) tailored for EACH muscle.
    3b. COMPUTE ACTIVATION (MUST MATCH CODE): For each muscle you return parameters for, compute the activation using EXACTLY this formula (same as convert_ems_to_activation):
        normalized_current = min(amplitude_mA / 30.0, 1.0)
        normalized_frequency = min(frequency_Hz / 50.0, 1.0)
        normalized_pulse_width = min(pulse_width_us / 400.0, 1.0)
        stimulus_strength = normalized_current * normalized_frequency * normalized_pulse_width
        activation = 1.0 / (1.0 + exp(-5.0 * (stimulus_strength - 0.5)))
        Output `activation` as a float in [0, 1] for that same muscle.
    4. ESTIMATE JOINT ANGLES: Provide the target angle (in degrees) for EVERY relevant finger joint to visualize the pose.
       - Use EXACT joint names from AVAILABLE JOINTS. Typical naming:
         * MCP (knuckles): 'MCP2_flex' (Index), 'MCP2M_flex' (Middle), 'RCP2M_flex' (Ring), 'LCP2M_flex' (Pinky).
         * PIP: 'PIP_flex', 'MPIP_flex', 'RPIP_flex', 'LPIP_flex'.
         * DIP (distal / fingertip): 'DIP_flex', 'MDIP_flex', 'RDIP_flex', 'LDIP_flex' — REQUIRED whenever that finger is curled; do not omit them.
         * Thumb: 'thumb_flex', 'thumb_abd', and often 'TCP2M_flex', 'TCP2M2_flex' for thumb–index/middle carpometacarpal coupling when pinching or combining thumb with digits.
         * Wrist: 'flexion', 'deviation'.
       - IMPORTANT LOGIC: 0 means the finger is perfectly STRAIGHT and pointing. Positive numbers (like 90) mean the finger is CURLED/CLOSED into the palm (Flexion).
       - Example A (Pointing): The pointing finger must be 0 (straight). The others must be 90 (curled out of the way).
       - Example B (Peace Sign): The Index and Middle fingers must be 0 (straight/pointing). The Ring and Pinky fingers must be 90 (curled closed).
       - Negative (-) is ONLY for extending the Wrist/Thumb backwards.
       - IMPORTANT: Do not include joints that do not exist in the AVAILABLE JOINTS list.
       - For each finger you curl, set MCP, PIP, and DIP together (typically the same target, e.g. 90° for a full curled finger).
    5. SIGN LANGUAGE & GESTURES MAPPING (CRITICAL FOR ACCURACY):
       - When curling a finger, you MUST set MCP, PIP, and DIP for that finger (e.g. MCP2_flex, PIP_flex, DIP_flex all 90 for a fully curled index).
       - For thumb combined with digits (pinch, pinch adjacent fingers): set thumb_flex/thumb_abd together with the relevant finger MCP/PIP/DIP and, if listed in AVAILABLE JOINTS, TCP2M_flex / TCP2M2_flex to realistic non-zero values.
       - If user asks for "Sign Language A", make a fist with thumb on side: thumb_flex=0, all others MCP/PIP/DIP 90 per finger.
       - If user asks for "Sign Language B", open hand with thumb crossed: thumb_flex=90, all others 0.
       - If user asks for "Sign Language V", peace sign: index=0, middle=0, ring(MCP/PIP)=90, pinky(MCP/PIP)=90.
       - If user asks for "Sign Language Y" or "Call Me", thumb & pinky out: thumb_flex=0, LCP2M_flex=0, LPIP_flex=0, others 90.
       - If user asks for "I Love You" sign: Thumb, Index, and Pinky are straight (0). Middle and Ring are curled (90).
       - If user asks to "Show ring finger": Ring finger is straight (RCP2M_flex=0, RPIP_flex=0). All other fingers and thumb are curled (90).
       - If user asks for "OK Symbol", pinch index & thumb to make an O, other 3 fingers straight: thumb_flex=45, MCP2_flex=45, PIP_flex=45, Middle/Ring/Pinky=0.
       - If user asks for "Thumbs down", curl all fingers (90) and keep thumb straight (0) but flex the wrist downwards to rotate the hand (flexion=70).
       - Only select muscles that correspond to flexing or extending the necessary fingers. For example, for "OK Symbol", activate muscles that flex the thumb (FPL, EPB) and flex the index finger (FDSI, FDPI).
        """
        json_example = """       {{
         "action_name": "<string: name of the requested movement>",
         "muscle_parameters": {{
            "<string: name of first muscle>": {{ "amplitude_mA": <int>, "frequency_Hz": <int>, "pulse_width_us": <int>, "activation": <float> }},
            "<string: name of second muscle>": {{ "amplitude_mA": <int>, "frequency_Hz": <int>, "pulse_width_us": <int>, "activation": <float> }}
         }},
         "joint_angles": {{
            "MCP2_flex": <int>,
            "PIP_flex": <int>,
            "DIP_flex": <int>,
            "MCP2M_flex": <int>,
            "MPIP_flex": <int>,
            "MDIP_flex": <int>,
            "RCP2M_flex": <int>,
            "RPIP_flex": <int>,
            "RDIP_flex": <int>,
            "LCP2M_flex": <int>,
            "LPIP_flex": <int>,
            "LDIP_flex": <int>,
            "thumb_flex": <int>,
            "thumb_abd": <int>,
            "TCP2M_flex": <int>,
            "TCP2M2_flex": <int>,
            "flexion": <int>,
            "deviation": <int>
         }}
       }}"""
    else:
        # UNIVERSAL OPENSIM INSTRUCTIONS
        # If the user loads a leg, arm, full body (like Rajagopal), or spine model, this logic will dynamically adapt.
        special_instructions = """
    1. ANALYZE the movement: Determine the gross anatomical action (e.g., knee flexion, shoulder abduction, hip extension).
    2. ANALYZE AVAILABLE MUSCLES & JOINTS: Look closely at the `AVAILABLE MUSCLES` and `AVAILABLE JOINTS` lists. You MUST deduce the acronyms and naming conventions the author of this specific `.osim` model used (e.g., 'gasmed_r' for medial gastrocnemius right in Rajagopal models).
    3. SELECT MUSCLES: Choose ONLY from the `AVAILABLE MUSCLES` list. Pick the specific agonist muscles required to perform the action.
    4. ESTIMATE PARAMETERS: Provide a unique set of parameters (amplitude, frequency, pulse width) tailored for EACH muscle you chose.
    4b. COMPUTE ACTIVATION (MUST MATCH CODE): For each muscle you return parameters for, compute the activation using EXACTLY this formula (same as convert_ems_to_activation):
        normalized_current = min(amplitude_mA / 30.0, 1.0)
        normalized_frequency = min(frequency_Hz / 50.0, 1.0)
        normalized_pulse_width = min(pulse_width_us / 400.0, 1.0)
        stimulus_strength = normalized_current * normalized_frequency * normalized_pulse_width
        activation = 1.0 / (1.0 + exp(-5.0 * (stimulus_strength - 0.5)))
        Include `activation` as a float in [0, 1] inside each muscle parameter object.
    5. ESTIMATE JOINT ANGLES: Provide the target angle (in degrees) for EVERY relevant joint to visualize the pose.
       - Use EXACT joint names from the `AVAILABLE JOINTS` list. Do NOT invent joint names.
       - IMPORTANT LOGIC: 0 is typically neutral/resting. Provide your best biomechanical estimate of the angles in degrees for the completed movement.
        """
        json_example = """       {{
         "action_name": "<string: name of the requested movement>",
         "muscle_parameters": {{
            "<string: name of first muscle>": {{ "amplitude_mA": <int>, "frequency_Hz": <int>, "pulse_width_us": <int>, "activation": <float> }},
            "<string: name of second muscle>": {{ "amplitude_mA": <int>, "frequency_Hz": <int>, "pulse_width_us": <int>, "activation": <float> }}
         }},
         "joint_angles": {{
            "<string: name of first relevant joint>": <int>,
            "<string: name of second relevant joint>": <int>
         }}
       }}"""

    prompt = f"""
    You are an expert Biomechanical Engineer and FES (Functional Electrical Stimulation) Controller.
    Your goal is to GENERATE a stimulation protocol for the USER'S REQUESTED MOVEMENT from scratch.
    
    AVAILABLE MUSCLES (From Loaded Model): {LIVE_MUSCLES}
    AVAILABLE JOINTS (From Loaded Model): {LIVE_JOINTS}
    
    USER REQUEST: "{user_input}"
    ANATOMICAL TRANSLATION (Use this as your strict guide!): "{anatomical_description}"
    
    INSTRUCTIONS:{special_instructions}
    
    5. RETURN JSON ONLY. Use the exact keys shown below but REPLACE the placeholder text with your generated integers/strings. For joint_angles, include as many keys from AVAILABLE JOINTS as needed.
    6. IMPORTANT: If the user requests a movement that is NOT POSSIBLE given the AVAILABLE MUSCLES and AVAILABLE JOINTS (e.g. asking a wrist model to kick, or leg model to grab), you MUST NOT hallucinate parameters. Instead, return ONLY this JSON:
       {{ "error": "This movement is not possible with the currently loaded OpenSim model." }}
       
{json_example}
    """

    if not llm_client:
        return {"error": "LLM client not available. Please set GROQ_API_KEY."}

    # ... prompt from before
    
    try:
        print("Sending request to Groq llama-3.3-70b-versatile...")
        response = llm_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert Biomechanical Engineer. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=800
        )
        
        response_content = response.choices[0].message.content
        print(f"Raw LLM Response: {response_content}")
        
        result = json.loads(response_content)
        
        # If the LLM didn't return a global parameters dict, pick the first muscle's params for UI default
        if "muscle_parameters" in result and result["muscle_parameters"]:
            muscles = list(result["muscle_parameters"].keys())
            result["muscles"] = muscles
            result["opensim_muscles"] = muscles
            # Take average or just the first one for the overall visualizer parameters
            if len(muscles) > 0:
                first_muscle_params = result["muscle_parameters"][muscles[0]]
                result["parameters"] = first_muscle_params
            else:
                 result["parameters"] = { "amplitude_mA": 15, "frequency_Hz": 40, "pulse_width_us": 300 }
            
        # Attach the first-pass translation to the final output so the frontend can display it!
        result["description"] = anatomical_description

        # Save the raw result so we can verify LLM-provided activations vs generated *_states.sto.
        _write_llm_debug_json(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "user_input": user_input,
                "anatomical_translation": anatomical_description,
                "llm_result": result,
            }
        )
        
        return result
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"error": str(e)}

