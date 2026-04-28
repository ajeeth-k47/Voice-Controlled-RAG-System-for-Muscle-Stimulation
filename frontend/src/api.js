export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const sendCommand = async (text) => {
    const response = await fetch(`${API_URL}/api/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, use_llm: true }),
    });
    return response.json();
};

export const executeProtocol = async (protocolKey, protocolData = null) => {
    const payload = { protocol_key: protocolKey };

    if (protocolData) {
        // Pass dynamic overrides if they exist (from LLM)
        if (protocolData.parameters) payload.custom_parameters = protocolData.parameters;
        if (protocolData.muscle_parameters) payload.custom_muscle_parameters = protocolData.muscle_parameters;
        if (protocolData.muscles) payload.custom_muscles = protocolData.muscles;
        if (protocolData.opensim_muscles) payload.custom_opensim_muscles = protocolData.opensim_muscles;
        if (protocolData.joint_angles) payload.custom_angles = protocolData.joint_angles;
    }

    const response = await fetch(`${API_URL}/api/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    return response.json();
};
