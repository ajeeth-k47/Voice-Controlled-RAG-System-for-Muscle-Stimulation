from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import json
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our modules
from backend.database import get_protocol_by_key, get_all_protocols
from backend.vector_store import initialize_vector_db, search_movement
from backend.llm_service import parse_intent_with_llm
from backend.hardware_mock import hardware_interface
from backend.voice_service import listen_and_transcribe

app = FastAPI(title="SERCS+ API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all. In prod, lock this down.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "public")
app.mount("/static", StaticFiles(directory=frontend_public_dir), name="static")

# Initialize Vector DB on startup (Deprecated since switching to fully generative LLM)
@app.on_event("startup")
def startup_event():
    # initialize_vector_db()
    pass

class CommandRequest(BaseModel):
    text: str
    use_llm: bool = True

class ExecuteRequest(BaseModel):
    protocol_key: str
    custom_parameters: dict = None
    custom_muscle_parameters: dict = None
    custom_muscles: list = None
    custom_opensim_muscles: list = None
    custom_angles: dict = None

@app.get("/")
def read_root():
    return {"status": "online", "message": "SERCS+ API is running"}

@app.get("/api/protocols")
def get_protocols():
    return get_all_protocols()

@app.post("/api/listen")
def listen_for_command():
    """
    Records audio on the server (5s), transcribes it using Whisper,
    and then processes the text as a command.
    """
    print("Starting server-side recording...")
    text = listen_and_transcribe(duration=5)
    print(f"Transcribed: {text}")
    
    if not text:
        return {"success": False, "message": "No speech detected or transcription failed."}
        
    # Reuse the command processing logic
    # We can create a synthetic request object
    request = CommandRequest(text=text, use_llm=True)
    response = process_command(request)
    
    # Inject the transcribed text into the response so the frontend knows what was said
    if isinstance(response, dict):
        response["transcribed_text"] = text
        
    return response

@app.post("/api/command")
def process_command(request: CommandRequest):
    """
    Process a natural language command.
    - If use_llm is True and GROQ_API_KEY exists, use LLM for generative protocol.
    - Falls back to Vector Search if LLM is unavailable or returns no result.
    """
    
    # Check if we have an API key for Groq
    has_llm_key = "GROQ_API_KEY" in os.environ
    
    intent_key = None
    source = "vector_db"
    
    if request.use_llm and has_llm_key:
        print("Using LLM for intent parsing & parameter generation...")
        llm_result = parse_intent_with_llm(request.text)
        print(f"LLM Result: {llm_result}")
        
        if "error" in llm_result:
            return {
                "success": False,
                "message": llm_result["error"]
            }
        
        # Check if LLM returned a generative action name (or 'intent' from old prompt)
        action_name = llm_result.get("action_name") or llm_result.get("intent")
        
        if action_name:
            intent_key = action_name.lower().replace(" ", "_")
            source = "llm_generative"
            
            # --- FULLY GENERATIVE APPROACH ---
            # Construct protocol purely from LLM's biomechanical expertise
            protocol = {
                "key": intent_key,
                "action": action_name,
                "description": llm_result.get("description", "Generative movement based on biomechanical analysis."),
                "parameters": llm_result.get("parameters", { "amplitude_mA": 10, "frequency_Hz": 30, "pulse_width_us": 200 }),
                "muscles": llm_result.get("muscles", []),
                "opensim_muscles": llm_result.get("opensim_muscles", []),
                "muscle_parameters": llm_result.get("muscle_parameters", None),
                "joint_angles": llm_result.get("joint_angles", {}),
                # Add default metadata for frontend compatibility
                "electrodes": ["Custom Placement"],
                "electrode_placement_instruction": "Place electrodes on the target muscle bellies identified by the system.",
                "simulation_channels": [intent_key],
                "safety_warning": "Generated protocol. Verify validation messages."
            }
            
            return {
                "success": True,
                "source": source,
                "detected_intent": intent_key,
                "protocol": protocol,
                "llm_generated_params": True
            }
    
    # # Fallback to Vector Search if LLM is disabled or returned no action
    # if not intent_key:
    #     print("Using Vector Search fallback...")
    #     intent_key = search_movement(request.text)
    #     source = "vector_db"
    # 
    # if intent_key:
    #     protocol = get_protocol_by_key(intent_key)
    #     if protocol:
    #         return {
    #             "success": True,
    #             "source": source,
    #             "detected_intent": intent_key,
    #             "protocol": protocol,
    #             "llm_generated_params": False
    #         }

    return {
        "success": False,
        "message": f"I didn't recognize that movement. Try one of the quick-action buttons or rephrase your command."
    }

@app.post("/api/execute")
def execute_protocol(request: ExecuteRequest):
    """
    Send the protocol to the (mock) hardware.
    """
    # 1. Try to fetch from DB first
    protocol = get_protocol_by_key(request.protocol_key)
    
    # 2. If not in DB (Generative), create a skeleton from overrides
    if not protocol:
        if request.custom_parameters or request.custom_muscles:
             protocol = {
                "key": request.protocol_key,
                "action": request.protocol_key,
                "parameters": {},
                "muscles": [],
                "opensim_muscles": []
             }
        else:
            raise HTTPException(status_code=404, detail="Protocol not found and no overrides provided")

    # Apply Overrides (Dynamic Data from LLM/Frontend)
    if request.custom_parameters:
        print("[EXECUTE] Applying Custom Parameters")
        protocol['parameters'] = request.custom_parameters
    if request.custom_muscle_parameters:
        print("[EXECUTE] Applying Custom Muscle Parameters")
        protocol['muscle_parameters'] = request.custom_muscle_parameters
    if request.custom_muscles:
        protocol['muscles'] = request.custom_muscles
    if request.custom_opensim_muscles:
        protocol['opensim_muscles'] = request.custom_opensim_muscles
        
    angles_to_use = None
    if request.custom_angles:
        print("[EXECUTE] Applying Custom Joint Angles")
        angles_to_use = request.custom_angles


    # --- SCIENTIFIC VALIDATION LAYER ---
    # Before executing, verify parameters against physiological constraints
    from backend.validator import validate_parameters
    
    # For generative keys (not in DB), we might not have a specific validation profile.
    # The validator should handle 'unknown' keys by applying default safety limits.
    is_valid, validation_msg = validate_parameters(request.protocol_key, protocol.get("parameters", {}))
    
    print(f"[VALIDATOR] {validation_msg}")
    
    if not is_valid:
        # If scientifically unsafe/invalid, REJECT the command.
        return {
            "success": False,
            "message": f"Safety Protocol halted execution: {validation_msg}",
            "validation_error": True
        }

    # If valid, proceed to Hardware & Visualizer
    result = hardware_interface.send_command(protocol)
    
    # --- OPENSIM SIMULATION (In-process: ensures our code runs, no subprocess cache) ---
    try:
        from io import StringIO
        
        params = protocol.get("parameters", {})
        muscles = protocol.get("opensim_muscles", []) 
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        print(f"[OPENSIM] Running simulation in-process for {request.protocol_key}...")
        
        from backend.open_sim_runner import HandGestureSimulator
        sim = HandGestureSimulator()
        buf = StringIO()
        import sys
        _old_out, _old_err = sys.stdout, sys.stderr
        try:
            sys.stdout = sys.stderr = buf
            sim.simulate_gesture(
                request.protocol_key,
                params.get("amplitude_mA", 0),
                params.get("frequency_Hz", 0),
                params.get("pulse_width_us", 0),
                muscles,
                os.path.join(project_root, "simulations"),
                angles_to_use,
                protocol.get("muscle_parameters"),
            )
        finally:
            sys.stdout, sys.stderr = _old_out, _old_err
        with open(os.path.join(project_root, "simulation_log.txt"), "w") as f:
            f.write(buf.getvalue())
        print(f"[OPENSIM] Simulation complete.")
    except Exception as e:
        print(f"[OPENSIM] Failed to trigger simulation: {e}")
        import traceback
        traceback.print_exc()

    # Tell the frontend exactly what filename to expect
    result["gltf_filename"] = f"{request.protocol_key}.gltf"
    return result

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
