import opensim as osim
import os

def save_activation_states(model, state, activated_muscles, output_dir, gesture_name):
    """
    Saves the live activation values out to a .sto file so they can be loaded
    directly into the OpenSim GUI for visual validation of legacy muscles.
    """
    try:
        # Create a new Storage object to hold state data
        state_storage = osim.Storage()
        state_storage.setName(f"{gesture_name}_activations")
        
        # We need a column for time, and a column for each muscle activation
        labels = osim.ArrayStr()
        labels.append("time")
        
        for i in range(model.getMuscles().getSize()):
            muscle = model.getMuscles().get(i)
            labels.append(f"{muscle.getName()}/activation")
            
        state_storage.setColumnLabels(labels)
        
        # Get the actual activation values from the live physics state
        row = osim.StateVector()
        row.setSystemTime(0.0) # We only need 1 frame of time for a static pose
        
        for i in range(model.getMuscles().getSize()):
            muscle = model.getMuscles().get(i)
            # Retrieve the activation from the physics state memory
            act_val = muscle.getActivation(state)
            row.getData().append(act_val)
            
        state_storage.append(row)
        
        # Save to disk
        sto_path = os.path.join(output_dir, f"{gesture_name}_states.sto")
        state_storage.printResult(state_storage, gesture_name, sto_path, 0.0, "", "")
        
        print(f"Validation states saved to: {sto_path}")
        return sto_path
    
    except Exception as e:
        print(f"Could not save states for validation: {e}")
        return None
