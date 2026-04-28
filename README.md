# **Voice Controlled EMS Simulation (Master Thesis)**

This application allows users to simulate hand/body movements based on LLM generated responses using the OpenSim simulation tool. It uses `"llama-3.3-70b-versatile"` to generate information about muscles, EMS parameters, the corresponding muscle activation values for each muscle, and joint angles that trigger the user requested movement.

Initially, the application used a ChromaDB vector database to store muscle and EMS values for 4–5 hand movements. Because that approach limited users to only the movements in the database, the current version uses the loaded OpenSim model information (available muscles and joints) together with the user prompt to generate any movement that is possible with the loaded model.

With further development, this prototype can be integrated with hardware (an EMS device) to help physiotherapists or wearable EMS systems for movement training, rehabilitation, and sports, without requiring manual EMS parameter configuration every time.


| Hand close | Kick | Peace sign |
| --- | --- | --- |
| <img src="gifs/handClose.gif" alt="Hand close demo" height="180" /> | <img src="gifs/Kick.gif" alt="Kick demo" height="180" /> | <img src="gifs/peaceSign.gif" alt="Peace sign demo" height="180" /> |

## **Instruction to run the application**

### **1. Prerequisites**
- Python 3.10.x, Node 18 or later
- OpenSim 4.5
- Conda/Miniconda (or any environment manager)
- GROQ API Key

### **2. Create an environment file with the following keys**
- GROQ_API_KEY: `<your API key>`
- OPENSIM_MODEL_PATH: `<path to an OpenSim model, e.g., wristmod2prueb2.osim or SoccerKickingModel.osim>`

### **3. Start the backend (FastAPI + simulation)**
- Create/activate a conda environment to run the application
- `conda activate <opensim-env>`
- `pip install -r requirements.txt`
- `python -m uvicorn backend.main:app --reload --port 8000`

### **4. Start the frontend (React app)**
- `cd frontend`
- `npm run dev`

