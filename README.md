# ⚡ EcoLoop — Physical AI Autonomous Building Agent

> Autonomous Closed-Loop Smart Building Energy Optimization using EnergyPlus Digital Sandbox, Model Context Protocol (MCP), and Open-Source Cognitive LLM Agents.

---

## 📸 Dashboard & UI Preview

### 1. Quantitative Energy & Comfort Dashboard
![EcoLoop Dashboard Overview](docs/dashboard_overview.png)

### 2. ISO 7730 Fanger PMV Comfort Index & Power Demand
![Fanger PMV & HVAC Power Charts](docs/pmv_power_charts.png)

### 3. Model Context Protocol (MCP) Forward Injection IDF Diff
![MCP Forward Injection IDF Diff](docs/mcp_idf_diff.png)

---

## 💡 System Overview

Buildings account for ~40% of global electricity consumption. Traditional Building Management Systems (BMS) rely on rigid, fixed schedules (e.g., maintaining 22°C continuously) that fail to adapt to dynamic grid carbon intensity spikes ($gCO_2/kWh$), variable electricity tariffs ($/kWh), and occupant thermal comfort boundaries.

**EcoLoop** provides an autonomous **closed-loop feedback pipeline**:

1. **Feedback Loop (EnergyPlus → AI)**: Real-time sensor streaming of zone temperatures, outdoor weather, occupancy, electricity tariffs, and ISO 7730 Fanger Predicted Mean Vote (PMV) comfort indices.
2. **Cognitive Reasoning (LLM + MCP)**: Evaluates thermal comfort against dynamic grid carbon intensity and peak electricity prices.
3. **Forward Injection (AI → EnergyPlus)**: Dynamically updates EnergyPlus Input Data File (`.idf`) setpoint schedules (`ThermostatSetpoint:DualSetpoint`).

---

## 🏗 System Architecture

```
 ┌────────────────────────────────┐            ┌────────────────────────────────┐
 │  EnergyPlus Sandbox Engine     │            │ Model Context Protocol (MCP)   │
 │                                │ ─Sensors─> │            Server              │
 │  - Baseline IDF Building       │ Telemetry  │  - get_building_sensors       │
 │  - ISO 7730 Fanger PMV Engine  │            │  - calculate_fanger_pmv        │
 │  - Grid Carbon Streamer        │            │  - update_idf_setpoint_schedule│
 └────────────────────────────────┘            │  - inject_hvac_control         │
                ▲                              └────────────────────────────────┘
                │ Forward Injection                             │ Tool Calls &
                │ Setpoint Modification                         ▼ Step Reasoning
                └────────────────────────────── ┌────────────────────────────────┐
                                                │   Autonomous Open-Source LLM   │
                                                │   (Self-Correction & Shaving) │
                                                └────────────────────────────────┘
```

### Protocol Tools
- `get_building_sensors`: Reads real-time environmental telemetry.
- `calculate_fanger_pmv`: Solves ISO 7730 Fanger PMV thermal comfort equations.
- `update_idf_setpoint_schedule`: Modifies thermostat setpoint schedules in EnergyPlus `.idf` files and saves `data/optimized_ecm.idf`.
- `inject_hvac_control`: Applies setpoint and cooling overrides back into the active building model.

---

## 📦 Project Deliverables

| # | Deliverable | Repository File Path | Description |
| :-: | :--- | :--- | :--- |
| **1** | **Source Code** | [`app/`](file:///c:/Users/tyagi/Desktop/EcoLoop/app/) | Python codebase for EnergyPlus engine, MCP server, and LLM agent |
| **2** | **Building Models (.idf)** | [`data/baseline_building.idf`](file:///c:/Users/tyagi/Desktop/EcoLoop/data/baseline_building.idf)<br>[`data/optimized_ecm.idf`](file:///c:/Users/tyagi/Desktop/EcoLoop/data/optimized_ecm.idf) | Baseline Small Office IDF and AI-generated runtime ECM model |
| **3** | **Quantitative Dashboard** | [`app/main.py`](file:///c:/Users/tyagi/Desktop/EcoLoop/app/main.py)<br>[`dist/demo.html`](file:///c:/Users/tyagi/Desktop/EcoLoop/dist/demo.html) | Interactive Streamlit Plotly dashboard and standalone HTML app |
| **4** | **System Architecture** | [`SYSTEM_ARCHITECTURE.md`](file:///c:/Users/tyagi/Desktop/EcoLoop/SYSTEM_ARCHITECTURE.md) | Technical report on tool-calling, prompt engineering, and latency management |

---

## ⚡ Quickstart Guide

### Option A: Automated Pipeline Test
```bash
python test_pipeline.py
```

### Option B: Interactive Dashboard (Streamlit)
```bash
pip install -r requirements.txt
streamlit run app/main.py
```

### Option C: Standalone Web Demo
Open [`dist/demo.html`](file:///c:/Users/tyagi/Desktop/EcoLoop/dist/demo.html) in any browser.

---

### 👨‍💻 Author
**Made with ❤️ by Sujal Tyagi**
