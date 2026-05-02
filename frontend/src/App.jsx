import { useState, useEffect } from "react";
import ControlPanel from "./components/ControlPanel";
import ProtocolPanel from "./components/ProtocolPanel";
import Hand3D from "./components/Hand3D";
import { sendCommand, executeProtocol } from "./api";

function App() {
  const [currentProtocol, setCurrentProtocol] = useState(null);
  const [currentKey, setCurrentKey] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastLog, setLastLog] = useState(null);
  const [history, setHistory] = useState([]);
  const [errorMessage, setErrorMessage] = useState(null);
  const [executeSignal, setExecuteSignal] = useState(0);
  const [gltfFilename, setGltfFilename] = useState("test_model.gltf"); // Default: file exists in public/

  // --- Hand State ---
  // If no protocol is selected, we pass empty/defaults to Hand3D so it shows "Relaxed"
  const activeChannels = currentProtocol?.simulation_channels || [];
  const amplitude = currentProtocol?.parameters?.amplitude_mA || 0;
  const duration = currentProtocol?.parameters?.duration_s || 0;

  const handleAudioComplete = (result) => {
    if (result.transcribed_text) {
      console.log("Transcribed:", result.transcribed_text);
    }

    if (result.success) {
      setErrorMessage(null);
      setCurrentProtocol(result.protocol);
      setCurrentKey(result.detected_intent);
      setLastLog({
        type: "success",
        msg: `Identified: ${result.detected_intent}`,
      });
      setHistory((prev) =>
        [
          { text: result.transcribed_text || "Voice Command", success: true },
          ...prev,
        ].slice(0, 5),
      );
    } else {
      setErrorMessage(result.message || "Failed to recognize command.");
      setLastLog({
        type: "error",
        msg: result.message || "Failed to recognize command.",
      });
    }
  };

  const handleCommand = async (text) => {
    setIsProcessing(true);
    setCurrentProtocol(null);
    setErrorMessage(null);
    setLastLog({ type: "info", msg: "Processing command..." });

    try {
      const result = await sendCommand(text);

      if (result.success) {
        setErrorMessage(null);
        setCurrentProtocol(result.protocol);
        setCurrentKey(result.detected_intent);
        setLastLog({
          type: "success",
          msg: `Identified: ${result.detected_intent}`,
        });
        setHistory((prev) => [{ text, success: true }, ...prev].slice(0, 5));
      } else {
        setErrorMessage(result.message);
        setLastLog({ type: "error", msg: result.message });
      }
    } catch (error) {
      setErrorMessage("Failed to connect to backend.");
      setLastLog({ type: "error", msg: "Failed to connect to backend." });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExecute = async () => {
    if (!currentKey) return;

    setIsExecuting(true);
    setExecuteSignal(Date.now()); // Notify the Hand3D component to wait for the new GLTF
    try {
      const result = await executeProtocol(currentKey, currentProtocol);
      if (result && result.gltf_filename) {
        setGltfFilename(result.gltf_filename);
      }
      setLastLog({ type: "success", msg: "Signal Sent to Hardware" });
    } catch (e) {
      setLastLog({ type: "error", msg: "Hardware Error" });
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-blue-500/30 flex flex-col overflow-hidden">
      {/* Background Ambience */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-900/20 rounded-full blur-[128px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-900/20 rounded-full blur-[128px]"></div>
      </div>

      {/* --- TOP SECTION: Input & History --- */}
      <div className="z-10 w-full max-w-7xl mx-auto px-6 pt-6 pb-2">
        <div className="flex flex-col md:flex-row gap-6 items-start md:items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              3D Model
            </h1>
            <p className="text-gray-500 text-xs mt-1">
              Status: <span className="text-green-500">ONLINE</span>
            </p>
          </div>

          {/* Control Panel (Voice/Text Input) */}
          <div className="flex-1 w-full max-w-xl">
            <ControlPanel
              onCommandProcessed={handleCommand}
              onAudioComplete={handleAudioComplete}
              isProcessing={isProcessing}
              silenceTimeout={2500}
            />
          </div>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex gap-2 justify-center md:justify-start flex-wrap">
          {["Open Hand", "Close Hand", "Lateral Pinch", "Palmar Grasp"].map(
            (cmd) => (
              <button
                key={cmd}
                onClick={() => handleCommand(cmd)}
                className="text-xs py-1.5 px-3 rounded-full bg-gray-900 border border-gray-800 hover:border-blue-500 text-gray-400 hover:text-white transition-all"
              >
                {cmd}
              </button>
            ),
          )}
        </div>
      </div>

      {/* --- BOTTOM SECTION: Split View (Hand Left | Protocol Right) --- */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-4 z-10 grid grid-cols-1 lg:grid-cols-2 gap-6 h-[65vh]">
        {/* LEFT: 3D Hand Visualization (Always Visible) */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl overflow-hidden relative shadow-2xl backdrop-blur-sm h-full">
          <div className="absolute top-4 left-4 z-10 bg-black/60 px-2 py-1 rounded text-xs text-green-400 font-mono pointer-events-none">
            VISUALIZER
          </div>
          {/* We pass the active channels directly so it updates instantly 
                even if we haven't clicked 'Execute' yet. The 3D and Protocol update together.
            */}
          <Hand3D
            activeChannels={activeChannels}
            amplitude={amplitude}
            duration={duration}
            jointAngles={currentProtocol?.joint_angles || {}}
            executeSignal={executeSignal}
            isExecuting={isExecuting}
            gltfFilename={gltfFilename}
          />
        </div>

        {/* RIGHT: Protocol Details & Execution Controls */}
        <div className="h-full">
          <ProtocolPanel
            protocol={currentProtocol}
            onExecute={handleExecute}
            isExecuting={isExecuting}
            errorMessage={errorMessage}
          />
        </div>
      </main>

      {/* Logs Toast */}
      {lastLog && (
        <div className="fixed bottom-4 left-6 z-50 animate-fade-in-up">
          <div
            className={`px-4 py-2 rounded-lg text-xs font-mono border ${lastLog.type === "error" ? "bg-red-900/20 border-red-500/50 text-red-300" : "bg-gray-900 border-green-500/30 text-green-400"}`}
          >
            {">"} {lastLog.msg}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
