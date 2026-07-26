import os
import time
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as bg_plotly
import streamlit as st

# Custom modules
from app.ui_theme import apply_custom_theme
from app.energyplus_engine import EnergyPlusSimulationEngine
from app.mcp_server import EcoLoopMCPServer
from app.agent_mcp import EcoLoopAgent
from app.idf_tools import IDFManager

st.set_page_config(
    page_title="EcoLoop — Autonomous Physical AI Building Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply glassmorphic CSS styling
apply_custom_theme()

# Header Card
st.markdown("""
<div class="header-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 class="header-title">EcoLoop — Physical AI Building Agent</h1>
            <p class="header-subtitle">Autonomous Closed-Loop Energy Optimization via EnergyPlus Sandbox & Model Context Protocol (MCP)</p>
        </div>
        <div class="status-badge-active">
            <span class="pulse-dot"></span> Closed-Loop Protocol: ACTIVE
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/leaf.png", width=60)
    st.header("⚡ Simulation Controls")
    
    sim_hours = st.slider("Simulation Horizon (Hours)", min_value=12, max_value=72, value=24, step=6)
    weather_scenario = st.selectbox(
        "Outdoor Weather Scenario",
        ["Summer Heatwave (18°C - 36°C)", "Mild Spring (14°C - 26°C)", "Extreme Peak Load (22°C - 38°C)"]
    )
    
    agent_strategy = st.radio(
        "Agent Control Strategy",
        ["EcoLoop MCP AI Agent (Autonomous)", "Fixed Baseline Schedule (Rigid 22°C)", "Rule-Based Proportional"]
    )
    
    st.divider()
    st.subheader("🎯 Comfort Targets")
    pmv_target_min, pmv_target_max = st.slider("ISO 7730 PMV Comfort Bounds", -1.0, 1.0, (-0.5, 0.5), step=0.1)
    
    st.divider()
    run_button = st.button("🚀 Run Closed-Loop Simulation", type="primary", use_container_width=True)

# Generate Synthetic Weather Dataset
def get_weather_data(hours: int, scenario: str) -> pd.DataFrame:
    t = np.arange(hours)
    if "Summer Heatwave" in scenario:
        base_temp = 26.0
        amp = 9.0
    elif "Mild Spring" in scenario:
        base_temp = 20.0
        amp = 6.0
    else:  # Extreme Peak Load
        base_temp = 28.0
        amp = 10.0
    
    # Sinusoidal diurnal temperature profile with peak around hour 15
    tout = base_temp + amp * np.sin(2 * np.pi * (t - 8) / 24)
    return pd.DataFrame({'hour': t, 'Tout': tout})

weather_df = get_weather_data(sim_hours, weather_scenario)

# Initialize EnergyPlus Sandbox Engine & MCP Agent
ep_engine_ai = EnergyPlusSimulationEngine(idf_path="data/baseline_building.idf")
ep_engine_base = EnergyPlusSimulationEngine(idf_path="data/baseline_building.idf")

mcp_server = EcoLoopMCPServer(idf_filepath="data/baseline_building.idf")
ai_agent = EcoLoopAgent(mcp_server=mcp_server, mode="MCP_AI_Agent")

# Always run simulation on initial load or button press
if run_button or 'sim_run' not in st.session_state:
    st.session_state['sim_run'] = True
    
    # 1. Run AI Agent Simulation
    df_ai = ep_engine_ai.run_simulation(weather_df, agent_controller=ai_agent)
    
    # 2. Run Baseline Simulation (Fixed rigid 22.0°C cooling setpoint)
    df_base = ep_engine_base.run_simulation(weather_df, agent_controller=None, default_cooling_setpoint=22.0)
    
    st.session_state['df_ai'] = df_ai
    st.session_state['df_base'] = df_base
    st.session_state['mcp_logs'] = mcp_server.call_log

df_ai = st.session_state['df_ai']
df_base = st.session_state['df_base']
mcp_logs = st.session_state.get('mcp_logs', [])

# Calculate Key Performance Indicators (KPIs)
ai_kwh = df_ai['Energy_kWh'].sum()
base_kwh = df_base['Energy_kWh'].sum()
energy_savings_pct = ((base_kwh - ai_kwh) / base_kwh * 100.0) if base_kwh > 0 else 0.0

ai_cost = df_ai['Cost_USD'].sum()
base_cost = df_base['Cost_USD'].sum()
cost_savings_pct = ((base_cost - ai_cost) / base_cost * 100.0) if base_cost > 0 else 0.0

ai_carbon = df_ai['Carbon_kgCO2'].sum()
base_carbon = df_base['Carbon_kgCO2'].sum()
carbon_savings_pct = ((base_carbon - ai_carbon) / base_carbon * 100.0) if base_carbon > 0 else 0.0

ai_comfort_pct = (df_ai['Comfort_Compliant'].sum() / len(df_ai)) * 100.0

# Render Key Metrics Cards
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{ai_kwh:.1f} kWh</div>
        <div class="metric-label">Total Energy (kWh)</div>
        <div class="metric-badge-green">↓ {energy_savings_pct:.1f}% Energy Saved</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">${ai_cost:.2f}</div>
        <div class="metric-label">Electricity Cost</div>
        <div class="metric-badge-green">↓ ${base_cost - ai_cost:.2f} ({cost_savings_pct:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{ai_carbon:.1f} kg</div>
        <div class="metric-label">Carbon Footprint</div>
        <div class="metric-badge-green">↓ {carbon_savings_pct:.1f}% CO₂ Shaved</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{ai_comfort_pct:.1f}%</div>
        <div class="metric-label">PMV Comfort Score</div>
        <div class="metric-badge-blue">ISO 7730 Compliant</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Closed-Loop Telemetry",
    "📄 IDF Model & MCP Logs",
    "📊 Quantitative Savings",
    "📚 Architecture Document"
])

with tab1:
    st.subheader("Real-Time Closed-Loop Simulation Telemetry")
    
    # 1. Temperature Timeline Graph
    fig_temp = bg_plotly.Figure()
    
    # Comfort band shading (20 to 24 C)
    fig_temp.add_hrect(y0=20.0, y1=24.5, fillcolor="rgba(34, 197, 94, 0.1)", line_width=0, annotation_text="ASHRAE 55 Comfort Zone")
    
    fig_temp.add_trace(bg_plotly.Scatter(
        x=df_ai['hour'], y=df_ai['Tout'],
        name="Outdoor Temp (°C)", line=dict(color="#f43f5e", width=2, dash="dash")
    ))
    fig_temp.add_trace(bg_plotly.Scatter(
        x=df_ai['hour'], y=df_ai['Tin'],
        name="EcoLoop AI Indoor Temp (°C)", line=dict(color="#38bdf8", width=3)
    ))
    fig_temp.add_trace(bg_plotly.Scatter(
        x=df_base['hour'], y=df_base['Tin'],
        name="Baseline Fixed Temp (°C)", line=dict(color="#94a3b8", width=2, dash="dot")
    ))
    fig_temp.add_trace(bg_plotly.Scatter(
        x=df_ai['hour'], y=df_ai['Cooling_Setpoint'],
        name="AI Cooling Setpoint (°C)", line=dict(color="#a855f7", width=2)
    ))
    
    fig_temp.update_layout(
        template="plotly_dark",
        title="Indoor & Outdoor Temperature Dynamics vs AI Dynamic Setpoints",
        xaxis_title="Simulation Hour",
        yaxis_title="Temperature (°C)",
        height=380,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_temp, use_container_width=True)

    col_left, col_right = st.columns(2)
    
    with col_left:
        # 2. Fanger PMV Comfort Index Graph
        fig_pmv = bg_plotly.Figure()
        fig_pmv.add_hrect(y0=-0.5, y1=0.5, fillcolor="rgba(34, 197, 94, 0.15)", line_width=0, annotation_text="Compliant Zone [-0.5, +0.5]")
        fig_pmv.add_trace(bg_plotly.Scatter(
            x=df_ai['hour'], y=df_ai['PMV'],
            name="EcoLoop AI PMV", line=dict(color="#4ade80", width=2.5)
        ))
        fig_pmv.add_trace(bg_plotly.Scatter(
            x=df_base['hour'], y=df_base['PMV'],
            name="Baseline PMV", line=dict(color="#f43f5e", width=1.5, dash="dot")
        ))
        fig_pmv.update_layout(
            template="plotly_dark",
            title="Fanger PMV Thermal Comfort Index (ISO 7730)",
            xaxis_title="Simulation Hour",
            yaxis_title="PMV Index (-3 to +3)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_pmv, use_container_width=True)

    with col_right:
        # 3. HVAC Power & Carbon Grid Intensity
        fig_power = bg_plotly.Figure()
        fig_power.add_trace(bg_plotly.Bar(
            x=df_ai['hour'], y=df_ai['HVAC_kW'],
            name="EcoLoop HVAC (kW)", marker_color="#38bdf8", opacity=0.85
        ))
        fig_power.add_trace(bg_plotly.Scatter(
            x=df_ai['hour'], y=df_ai['Carbon_Intensity_g_kWh'],
            name="Grid Carbon Intensity (gCO2/kWh)", yaxis="y2", line=dict(color="#fbbf24", width=2)
        ))
        fig_power.update_layout(
            template="plotly_dark",
            title="HVAC Electric Demand (kW) vs Grid Carbon Intensity",
            xaxis_title="Simulation Hour",
            yaxis=dict(title="HVAC Power (kW)"),
            yaxis2=dict(title="Carbon Intensity (gCO2/kWh)", overlaying="y", side="right"),
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_power, use_container_width=True)

with tab2:
    st.subheader("EnergyPlus IDF Model & MCP Tool Execution Logs")
    
    col_idf, col_mcp = st.columns(2)
    
    with col_idf:
        st.markdown("### 🏢 EnergyPlus Building Model (.idf)")
        if os.path.exists("data/baseline_building.idf") and os.path.exists("data/optimized_ecm.idf"):
            with open("data/baseline_building.idf") as f:
                base_idf = f.read()
            with open("data/optimized_ecm.idf") as f:
                opt_idf = f.read()
            diff_text = IDFManager.generate_diff(base_idf, opt_idf)
            
            st.caption("Visual Unified Diff: Baseline IDF vs AI Generated ECM IDF")
            st.code(diff_text if diff_text else "No setpoint changes detected.", language="diff")
        else:
            st.info("Run simulation to generate runtime IDF file comparison.")
            
    with col_mcp:
        st.markdown("### 🛠️ Model Context Protocol (MCP) Tool Execution Trace")
        st.caption("Live trace log of agent JSON-RPC tool calls and closed-loop actions")
        if mcp_logs:
            st.dataframe(pd.DataFrame(mcp_logs), use_container_width=True, height=400)
        else:
            st.info("No tool calls recorded yet.")

with tab3:
    st.subheader("Quantitative Energy & Cost Savings Breakdown")
    
    # Cumulative Energy Comparison Chart
    df_ai['Cumulative_AI_kWh'] = df_ai['Energy_kWh'].cumsum()
    df_base['Cumulative_Base_kWh'] = df_base['Energy_kWh'].cumsum()
    
    fig_cum = bg_plotly.Figure()
    fig_cum.add_trace(bg_plotly.Scatter(
        x=df_ai['hour'], y=df_base['Cumulative_Base_kWh'],
        name="Baseline Cumulative kWh", line=dict(color="#f43f5e", width=2, dash="dash")
    ))
    fig_cum.add_trace(bg_plotly.Scatter(
        x=df_ai['hour'], y=df_ai['Cumulative_AI_kWh'],
        name="EcoLoop AI Cumulative kWh", line=dict(color="#10b981", width=3), fill='tonexty'
    ))
    fig_cum.update_layout(
        template="plotly_dark",
        title="Cumulative Energy Consumption (kWh) Over Time",
        xaxis_title="Simulation Hour",
        yaxis_title="Cumulative kWh",
        height=350
    )
    st.plotly_chart(fig_cum, use_container_width=True)
    
    # Export telemetry CSV button
    csv_data = df_ai.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Telemetry Report (CSV)",
        data=csv_data,
        file_name="ecoloop_telemetry_results.csv",
        mime="text/csv",
        type="primary"
    )
    
    st.markdown("#### Simulation Data Table")
    st.dataframe(df_ai, use_container_width=True)

with tab4:
    st.subheader("System Architecture & Technical Approach")
    if os.path.exists("docs/system_architecture.md"):
        with open("docs/system_architecture.md", encoding="utf-8") as f:
            arch_md = f.read()
        st.markdown(arch_md)
    else:
        st.write("System architecture document loading...")
