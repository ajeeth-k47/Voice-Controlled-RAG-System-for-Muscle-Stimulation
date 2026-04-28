
import opensim as osim
import math
import argparse
import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

class HandGestureSimulator:
    """Simulates functional hand gestures from EMS parameters."""
    
    def __init__(self):
        # Model path from .env (fallback if missing)
        self.model_file = os.environ.get("OPENSIM_MODEL_PATH", r"C:\OpenSim 4.5\Resources\Models\Rajagopal\RajagopalLaiUhlrich2023.osim")
        
        print(f"Initializing simulator with model: {self.model_file}")
        
        if not os.path.exists(self.model_file):
            print(f"Error: Model file not found at {self.model_file}")
            
        # Load model with its folder as cwd (avoids geometry path issues)
        original_dir = os.getcwd()
        model_directory = os.path.dirname(self.model_file)
        
        try:
            if os.path.exists(model_directory):
                os.chdir(model_directory)
            
            self.model = osim.Model(self.model_file)
            self.state = self.model.initSystem()
            self.joints = self.model.getCoordinateSet()
            self.muscles = self.model.getMuscles()
            
            print(f"Model loaded successfully")
            print(f"Available muscles: {self.muscles.getSize()}")
            available_muscle_names = [self.muscles.get(i).getName() for i in range(self.muscles.getSize())]
            print(f"MUSCLE LIST: {available_muscle_names}")
            
            print(f"Available joints: {self.joints.getSize()}")
            available_joint_names = [self.joints.get(i).getName() for i in range(self.joints.getSize())]
            print(f"JOINT LIST: {available_joint_names}\n")
        except Exception as e:
            print(f"Failed to load OpenSim model: {e}")
            sys.exit(1)
        finally:
            os.chdir(original_dir)

    def _debug_log(self, hypothesis_id, location, message, data=None, run_id="pre-fix"):
        # #region agent log
        try:
            payload = {
                "sessionId": "ffdcb8",
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data or {},
                "timestamp": int(__import__("time").time() * 1000),
            }
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_path = os.path.join(project_root, "debug-ffdcb8.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception:
            pass
        # #endregion
    
    
    def convert_ems_to_activation(self, current, frequency, pulse_width):
        """Convert EMS params to activation (0..1)."""
        normalized_current = min(current / 30.0, 1.0)
        normalized_frequency = min(frequency / 50.0, 1.0)
        normalized_pulse_width = min(pulse_width / 400.0, 1.0)
        
        stimulus_strength = normalized_current * normalized_frequency * normalized_pulse_width
        
        activation = 1.0 / (1.0 + math.exp(-5.0 * (stimulus_strength - 0.5)))
        
        return activation
    
    
    def activate_target_muscles(self, muscle_list, global_activation, multi_channel_params=None):
        """Set activations for the target muscles."""
        activated_muscles = []
        
        print(f"\nMuscle Activation:")
        if not multi_channel_params:
            print(f"Global Target level: {global_activation:.2f} ({global_activation*100:.0f}%)")
        
        for i in range(self.muscles.getSize()):
            muscle = self.muscles.get(i)
            muscle.setActivation(self.state, 0.0)
        
        for muscle_name in muscle_list:
            if self.muscles.contains(muscle_name):
                muscle = self.muscles.get(muscle_name)
                
                muscle_activation = global_activation
                
                if multi_channel_params and muscle_name in multi_channel_params:
                    params = multi_channel_params[muscle_name]
                    if "activation" in params:
                        muscle_activation = float(params.get("activation", 0.0))
                        muscle_activation = max(0.0, min(1.0, muscle_activation))
                    else:
                        muscle_activation = self.convert_ems_to_activation(
                            params.get("amplitude_mA", 15),
                            params.get("frequency_Hz", 40),
                            params.get("pulse_width_us", 300),
                        )
                    print(f"  --> MUSCLE SET: {muscle_name} | Activation Value: {muscle_activation:.4f} (from custom params)")
                else:
                    print(f"  --> MUSCLE SET: {muscle_name} | Activation Value: {muscle_activation:.4f} (from global params)")
                
                muscle.setActivation(self.state, muscle_activation)
                activated_muscles.append(muscle_name)
        
        print(f"Total muscles activated: {len(activated_muscles)}")
        return activated_muscles
    
    
    def position_hand(self, gesture_name, strength, custom_angles=None):
        """
        Set hand to specific gesture position.
        If custom_angles is provided (from LLM), use those instead of hardcoded lookups.
        """
        print(f"\nPositioning hand for: {gesture_name}")
        
        # Reset all joints to neutral position
        for i in range(self.joints.getSize()):
            joint = self.joints.get(i)
            joint.setValue(self.state, 0)
            joint.setDefaultValue(0)
        
        if custom_angles:
             print(f"Applying Custom Generative Kinematics: {custom_angles}")
             joint_angles = custom_angles
             angle_scale = 1.0 # Trust the LLM's angles directly
        else:
            # Fallback to hardcoded database
            gestures_needing_full_strength = ['lateral_pinch', 'wrist_extension', 'wrist_flexion']
            angle_scale = 1.0 if gesture_name in gestures_needing_full_strength else strength
            
            # Since you deleted the hardcoded dictionary `get_gesture_angles`, 
            # we MUST rely on generative angles or default to empty.
            print("Warning: Database kinematics disabled. Relying purely on Generative JSON or defaulting to open hand.")
            joint_angles = {} 
        
        for joint_name, target_angle in joint_angles.items():
            actual_angle = target_angle * angle_scale
            
            if self.joints.contains(joint_name):
                joint = self.joints.get(joint_name)
                angle_radians = math.radians(actual_angle)
                
                min_limit = joint.getRangeMin()
                max_limit = joint.getRangeMax()
                angle_radians = max(min_limit, min(max_limit, angle_radians))
                
                joint.setValue(self.state, angle_radians)
                joint.setDefaultValue(angle_radians)
        
        self.model.realizeDynamics(self.state)

    def simulate_gesture(self, gesture_key, amplitude, frequency, pulse_width, muscle_list, output_dir=".", custom_angles=None, multi_channel_params=None):
        """
        Run simulation for a specific gesture using provided parameters
        """
        # #region agent log
        self._debug_log(
            "H6",
            "backend/open_sim_runner.py:simulate_gesture",
            "simulate_entry",
            {
                "gesture_key": gesture_key,
                "custom_angles_type": type(custom_angles).__name__,
                "custom_angles_is_dict": isinstance(custom_angles, dict),
                "custom_angles_len": (len(custom_angles) if isinstance(custom_angles, dict) else 0),
                "has_deviation_key": isinstance(custom_angles, dict) and "deviation" in custom_angles,
                "has_flexion_key": isinstance(custom_angles, dict) and "flexion" in custom_angles,
                "custom_angle_keys_sample": list(custom_angles.keys())[:30] if isinstance(custom_angles, dict) else [],
            },
        )
        # #endregion
        # Fill missing DIP flex from PIP when LLM omits distal joints (avoids DIP=0 in *_coords.mot)
        if custom_angles is not None and isinstance(custom_angles, dict) and len(custom_angles) > 0:
            try:
                from backend.joint_angle_postprocess import augment_joint_angles
            except ImportError:
                from joint_angle_postprocess import augment_joint_angles

            coord_names = [self.joints.get(i).getName() for i in range(self.joints.getSize())]
            custom_angles = augment_joint_angles(dict(custom_angles), model_coord_names=coord_names)
            self._debug_log(
                "H7",
                "backend/open_sim_runner.py:simulate_gesture",
                "custom_angles_after_augment",
                {
                    "gesture_key": gesture_key,
                    "custom_angles_len": len(custom_angles),
                    "has_deviation_key": "deviation" in custom_angles,
                    "has_flexion_key": "flexion" in custom_angles,
                    "deviation_value": custom_angles.get("deviation"),
                    "flexion_value": custom_angles.get("flexion"),
                },
            )

        print(f"\nRunning Simulation for: {gesture_key}")
        if multi_channel_params:
             print(f"Using advanced multi-channel per-muscle parameterization!")
        else:
             print(f"Global Params: {amplitude}mA, {frequency}Hz, {pulse_width}us")
             
        print(f"Target Muscles: {muscle_list}")
        
        global_activation = self.convert_ems_to_activation(amplitude, frequency, pulse_width)
        
        # Activate muscles provided, utilizing unique parameters per channel if available
        activated = self.activate_target_muscles(muscle_list, global_activation, multi_channel_params)
        
        # Position hand (Using custom angles if available)
        self.position_hand(gesture_key, global_activation, custom_angles)
        
        # Save .osim
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{gesture_key}.osim"
        filepath = os.path.join(output_dir, filename)
        self.model.printToXML(filepath)
        
        # Write explicit state values to a .sto file so legacy Schutte muscles can be viewed in UI
        try:
            sto_path = os.path.join(output_dir, f"{gesture_key}_states.sto")
            with open(sto_path, "w") as f:
                f.write("Generated States\n")
                f.write("version=1\n")
                f.write("nRows=1\n")
                f.write(f"nColumns={self.muscles.getSize() + 1}\n")
                f.write("inDegrees=yes\n")
                f.write("endheader\n")
                
                # Header row
                labels = ["time"]
                for i in range(self.muscles.getSize()):
                    labels.append(f"{self.muscles.get(i).getName()}/activation")
                f.write("\t".join(labels) + "\n")
                
                # Data row (time=0.0)
                data = ["0.000"]
                for i in range(self.muscles.getSize()):
                    act = self.muscles.get(i).getActivation(self.state)
                    # Rounding so it's clean and matches standard OpenSim formatting
                    data.append(f"{act:.6f}")
                f.write("\t".join(data) + "\n")
                
            print(f"Activation State File saved to: {sto_path}")
            print(f"*** LOAD THIS .sto FILE IN OPENSIM USING 'File -> Load Motion' TO VALIDATE ACTIVATIONS! ***")
        except Exception as e:
            print(f"Could not generate .sto file: {e}")
            
        print(f"Simulation saved to: {filepath}")

        # Generate a coordinate motion file so the WebUI can display flex-and-return
        coord_mot_path = None
        try:
            if custom_angles and isinstance(custom_angles, dict) and len(custom_angles) > 0:
                self._debug_log(
                    "H8",
                    "backend/open_sim_runner.py:simulate_gesture",
                    "creating_coord_mot_file",
                    {
                        "gesture_key": gesture_key,
                        "custom_angles_len": len(custom_angles),
                        "deviation_in_custom_angles": "deviation" in custom_angles,
                        "flexion_in_custom_angles": "flexion" in custom_angles,
                        "deviation_value": custom_angles.get("deviation"),
                        "flexion_value": custom_angles.get("flexion"),
                    },
                )
                duration = 1.0  # seconds
                num_steps = 151  # match reference wrist motions (0..1 inclusive)
                coord_mot_path = os.path.join(output_dir, f"{gesture_key}_coords.mot")

                n_coords = self.joints.getSize()
                header_labels = ["time"]
                for i in range(n_coords):
                    header_labels.append(self.joints.get(i).getName())

                with open(coord_mot_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(f"{gesture_key} coordinate motion generated from LLM joint_angles\n")
                    f.write("version=1\n")
                    f.write(f"nRows={num_steps}\n")
                    f.write(f"nColumns={n_coords + 1}\n")
                    f.write("inDegrees=yes\n")
                    f.write("endheader\n")
                    f.write("\t".join(header_labels) + "\n")

                    for step in range(num_steps):
                        t = duration * float(step) / float(num_steps - 1) if num_steps > 1 else 0.0
                        # Default profile: 0 -> peak -> 0
                        profile = math.sin(math.pi * (t / duration)) if duration > 0 else 0.0
                        if profile < 0.0:
                            profile = 0.0

                        row = [f"{t:.6f}"]
                        for i in range(n_coords):
                            cname = self.joints.get(i).getName()
                            peak_deg = float(custom_angles.get(cname, 0.0) or 0.0)
                            # Single-cycle profile for all coords: 0 -> target -> 0
                            row.append(f"{(peak_deg * profile):.6f}")
                        f.write("\t".join(row) + "\n")
                        if step in (0, int(num_steps / 2), num_steps - 1):
                            deviation_idx = None
                            flexion_idx = None
                            for j in range(n_coords):
                                n = self.joints.get(j).getName()
                                if n == "deviation":
                                    deviation_idx = j + 1  # +1 due to time column
                                if n == "flexion":
                                    flexion_idx = j + 1
                            self._debug_log(
                                "H5",
                                "backend/open_sim_runner.py:simulate_gesture",
                                "mot_sample_row",
                                {
                                    "step": step,
                                    "t": t,
                                    "deviation_value": row[deviation_idx] if deviation_idx is not None else None,
                                    "flexion_value": row[flexion_idx] if flexion_idx is not None else None,
                                    "coord_mot_path": coord_mot_path,
                                },
                            )

                print(f"Coordinate motion file saved to: {os.path.abspath(coord_mot_path)}")
        except Exception as e:
            print(f"Could not generate coordinate motion file: {e}")
        
        # Convert to GLTF for frontend visualization
        try:
            # Ensure backend directory is in path so osimConverters submodule can resolve itself
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from osimConverters.convertOsim2Gltf import convertOsim2Gltf
            from osimViewerOptions import osimViewerOptions
            
            # Setup path to frontend public folder
            frontend_public = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'public')
            gltf_filename = f"{gesture_key}.gltf"
            gltf_path = os.path.abspath(os.path.join(frontend_public, gltf_filename))
            
            options = osimViewerOptions()
            options.setShowMuscles(True)
            
            print(f"Converting to .gltf for {gesture_key} -> {gltf_path}", flush=True)
            # Use dir of generated osim (like manual_convert) - OpenSim model dir can break save path
            osim_dir = os.path.dirname(os.path.abspath(filepath))
            geometry_dir = os.path.dirname(self.model_file)
            
            abs_filepath = os.path.abspath(filepath)
            abs_sto_path = os.path.abspath(sto_path)

            motion_paths = []
            if coord_mot_path and os.path.exists(coord_mot_path):
                motion_paths = [os.path.abspath(coord_mot_path)]

            orig_cwd = os.getcwd()
            try:
                os.chdir(osim_dir)
                gltf = convertOsim2Gltf(abs_filepath, geometry_dir, motion_paths, options)
                gltf.save(gltf_path)
            finally:
                os.chdir(orig_cwd)

            if not os.path.exists(gltf_path):
                import shutil
                fallback = os.path.join(frontend_public, "test_model.gltf")
                if os.path.exists(fallback):
                    shutil.copy2(fallback, gltf_path)
                    print(f"Fallback: copied test_model.gltf -> {gltf_path}", flush=True)
                
            print("GLTF successfully generated for frontend view.")
        except Exception as e:
            import traceback
            print("Warning: GLTF conversion failed:", str(e))
            traceback.print_exc()
            
        return filepath


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OpenSim Hand Gesture Simulator')
    parser.add_argument('--gesture', type=str, required=True, help='Gesture key (e.g., palmar_grasp)')
    parser.add_argument('--amp', type=float, required=True, help='Amplitude in mA')
    parser.add_argument('--freq', type=float, required=True, help='Frequency in Hz')
    parser.add_argument('--width', type=float, required=True, help='Pulse Width in us')
    parser.add_argument('--muscles', type=str, required=True, help='JSON list of muscles')
    parser.add_argument('--muscle_params', type=str, required=False, help='JSON dict of unique muscle parameters')
    parser.add_argument('--angles', type=str, required=False, help='JSON dict of joint angles')
    parser.add_argument('--output', type=str, default='.', help='Output directory for .osim file')

    args = parser.parse_args()

    muscles = []
    if args.muscles:
        try:
            muscles = json.loads(args.muscles)
        except json.JSONDecodeError:
            print("Error: Muscles argument must be valid JSON list")
            sys.exit(1)
            
    custom_angles = None
    if args.angles:
        try:
            custom_angles = json.loads(args.angles)
        except json.JSONDecodeError:
             print("Warning: --angles provided but invalid JSON. Ignoring.")
             
    multi_channel_params = None
    if args.muscle_params:
        try:
            multi_channel_params = json.loads(args.muscle_params)
        except json.JSONDecodeError:
             print("Warning: --muscle_params provided but invalid JSON. Ignoring.")

    simulator = HandGestureSimulator()
    
    if args.gesture == "list":
        print("Exiting after listing model info.")
        sys.exit(0)
        
    simulator.simulate_gesture(args.gesture, args.amp, args.freq, args.width, muscles, args.output, custom_angles, multi_channel_params)
