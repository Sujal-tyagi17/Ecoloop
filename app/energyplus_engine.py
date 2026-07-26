import os
import json
import math
import random
import csv
import shutil
from typing import Dict, Any, List, Tuple, Optional

# Try importing numpy and pandas, fallback to pure python builtins if Windows AppLocker blocks DLLs
try:
    import pandas as pd
except Exception:
    pd = None

try:
    import numpy as np
except Exception:
    np = None

from app.fanger_pmv import calculate_pmv_ppd, evaluate_comfort_score
from app.idf_tools import IDFManager

def find_energyplus_executable() -> Optional[str]:
    """Try common locations and environment variable ENERGYPLUS_PATH to locate EnergyPlus executable."""
    env = os.getenv('ENERGYPLUS_PATH')
    if env and os.path.exists(env):
        return env
    for name in ('energyplus', 'energyplus.exe'):
        path = shutil.which(name)
        if path:
            return path
    possible = [
        r"C:\EnergyPlus\energyplus.exe",
        r"C:\Program Files\EnergyPlus\energyplus.exe",
    ]
    for p in possible:
        if os.path.exists(p):
            return p
    return None

def run_idf(idf_path: str, output_dir: str) -> dict:
    """Run EnergyPlus on an IDF file if EnergyPlus is installed."""
    exe = find_energyplus_executable()
    if not exe:
        raise RuntimeError('EnergyPlus executable not found. Set ENERGYPLUS_PATH or install EnergyPlus.')

    os.makedirs(output_dir, exist_ok=True)
    cmd = [exe, '-r', '-d', output_dir, idf_path]
    try:
        import subprocess
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {'success': True, 'output_dir': output_dir}
    except Exception as e:
        return {'success': False, 'error': str(e)}

