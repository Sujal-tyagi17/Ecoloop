import os
import json
import requests
from typing import Dict, Any, Tuple
from app.mcp_server import EcoLoopMCPServer
from app.fanger_pmv import calculate_pmv_ppd

class EcoLoopAgent:
    """
    Autonomous Open-Source LLM Agent leveraging MCP tool-calling protocol,
    Fanger PMV thermal comfort constraints, dynamic peak-shaving, and self-correcting decision loops.
    """

    def __init__(self, mcp_server: EcoLoopMCPServer = None, mode: str = "MCP_AI_Agent"):
        self.mcp_server = mcp_server or EcoLoopMCPServer()
        self.mode = mode
        self.decision_logs = []

    def decide(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Closed-loop agent execution method.
        Ingests real-time observation dict:
            {Tin, Tout, hour, rh, grid_carbon_g_kwh, electricity_rate_usd, occupants}
        Returns:
            {"cooling_setpoint": float, "hvac_kw": float or None, "reasoning": str, "tool_used": str}
        """
        Tin = observation.get("Tin", 22.0)
        Tout = observation.get("Tout", 25.0)
        hour = observation.get("hour", 12)
        carbon_g = observation.get("grid_carbon_g_kwh", 300.0)
        rate_usd = observation.get("electricity_rate_usd", 0.22)
        occupants = observation.get("occupants", 5)

        # 1. MCP Tool Execution: Calculate Fanger PMV at current indoor temp
        pmv_res = self.mcp_server.execute_tool(
            "calculate_fanger_pmv",
            {"ta": Tin, "rh": 50.0, "clo": 0.5 if 8 <= (hour % 24) <= 18 else 0.7, "met": 1.2 if occupants > 0 else 0.9},
            observation
        )
        current_pmv = pmv_res.get("pmv", 0.0)

        # 2. Decision logic depending on mode (supports Local LLM API / MCP Closed Loop AI)
        if self.mode == "OpenSource_LLM" and os.getenv("LLM_API_URL"):
            return self._call_external_oss_llm(observation, current_pmv)
        else:
            return self._autonomous_mcp_control_loop(observation, current_pmv, carbon_g, rate_usd)

    def _autonomous_mcp_control_loop(
        self,
        obs: Dict[str, Any],
        current_pmv: float,
        carbon_g: float,
        rate_usd: float
    ) -> Dict[str, Any]:
        """
        High-performance MCP Autonomous Decision Engine.
        Balances thermal comfort (PMV [-0.5, 0.5]), Peak Grid Carbon Shaving, and Electricity Cost.
        """
        Tin = obs["Tin"]
        Tout = obs["Tout"]
        hour = obs["hour"] % 24
        occupants = obs["occupants"]

        # Default occupied cooling setpoint
        base_setpoint = 23.0

        # Optimization Strategy Rules:
        # Rule 1: Pre-cooling strategy (14:00 - 16:00 before high carbon/cost peak)
        if 14 <= hour < 16 and carbon_g > 350:
            target_setpoint = 21.5
            reasoning = "Pre-cooling zone before peak electricity rates & carbon intensity surge."

        # Rule 2: Peak Shaving & High Carbon Avoidance (17:00 - 21:00)
        elif 17 <= hour <= 21 and carbon_g > 380:
            # Shift setpoint up slightly to reduce HVAC power while staying within PMV comfort limit (PMV < +0.45)
            # Check PMV at 24.5°C
            test_pmv, _, _ = calculate_pmv_ppd(ta=24.5, clo=0.5, met=1.2 if occupants > 0 else 0.9)
            if test_pmv <= 0.48:
                target_setpoint = 24.5
                reasoning = "Grid Carbon Peak Shaving: Raising cooling setpoint to 24.5 C while maintaining PMV comfort < +0.5."
            else:
                target_setpoint = 23.8
                reasoning = "Grid Carbon Reduction: Moderate setpoint increase to 23.8 C to satisfy PMV thermal bounds."

        # Rule 3: Unoccupied Night Setback (22:00 - 06:00)
        elif hour >= 22 or hour < 6:
            target_setpoint = 26.5
            reasoning = "Unoccupied Night Setback: Relaxing HVAC setpoint to 26.5 C to save baseline energy."

        # Rule 4: Moderate Daytime Operation
        else:
            if Tout > 28.0:
                target_setpoint = 23.0
                reasoning = "Active daytime cooling for office occupancy."
            elif Tout < 20.0:
                target_setpoint = 24.0
                reasoning = "Mild outdoor temperature; using energy conservation setpoint of 24.0 C."
            else:
                target_setpoint = 23.5
                reasoning = "Normal comfort balance setpoint."

        # Execute MCP IDF Update Tool Call (Forward Injection into IDF model)
        idf_tool_res = self.mcp_server.execute_tool(
            "update_idf_setpoint_schedule",
            {"cooling_setpoint": target_setpoint, "heating_setpoint": 20.0},
            obs
        )

        # Execute MCP HVAC Injection Tool Call
        self.mcp_server.execute_tool(
            "inject_hvac_control",
            {"cooling_setpoint": target_setpoint, "reasoning": reasoning},
            obs
        )

        log_entry = {
            "hour": obs["hour"],
            "Tin": Tin,
            "Tout": Tout,
            "PMV": current_pmv,
            "Target_Setpoint": target_setpoint,
            "Reasoning": reasoning,
            "MCP_Tool": "update_idf_setpoint_schedule -> inject_hvac_control"
        }
        self.decision_logs.append(log_entry)

        return {
            "cooling_setpoint": target_setpoint,
            "hvac_kw": None,  # Closed loop controls setpoint
            "reasoning": reasoning,
            "tool_used": "update_idf_setpoint_schedule"
        }

    def _call_external_oss_llm(self, obs: Dict[str, Any], current_pmv: float) -> Dict[str, Any]:
        """Calls external Open-Source LLM API (e.g. Ollama/vLLM/OpenAI compatible) with self-correction."""
        api_url = os.getenv("LLM_API_URL")
        prompt = (
            "System: You are an autonomous smart building HVAC optimization agent utilizing MCP tool calling.\n"
            f"Observation: Indoor Temp: {obs['Tin']} C, Outdoor Temp: {obs['Tout']} C, PMV Index: {current_pmv:.2f}, "
            f"Carbon Intensity: {obs['grid_carbon_g_kwh']} gCO2/kWh, Electricity Tariff: ${obs['electricity_rate_usd']}/kWh.\n"
            "Return JSON ONLY with schema: {\"cooling_setpoint\": float (20.0-26.0), \"reasoning\": string}"
        )
        try:
            resp = requests.post(api_url, json={"prompt": prompt, "max_tokens": 100}, timeout=2.0)
            data = resp.json()
            # Self-correction JSON extraction
            text = str(data.get("text", data.get("response", "")))
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                parsed = json.loads(text[start:end+1])
                c_set = float(parsed.get("cooling_setpoint", 23.0))
                c_set = max(20.0, min(26.0, c_set))
                return {
                    "cooling_setpoint": c_set,
                    "hvac_kw": None,
                    "reasoning": parsed.get("reasoning", "LLM setpoint optimization"),
                    "tool_used": "external_oss_llm"
                }
        except Exception as e:
            print(f"LLM API Call failed, self-correcting to fallback: {e}")

        # Fallback if API fails
        return self._autonomous_mcp_control_loop(obs, current_pmv, obs["grid_carbon_g_kwh"], obs["electricity_rate_usd"])
