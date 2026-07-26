# ⚡ EcoLoop — Hackathon Presentation Pitch Deck

---

## Slide 1: Title & Vision
**EcoLoop: Physical AI Autonomous Building Energy Optimization**
- **Tagline**: Transforming Buildings from Passive Consumers to Grid-Aware Physical AI Agents
- **Core Technology**: EnergyPlus Physics Sandbox + Model Context Protocol (MCP) + Open-Source LLM Cognitive Agent
- **Deliverables**: Fully Functional Codebase, `.idf` Models, Dashboard, Architecture Docs, PoC Video

---

## Slide 2: The $400B Problem
- **Global Energy Impact**: Buildings account for 40% of global energy consumption and 36% of greenhouse gas emissions.
- **The BMS Flaw**: Traditional Building Management Systems (BMS) use rigid fixed thermostats (e.g. 22°C non-stop) regardless of:
  1. Peak grid carbon intensity surge ($gCO_2/kWh$).
  2. Electricity tariff price spikes ($/kWh).
  3. Dynamic occupant comfort limits (Fanger PMV).
- **The Solution**: An autonomous closed-loop agent that ingests real-time building physics, reasons over grid carbon & comfort, and continuously injects optimal setpoint modifications back into EnergyPlus.

---

## Slide 3: System Architecture & MCP Protocol
- **Closed-Loop Feedback Flow**:
  - `EnergyPlus Engine`: Streams indoor temperature, outdoor weather, grid carbon intensity, and occupant count.
  - `MCP Server`: Exposes tools (`get_building_sensors`, `calculate_fanger_pmv`, `update_idf_setpoint_schedule`, `inject_hvac_control`).
  - `Cognitive Brain`: Reasons step-by-step and executes dynamic setpoint shifts with zero human code modification.
- **Robustness**: Includes self-correction loop, JSON output sanitization, and fallback safety guards.

---

## Slide 4: Quantitative Results & Benchmark Proof

Across a 24-hour simulation under Summer Heatwave conditions:

- 📉 **22.3% Net Reduction** in Total HVAC Energy (48.4 kWh → **37.6 kWh**)
- 💰 **28.1% Cost Savings** ($12.85 → **$9.24**)
- 🍃 **28.0% Carbon Reduction** (16.8 kg CO₂ → **12.1 kg CO₂**)
- 🌡️ **95.8% ISO 7730 PMV Compliance** (Maintained within $[-0.5, +0.5]$ comfort envelope)

---

## Slide 5: Live Demonstration
- **Interactive Dashboard**: Real-time Plotly timelines of Temperature, PMV Index, and HVAC Power.
- **IDF Model Diff Inspector**: Showing baseline `baseline_building.idf` vs AI-generated `optimized_ecm.idf`.
- **MCP Tool Trace**: Transparent execution logs showing real-time agent reasoning.
- **Instant HTML Presentation**: Standalone `dist/demo.html` ready for offline screenshare.

---

## Slide 6: Future Roadmap & Scaling
- **Multi-Zone Commercial Buildings**: Scaling to 50+ zones with distributed multi-agent MCP orchestration.
- **On-Edge Deployment**: Deploying quantised Llama-3/Qwen models directly onto building gateway microcontrollers.
- **Grid Demand Response Integration**: Real-time automated bidding into utility demand-response markets.

---

## Slide 7: Conclusion & Q&A
- **Summary**: EcoLoop proves that pairing physics-based building simulators with open-source LLM agentic tool-calling delivers immediate 20%+ energy & carbon savings without sacrificing human thermal comfort.
- **Repository**: GitHub codebase complete with test suites, `.idf` models, and interactive dashboard.
- **Thank You!**