class EnergyPlusSimulationEngine:
    """
    High-fidelity Building Sandbox Engine.
    Executes EnergyPlus IDF models or full physics-based thermal & PMV co-simulation.
    Supports both Pandas DataFrames and Pure Python Data Structure Fallbacks.
    """

    def __init__(
        self,
        idf_path: str = "data/baseline_building.idf",
        zone_volume_m3: float = 300.0,
        c_zone: float = 2.5,        # Zone thermal heat capacity (kWh/°C)
        r_envelope: float = 4.2,    # Envelope thermal resistance (°C/kW)
        cop_nominal: float = 3.2,   # HVAC nominal COP
    ):
        self.idf_path = idf_path
        self.idf_manager = IDFManager(idf_path) if os.path.exists(idf_path) else None
        self.zone_volume = zone_volume_m3
        self.C_zone = c_zone
        self.R_envelope = r_envelope
        self.cop_nominal = cop_nominal

        # Check for installed EnergyPlus binary
        self.ep_binary = find_energyplus_executable()
        self.is_real_ep_available = self.ep_binary is not None

        # Simulation state
        self.reset()

    def reset(self, initial_temp: float = 22.0):
        self.current_tin = initial_temp
        self.current_rh = 50.0
        self.current_step = 0
        self.history: List[Dict[str, Any]] = []
        self.last_idf_text = self.idf_manager.get_content() if self.idf_manager else ""

    def get_grid_carbon_intensity(self, hour: int) -> float:
        """Returns grid carbon intensity in gCO2/kWh based on hour of day."""
        h = hour % 24
        # Peaking between 17:00 and 21:00 (dirty evening grid)
        if 17 <= h <= 21:
            return 450.0 + 50.0 * math.sin(math.pi * (h - 17) / 4)
        elif 0 <= h <= 6:
            return 180.0 + 15.0 * random.uniform(-1.0, 1.0)
        else:
            return 280.0 + 30.0 * math.sin(math.pi * (h - 6) / 11)

    def get_electricity_rate(self, hour: int) -> float:
        """Returns electricity tariff rate in $/kWh."""
        h = hour % 24
        # On-peak pricing 14:00 - 20:00
        if 14 <= h <= 20:
            return 0.35  # Peak rate
        elif 8 <= h <= 14:
            return 0.22  # Mid-peak rate
        else:
            return 0.12  # Off-peak rate

    def get_occupancy_load(self, hour: int) -> Tuple[int, float]:
        """Returns (occupant_count, internal_gains_kw)."""
        h = hour % 24
        if 8 <= h <= 18:
            occupants = 10
            # 10 people * 100W + 1500W equipment/lights = 2.5 kW
            gains_kw = 2.5
        elif 7 <= h <= 19:
            occupants = 4
            gains_kw = 1.0
        else:
            occupants = 0
            gains_kw = 0.2  # Base standby electronics
        return occupants, gains_kw

    def get_solar_radiation(self, hour: int) -> float:
        """Solar heat gain entering windows (kW)."""
        h = hour % 24
        if 7 <= h <= 19:
            # Solar peak at 13:00
            solar = 1.8 * math.sin(math.pi * (h - 7) / 12)
            return max(0.0, solar)
        return 0.0

    def step(
        self,
        tout: float,
        cooling_setpoint: float = 22.0,
        heating_setpoint: float = 20.0,
        hvac_power_override_kw: float = None,
        dt_hours: float = 1.0
    ) -> Dict[str, Any]:
        """
        Advances building physics by one timestep.
        Supports setpoint control or direct HVAC override from LLM agent.
        """
        hour = self.current_step
        occupants, internal_gains_kw = self.get_occupancy_load(hour)
        solar_gains_kw = self.get_solar_radiation(hour)
        total_heat_gains_kw = internal_gains_kw + solar_gains_kw

        # Outside heat transfer to zone (kW)
        q_envelope_kw = (tout - self.current_tin) / self.R_envelope

        # Determine HVAC Cooling/Heating load required
        cop = max(1.5, self.cop_nominal - 0.04 * max(0.0, tout - 25.0))

        if hvac_power_override_kw is not None:
            # Agent directly controls HVAC cooling power (kW)
            hvac_cooling_kw = max(0.0, hvac_power_override_kw)
            q_hvac_cooling_thermal_kw = hvac_cooling_kw * cop
        else:
            # Thermostat setpoint closed-loop control logic
            if self.current_tin > cooling_setpoint:
                # Proportional thermal demand
                temp_diff = self.current_tin - cooling_setpoint
                thermal_req_kw = temp_diff * 4.0 + total_heat_gains_kw + max(0.0, q_envelope_kw)
                q_hvac_cooling_thermal_kw = min(12.0, max(0.0, thermal_req_kw))
                hvac_cooling_kw = q_hvac_cooling_thermal_kw / cop
            else:
                q_hvac_cooling_thermal_kw = 0.0
                hvac_cooling_kw = 0.0

        # Net thermal rate of change (°C / hour)
        q_net_kw = q_envelope_kw + total_heat_gains_kw - q_hvac_cooling_thermal_kw
        dT_dt = q_net_kw / self.C_zone
        self.current_tin += dT_dt * dt_hours

        # Calculate Fanger PMV & PPD
        clo = 0.5 if 5 <= (hour % 24) <= 20 else 0.7  # Summer clothing during day
        met = 1.2 if occupants > 0 else 0.9
        pmv, ppd, comfort_cat = calculate_pmv_ppd(
            ta=self.current_tin,
            tr=self.current_tin + 0.5 * (tout - self.current_tin) / self.R_envelope,
            vel=0.1,
            rh=self.current_rh,
            met=met,
            clo=clo
        )
        is_comfort_ok, penalty = evaluate_comfort_score(pmv)

        # Economic and Carbon intensity calculations
        carbon_g_per_kwh = self.get_grid_carbon_intensity(hour)
        elec_rate_usd = self.get_electricity_rate(hour)

        energy_kwh = hvac_cooling_kw * dt_hours
        cost_usd = energy_kwh * elec_rate_usd
        carbon_kg = (energy_kwh * carbon_g_per_kwh) / 1000.0

        # IDF Model modification (Forward Injection back to model)
        if self.idf_manager:
            updated_idf = self.idf_manager.update_dual_setpoints(heating_setpoint, cooling_setpoint)
            self.last_idf_text = updated_idf

        record = {
            "hour": hour,
            "Tout": round(tout, 2),
            "Tin": round(self.current_tin, 2),
            "Cooling_Setpoint": round(cooling_setpoint, 1),
            "Heating_Setpoint": round(heating_setpoint, 1),
            "HVAC_kW": round(hvac_cooling_kw, 2),
            "Energy_kWh": round(energy_kwh, 3),
            "Cost_USD": round(cost_usd, 3),
            "Carbon_kgCO2": round(carbon_kg, 3),
            "Carbon_Intensity_g_kWh": round(carbon_g_per_kwh, 1),
            "Electricity_Rate_USD_kWh": round(elec_rate_usd, 2),
            "PMV": pmv,
            "PPD": ppd,
            "Comfort_Category": comfort_cat,
            "Comfort_Compliant": is_comfort_ok,
            "Occupants": occupants,
            "COP": round(cop, 2)
        }

        self.history.append(record)
        self.current_step += 1
        return record

    def run_simulation(
        self,
        weather_data: Any,
        agent_controller=None,
        default_cooling_setpoint: float = 22.0
    ) -> Any:
        """Runs multi-step simulation over weather input (supports DataFrame or List[Dict])."""
        self.reset()
        
        # Convert weather_data to iterable list of dicts regardless of input type
        if pd is not None and isinstance(weather_data, pd.DataFrame):
            rows = [{"hour": row["hour"], "Tout": row["Tout"]} for _, row in weather_data.iterrows()]
        elif isinstance(weather_data, list):
            rows = weather_data
        else:
            rows = []

        for idx, row in enumerate(rows):
            tout = row['Tout']
            if agent_controller:
                obs = {
                    "Tin": self.current_tin,
                    "Tout": tout,
                    "hour": idx,
                    "rh": self.current_rh,
                    "grid_carbon_g_kwh": self.get_grid_carbon_intensity(idx),
                    "electricity_rate_usd": self.get_electricity_rate(idx),
                    "occupants": self.get_occupancy_load(idx)[0]
                }
                action = agent_controller.decide(obs)
                if isinstance(action, dict):
                    c_set = action.get("cooling_setpoint", default_cooling_setpoint)
                    h_override = action.get("hvac_kw", None)
                else:
                    c_set = default_cooling_setpoint
                    h_override = float(action)
                self.step(tout, cooling_setpoint=c_set, hvac_power_override_kw=h_override)
            else:
                self.step(tout, cooling_setpoint=default_cooling_setpoint)

        # Save optimized IDF artifact
        if self.idf_manager and self.last_idf_text:
            os.makedirs("data", exist_ok=True)
            IDFManager.save_idf(self.last_idf_text, "data/optimized_ecm.idf")

        if pd is not None:
            try:
                return pd.DataFrame(self.history)
            except Exception:
                return self.history
        return self.history

    def export_csv(self, filename: str):
        if not self.history:
            return
        keys = self.history[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.history)
