# EcoLoop — System Architecture Document

## 1. Overview & Architecture Philosophy

EcoLoop is an autonomous **Physical AI Proof-of-Concept (PoC)** that transforms buildings from passive energy consumers into self-correcting, grid-aware smart assets. It bridges physics-based building thermodynamics (EnergyPlus) with an open-source cognitive agent framework using the **Model Context Protocol (MCP)**.

```
┌────────────────────────────────┐         ┌────────────────────────────────┐
│   EnergyPlus Sandbox / Engine  │         │   Model Context Protocol (MCP) │
│                                │         │             Server             │
│  - IDF Building Model Parser   │ ──────> │                                │
│  - Fanger PMV Comfort Engine   │ Sensor  │  - get_building_sensors       │
│  - Dynamic Grid Carbon Telemetry│ Data   │  - calculate_fanger_pmv        │
└────────────────────────────────┘         │  - update_idf_setpoint_schedule│
                 ▲                         │  - inject_hvac_control         │
                 │                         └────────────────────────────────┘
                 │ Forward                                 │
                 │ Control                                 │ Tool Calls &
                 │ Injection                               ▼ Reasoning
                 └───────────────────────── ┌────────────────────────────────┐
                                            │      Autonomous LLM Agent      │
                                            │   (Self-Correction & Peak-Shaving)
                                            └────────────────────────────────┘
```

---

## 2. Tool-Calling & Protocol Architecture (MCP)

EcoLoop implements a standardized **Model Context Protocol (MCP)** server (`app/mcp_server.py`) exposing granular tool schemas to the cognitive brain:

1. `get_building_sensors(hour)`: Fetches real-time zone air temperature ($T_{in}$), outdoor dry-bulb temperature ($T_{out}$), occupancy count, dynamic carbon grid intensity ($gCO_2/kWh$), and electricity tariff ($/kWh).
2. `calculate_fanger_pmv(ta, rh, clo, met)`: Calculates ISO 7730 Fanger Predicted Mean Vote (PMV) and Predicted Percentage Dissatisfied (PPD) thermal sensation metrics.
3. `update_idf_setpoint_schedule(cooling_setpoint, heating_setpoint)`: Modifies the underlying EnergyPlus `.idf` file setpoint objects (`Schedule:Compact`, `ThermostatSetpoint:DualSetpoint`) and generates the updated `data/optimized_ecm.idf` file.
4. `inject_hvac_control(cooling_setpoint, reasoning)`: Applies closed-loop forward control actions back into the active building instance.

---

## 3. Prompt Engineering & Prompt Latency Management

### Prompt Engineering Strategy
- **Strict JSON Schema Enforcement**: Prompts mandate deterministic JSON formatting with explicit key/value schemas.
- **Zero-Shot Tool Selection**: System instructions detail tool definitions and parameters, enabling direct tool invocation without ambiguous conversational filler.
- **Explicit Step-by-Step Reasoning**: The agent outputs a `reasoning` trace string explaining why setpoints are shifted (e.g. pre-cooling vs peak carbon shaving).

### Latency Management & Handling Lengthy Simulation Logs
For extended 72-hour or 7-day simulation runs, raw simulation log files (e.g. EnergyPlus `.eso` or `.csv` files) can reach megabytes. EcoLoop solves prompt latency and token window saturation through three strategies:

1. **State-Vector Summarization**: Rather than feeding raw log files to the LLM, the telemetry engine compresses past steps into a rolling window state vector:
   - Rolling mean temperature & variance
   - Peak energy window metrics
   - Instantaneous PMV index
2. **Deterministic Pre-Filtering**: Fast mathematical tools (e.g. Fanger PMV calculation) run as local native functions within the MCP tool server rather than asking the LLM to compute complex floating-point thermodynamic equations.
3. **Canceled Polling & Event-Driven Triggers**: LLM decision cycles trigger only during setpoint transition thresholds or environmental shifts, eliminating wasteful polling.

---

## 4. Self-Correction & Robustness Loops

To ensure 100% uptime during extended simulation time horizons (Evaluation Criterion: System Integration 30%), EcoLoop incorporates a multi-tier self-correction mechanism:

1. **JSON Extraction Guard**: If an open-source LLM outputs markdown backticks, conversational preamble, or malformed JSON, the agent's regex parser extracts the first valid `{ ... }` block.
2. **Physical Boundary Validation**: Generated setpoints are sanitized through hard safety guards ($20.0^\circ\text{C} \le T_{cooling} \le 26.5^\circ\text{C}$).
3. **Fallback Graceful Recovery**: If an external LLM endpoint times out or fails after retries, the MCP controller defaults to the peak-shaving policy while preserving continuous simulation state.

---

## 5. Physical Building Model & EnergyPlus Integration

- **Baseline Model**: `data/baseline_building.idf` (Small Office Zone with ideal loads system, occupancy schedules, internal equipment loads).
- **Forward Control Injection**: On every optimization cycle, thermostat setpoint schedules are injected directly into the EnergyPlus model, generating `data/optimized_ecm.idf`.
- **Fanger PMV Model**: Computes human sensation scores from indoor air temp, mean radiant temp, relative humidity (50%), metabolic rate ($1.2\text{ met}$), and clothing insulation ($0.5-0.7\text{ clo}$). ISO 7730 compliance is strictly enforced between $[-0.5, +0.5]$.
