import re
import difflib
from typing import Dict, Any, Tuple

class IDFManager:
    """Utility class for reading, updating, serializing, and diffing EnergyPlus IDF files."""

    def __init__(self, idf_filepath: str):
        self.filepath = idf_filepath
        with open(idf_filepath, 'r', encoding='utf-8') as f:
            self.content = f.read()

    def get_content(self) -> str:
        return self.content

    def update_cooling_setpoint(self, setpoint_c: float) -> str:
        """Dynamically update Cooling_Setpoint_Sched inside Schedule:Compact."""
        # Find Cooling_Setpoint_Sched block in IDF text
        pattern = r"(Schedule:Compact,\s*Cooling_Setpoint_Sched,[\s\S]*?Until:\s*18:00,\s*)([0-9.]+)(,[\s\S]*?;\s*)"
        new_content = re.sub(pattern, r"\g<1>" + f"{setpoint_c:.1f}" + r"\g<3>", self.content)
        return new_content

    def update_dual_setpoints(self, heating_c: float, cooling_c: float) -> str:
        """Update both heating and cooling occupied setpoints."""
        content = self.content
        # Update cooling
        pattern_cool = r"(Schedule:Compact,\s*Cooling_Setpoint_Sched,[\s\S]*?Until:\s*18:00,\s*)([0-9.]+)(,[\s\S]*?;\s*)"
        content = re.sub(pattern_cool, r"\g<1>" + f"{cooling_c:.1f}" + r"\g<3>", content)

        # Update heating
        pattern_heat = r"(Schedule:Compact,\s*Heating_Setpoint_Sched,[\s\S]*?Until:\s*18:00,\s*)([0-9.]+)(,[\s\S]*?;\s*)"
        content = re.sub(pattern_heat, r"\g<1>" + f"{heating_c:.1f}" + r"\g<3>", content)
        return content

    @staticmethod
    def generate_diff(original_idf: str, modified_idf: str) -> str:
        """Generate human-readable diff string comparing original and modified IDF files."""
        orig_lines = original_idf.splitlines(keepends=True)
        mod_lines = modified_idf.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig_lines, mod_lines,
            fromfile='baseline_building.idf',
            tofile='optimized_ecm.idf',
            n=2
        )
        return ''.join(diff)

    @staticmethod
    def save_idf(idf_content: str, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(idf_content)
