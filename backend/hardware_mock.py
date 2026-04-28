import time
import json

class HardwareMock:
    def __init__(self, port="COM3", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        print(f"HardwareMock initialized on {port} at {baudrate} baud.")

    def send_command(self, protocol_data):
        """
        Simulates sending a command to the Arduino.
        In reality, this would use serial.write()
        """
        print(f"Connecting to hardware on {self.port}...")
        time.sleep(0.5) # Simulate latency
        
        payload = json.dumps(protocol_data)
        print(f"[SERIAL SEND] >>> {payload}")
        
        # Simulate processing time
        time.sleep(1)
        
        print("[SERIAL RCV] <<< { 'status': 'success', 'message': 'Stimulation Triggered' }")
        return {
            "status": "success", 
            "message": "Command executed successfully on simulated hardware.",
            "payload_sent": protocol_data
        }

hardware_interface = HardwareMock()
