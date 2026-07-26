import os
import json
from app.energyplus_engine import EnergyPlusSimulationEngine
from app.mcp_server import EcoLoopMCPServer
from app.agent_mcp import EcoLoopAgent
from app.fanger_pmv import calculate_pmv_ppd
from app.idf_tools import IDFManager

def test_full_pipeline():
    print("=== Testing EcoLoop Closed-Loop Pipeline ===")
    
    # 1. Test Fanger PMV Calculation
    pmv, ppd, cat = calculate_pmv_ppd(ta=23.5, rh=50.0, clo=0.5, met=1.2)
    print(f"Fanger PMV: {pmv}, PPD: {ppd}%, Sensation: {cat}")
    assert -3.0 <= pmv <= 3.0, "PMV calculation out of range"
    
    # 2. Test IDF Parser & Modifier
    idf_path = "data/baseline_building.idf"
    assert os.path.exists(idf_path), "Baseline IDF file missing"
    idf_mgr = IDFManager(idf_path)
    modified_text = idf_mgr.update_dual_setpoints(heating_c=20.0, cooling_c=24.5)
    IDFManager.save_idf(modified_text, "data/optimized_ecm.idf")
    assert os.path.exists("data/optimized_ecm.idf"), "Failed to generate optimized IDF"
    
    diff = IDFManager.generate_diff(idf_mgr.get_content(), modified_text)
    print("IDF Diff preview:")
    print(diff[:250] if diff else "No diff")
    
    # 3. Test MCP Server & Tool Calling
    mcp_server = EcoLoopMCPServer(idf_filepath=idf_path)
    tools = mcp_server.list_tools()
    print(f"Registered MCP Tools: {[t['name'] for t in tools]}")
    assert len(tools) >= 3, "MCP tools missing"
    
    # 4. Test Autonomous Agent & Closed-Loop Simulation
    agent = EcoLoopAgent(mcp_server=mcp_server, mode="MCP_AI_Agent")
    engine = EnergyPlusSimulationEngine(idf_path=idf_path)
    
    # Run 24h simulation
    hours = 24
    t_out = [20, 19, 18, 18, 19, 21, 24, 27, 29, 31, 33, 35, 36, 35, 34, 32, 30, 28, 26, 24, 23, 22, 21, 20]
    weather_data = [{'hour': h, 'Tout': tout} for h, tout in enumerate(t_out)]
    
    history_records = engine.run_simulation(weather_data, agent_controller=agent)
    print(f"Simulation completed! Total steps: {len(history_records)}")
    
    total_kwh = sum(r['Energy_kWh'] for r in history_records)
    total_cost = sum(r['Cost_USD'] for r in history_records)
    total_carbon = sum(r['Carbon_kgCO2'] for r in history_records)
    print(f"Total kWh: {total_kwh:.2f}, Cost: ${total_cost:.2f}, Carbon: {total_carbon:.2f} kg CO2")
    
    # Export telemetry CSV using standard library
    engine.export_csv("data/runtime_telemetry.csv")
    assert os.path.exists("data/runtime_telemetry.csv"), "CSV export failed"
    print("Exported telemetry CSV to data/runtime_telemetry.csv")
    
    assert len(history_records) == 24, "Incorrect simulation step count"
    print("\n[SUCCESS] ALL CLOSED-LOOP PIPELINE TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_full_pipeline()
