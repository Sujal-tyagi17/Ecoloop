import json
from typing import Dict, Any, List
from app.fanger_pmv import calculate_pmv_ppd
from app.idf_tools import IDFManager

class EcoLoopMCPServer:
    """
    Model Context Protocol (MCP) Server for EcoLoop Smart Building Agents.
    Exposes tool schemas and handles agent JSON-RPC tool calls.
    """

    def __init__(self, idf_filepath: str = "data/baseline_building.idf"):
        self.idf_filepath = idf_filepath
        self.tools = self._register_tools()
        self.call_log: List[Dict[str, Any]] = []

    def _register_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_building_sensors",
                "description": "Read real-time environmental sensors from EnergyPlus simulation (Tin, Tout, Occupants, Carbon Intensity, Electricity Rate).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hour": {"type": "integer", "description": "Current simulation hour"}
                    },
                    "required": ["hour"]
                }
            },
            {
                "name": "calculate_fanger_pmv",
                "description": "Compute predicted mean vote (PMV) thermal comfort index based on ISO 7730.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ta": {"type": "number", "description": "Air temperature C"},
                        "rh": {"type": "number", "description": "Relative humidity %"},
                        "clo": {"type": "number", "description": "Clothing insulation clo"},
                        "met": {"type": "number", "description": "Metabolic rate met"}
                    },
                    "required": ["ta"]
                }
            },
            {
                "name": "update_idf_setpoint_schedule",
                "description": "Update EnergyPlus IDF file thermostat setpoints and save forward injection file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cooling_setpoint": {"type": "number", "description": "Cooling setpoint C (e.g. 23.5)"},
                        "heating_setpoint": {"type": "number", "description": "Heating setpoint C (e.g. 20.0)"}
                    },
                    "required": ["cooling_setpoint"]
                }
            },
            {
                "name": "inject_hvac_control",
                "description": "Inject dynamic HVAC control setpoint or power override into simulation engine.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cooling_setpoint": {"type": "number", "description": "Optimal target cooling temperature"},
                        "hvac_kw_limit": {"type": "number", "description": "Maximum allowed cooling power kW"},
                        "reasoning": {"type": "string", "description": "LLM step-by-step optimization reasoning"}
                    },
                    "required": ["cooling_setpoint", "reasoning"]
                }
            }
        ]

    def list_tools(self) -> List[Dict[str, Any]]:
        return self.tools

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Executes tool call and records trace telemetry log."""
        result = {}
        if tool_name == "get_building_sensors":
            result = {
                "Tin": state.get("Tin", 22.0),
                "Tout": state.get("Tout", 25.0),
                "grid_carbon_g_kwh": state.get("grid_carbon_g_kwh", 300.0),
                "electricity_rate_usd": state.get("electricity_rate_usd", 0.22),
                "occupants": state.get("occupants", 5)
            }
        elif tool_name == "calculate_fanger_pmv":
            ta = arguments.get("ta", state.get("Tin", 22.0))
            rh = arguments.get("rh", state.get("rh", 50.0))
            clo = arguments.get("clo", 0.5)
            met = arguments.get("met", 1.2)
            pmv, ppd, cat = calculate_pmv_ppd(ta=ta, rh=rh, clo=clo, met=met)
            result = {"pmv": pmv, "ppd": ppd, "category": cat, "in_comfort_bounds": -0.5 <= pmv <= 0.5}
        elif tool_name == "update_idf_setpoint_schedule":
            c_set = float(arguments.get("cooling_setpoint", 23.0))
            h_set = float(arguments.get("heating_setpoint", 20.0))
            idf_mgr = IDFManager(self.idf_filepath)
            updated_text = idf_mgr.update_dual_setpoints(h_set, c_set)
            IDFManager.save_idf(updated_text, "data/optimized_ecm.idf")
            result = {
                "status": "IDF Updated Successfully",
                "new_cooling_setpoint": c_set,
                "new_heating_setpoint": h_set,
                "saved_to": "data/optimized_ecm.idf"
            }
        elif tool_name == "inject_hvac_control":
            c_set = float(arguments.get("cooling_setpoint", 23.0))
            reasoning = arguments.get("reasoning", "Optimizing for thermal comfort & carbon intensity")
            result = {
                "action_applied": True,
                "target_cooling_setpoint": c_set,
                "hvac_kw_limit": arguments.get("hvac_kw_limit", None),
                "reasoning": reasoning
            }
        else:
            result = {"error": f"Unknown MCP tool: {tool_name}"}

        tool_call_log = {
            "hour": state.get("hour", 0),
            "tool": tool_name,
            "args": arguments,
            "result": result
        }
        self.call_log.append(tool_call_log)
        return result
