# Feature: Fluvius Energy Metering

## Overview

Integrate Fluvius digital meters (electricity, gas, water) into Home Assistant to track consumption, injection (solar), and calculate costs with Total Energies dynamic pricing.

## Problem Statement

With Fluvius digital meters installed in Belgium, detailed consumption data is available but not easily accessible in real-time. Integrating this data into Home Assistant enables:

1. Real-time monitoring of energy usage
2. Cost calculation with actual spot prices
3. Comparison of consumption vs. injection (if solar installed)
4. Historical analysis and trend identification

## User Stories

1. **As a user**, I want to see my real-time electricity consumption and injection on my Home Assistant dashboard so I understand my energy flow.

2. **As a user**, I want to track my monthly electricity, gas, and water costs calculated with actual Total Energies rates so I can budget accurately.

3. **As a user**, I want to see historical energy data in graphs so I can identify usage patterns and optimize consumption.

4. **As a user**, I want to compare my actual cost (spot price) vs. what I would pay with a fixed contract so I can validate my contract choice.

5. **As a user**, I want alerts when my consumption is unusually high so I can identify issues early.

## Data Sources

### Fluvius Digital Meter

Belgian digital meters (smart meters) support two integration methods:

| Method | Description | Real-time | Setup Complexity |
|--------|-------------|-----------|------------------|
| **P1 Port** | Physical connection to meter's P1 port | Yes (1-10 sec) | Medium - requires hardware |
| **Fluvius API** | Cloud API via Mijn Fluvius | No (15 min delay) | Low - software only |

### P1 Port Hardware

The P1 port is a serial interface on the digital meter. To use it:

1. **P1 Cable/Dongle**: USB or WiFi-enabled P1 reader
   - Examples: SlimmeLezer+, HomeWizard P1, Fluvius P1 cable
2. **Connection**: Plugs into meter's P1 port (RJ12 connector)
3. **Data**: DSMR (Dutch Smart Meter Requirements) protocol telegrams

### Fluvius API

Available via "Mijn Fluvius" portal:
- Requires Fluvius account linked to your meter
- Data delayed by ~15 minutes
- Historical data available
- HACS integration exists

## Technical Implementation

### Option A: P1 Port Integration (Recommended)

#### Hardware Setup

**Recommended Device**: HomeWizard P1 Meter or SlimmeLezer+

```yaml
# configuration.yaml
# HomeWizard P1 integration (auto-discovered if on same network)
# Or manually configure if needed
```

**Entities created automatically**:
- `sensor.p1_electricity_consumption` (current W)
- `sensor.p1_electricity_production` (current W - if solar)
- `sensor.p1_total_consumption_kwh` (cumulative)
- `sensor.p1_total_production_kwh` (cumulative)
- `sensor.p1_gas_consumption` (m)

#### SlimmeLezer+ Setup (if using)

```yaml
# ESPHome configuration for SlimmeLezer+
# Configured via ESPHome add-on, not main configuration.yaml
```

### Option B: Fluvius API Integration

```yaml
# configuration.yaml (via HACS integration)
# Install "Fluvius" integration from HACS
# Configure via UI with Mijn Fluvius credentials
```

### Energy Dashboard Configuration

Home Assistant's built-in Energy Dashboard:

```yaml
# Energy dashboard configuration is done via UI
# Settings > Dashboards > Energy

# Required sensor mappings:
# - Grid consumption: sensor.p1_total_consumption_kwh
# - Return to grid: sensor.p1_total_production_kwh
# - Gas consumption: sensor.p1_gas_consumption
```

### Cost Calculation with Spot Prices

Combine with Belgian Electricity Prices feature for real-time cost:

```yaml
# sensors.yaml
template:
  - sensor:
      - name: "Electricity Cost Current Hour"
        unit_of_measurement: "EUR"
        state: >
          {% set kwh = states('sensor.p1_electricity_consumption_hourly') | float(0) %}
          {% set price = states('sensor.electricity_total_cost') | float(0) %}
          {{ (kwh * price) | round(4) }}
        icon: mdi:currency-eur

      - name: "Electricity Cost Today"
        unit_of_measurement: "EUR"
        state: >
          {{ states('sensor.energy_cost_today') | float(0) | round(2) }}
        icon: mdi:currency-eur

      - name: "Electricity Cost This Month"
        unit_of_measurement: "EUR"
        state: >
          {{ states('sensor.energy_cost_monthly') | float(0) | round(2) }}
        icon: mdi:currency-eur

      # Compare spot vs fixed contract
      - name: "Fixed Contract Equivalent Cost"
        unit_of_measurement: "EUR"
        state: >
          {% set kwh = states('sensor.p1_total_consumption_kwh') | float(0) %}
          {% set fixed_rate = 0.30 %}  {# Typical fixed rate EUR/kWh #}
          {{ (kwh * fixed_rate) | round(2) }}
        icon: mdi:compare

      - name: "Spot Price Savings"
        unit_of_measurement: "EUR"
        state: >
          {% set fixed = states('sensor.fixed_contract_equivalent_cost') | float(0) %}
          {% set actual = states('sensor.electricity_cost_this_month') | float(0) %}
          {{ (fixed - actual) | round(2) }}
        icon: mdi:piggy-bank
```

### Gas Cost Calculation

```yaml
# sensors.yaml
template:
  - sensor:
      - name: "Gas Cost This Month"
        unit_of_measurement: "EUR"
        state: >
          {% set m3 = states('sensor.gas_consumption_monthly') | float(0) %}
          {% set price_per_m3 = 1.50 %}  {# Update with actual rate #}
          {{ (m3 * price_per_m3) | round(2) }}
        icon: mdi:gas-burner

      - name: "Gas Cost Today"
        unit_of_measurement: "EUR"
        state: >
          {% set m3 = states('sensor.gas_consumption_daily') | float(0) %}
          {% set price_per_m3 = 1.50 %}
          {{ (m3 * price_per_m3) | round(2) }}
```

### Water Cost Calculation

```yaml
# sensors.yaml
# Note: Water data typically not available via P1 port
# May require separate water meter integration

template:
  - sensor:
      - name: "Water Cost This Month"
        unit_of_measurement: "EUR"
        state: >
          {% set m3 = states('sensor.water_consumption_monthly') | float(0) %}
          {% set price_per_m3 = 4.50 %}  {# Update with actual rate #}
          {{ (m3 * price_per_m3) | round(2) }}
        icon: mdi:water
```

### Utility Meter for Daily/Monthly Tracking

```yaml
# configuration.yaml
utility_meter:
  electricity_daily:
    source: sensor.p1_total_consumption_kwh
    cycle: daily

  electricity_monthly:
    source: sensor.p1_total_consumption_kwh
    cycle: monthly

  gas_daily:
    source: sensor.p1_gas_consumption
    cycle: daily

  gas_monthly:
    source: sensor.p1_gas_consumption
    cycle: monthly
```

### High Consumption Alert

```yaml
# automations.yaml
automation:
  - alias: "High Electricity Consumption Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.p1_electricity_consumption
        above: 5000  # Watts
        for:
          minutes: 30
    action:
      - service: notify.mobile_app
        data:
          title: "High Power Usage"
          message: "Consuming {{ states('sensor.p1_electricity_consumption') }}W for 30+ minutes"
```

### Dashboard Cards

```yaml
# ui-lovelace.yaml
type: vertical-stack
title: Energy
cards:
  # Current Power Flow
  - type: custom:power-flow-card
    entities:
      grid: sensor.p1_electricity_consumption
      solar: sensor.p1_electricity_production
      home: sensor.home_consumption

  # Today's Stats
  - type: statistics-graph
    title: Electricity Today
    entities:
      - sensor.electricity_daily
    stat_types:
      - sum
    period:
      calendar:
        period: day

  # Cost Overview
  - type: entities
    title: Energy Costs
    entities:
      - entity: sensor.electricity_cost_today
        name: Electricity Today
      - entity: sensor.electricity_cost_this_month
        name: Electricity This Month
      - entity: sensor.gas_cost_this_month
        name: Gas This Month
      - entity: sensor.spot_price_savings
        name: Spot Price Savings

  # Monthly Comparison
  - type: custom:apexcharts-card
    header:
      title: Monthly Energy Cost
    graph_span: 12mo
    span:
      start: year
    series:
      - entity: sensor.electricity_cost_this_month
        type: column
        group_by:
          func: last
          duration: 1mo
```

## Requirements

### Must Have (MVP)

- [ ] P1 port reader installed and connected
- [ ] Real-time electricity consumption visible
- [ ] Daily/monthly consumption tracking
- [ ] Basic cost calculation with dynamic prices
- [ ] Energy dashboard configured

### Should Have

- [ ] Gas consumption tracking
- [ ] Cost comparison (spot vs. fixed)
- [ ] High consumption alerts
- [ ] Historical graphs and trends

### Could Have (Future)

- [ ] Water meter integration
- [ ] Export data to CSV/spreadsheet
- [ ] Integration with energy supplier billing
- [ ] Solar production tracking and optimization

### Won't Have (Out of Scope)

- [ ] Direct Fluvius billing integration
- [ ] Meter installation or configuration
- [ ] Multi-dwelling/apartment meter aggregation

## Configuration Files

```
src/
├── config/
│   ├── configuration.yaml    # Utility meters, energy integration
│   ├── sensors.yaml          # Cost calculation templates
│   ├── automations.yaml      # Alert automations
│   └── secrets.yaml          # API credentials (if using Fluvius API)
└── scripts/
    └── fluvius_cost_calculator.py  # Optional: Advanced cost analysis
```

## Setup Steps

1. **Hardware Setup** (if using P1 port)
   - Purchase P1 reader (HomeWizard P1, SlimmeLezer+, etc.)
   - Connect to Fluvius meter P1 port
   - Add to local network

2. **Home Assistant Integration**
   - Install relevant integration (HomeWizard, DSMR, or Fluvius HACS)
   - Configure via UI
   - Verify sensors appear

3. **Energy Dashboard**
   - Configure Home Assistant Energy Dashboard
   - Map consumption and production sensors

4. **Cost Calculation**
   - Add template sensors for cost calculation
   - Enter Total Energies rate components
   - Link to electricity price sensors

5. **Utility Meters**
   - Configure daily/monthly utility meters
   - Verify reset cycles work correctly

## Hardware Recommendations

| Device | Price Range | Features |
|--------|-------------|----------|
| **HomeWizard P1 Meter** | ~30 | WiFi, easy setup, app included |
| **SlimmeLezer+** | ~30 | WiFi, ESPHome compatible, DIY-friendly |
| **Fluvius P1 Cable** | ~20 | USB, requires always-on computer/Pi |

## Dependencies

- Fluvius digital meter with P1 port enabled
- Belgian Electricity Prices feature (for spot price integration)
- P1 reader hardware (for real-time data)
- Network connectivity for hardware

## Success Metrics

- Real-time power consumption visible within 10 seconds
- Accurate monthly cost tracking (within 5% of actual bill)
- Clear visibility into energy flow (consumption vs. injection)
- Spot price savings quantified and tracked

## References

- [Fluvius Digital Meter Info](https://www.fluvius.be/nl/thema/meters-en-meterstanden/digitale-meter)
- [Home Assistant DSMR Integration](https://www.home-assistant.io/integrations/dsmr/)
- [HomeWizard P1 Meter](https://www.homewizard.com/p1-meter/)
- [SlimmeLezer+ (ESPHome)](https://www.zuidwijk.com/product/slimmelezer-plus/)
- [Home Assistant Energy Dashboard](https://www.home-assistant.io/docs/energy/)
- [Belgian Electricity Prices PRD](./belgium-electricity-prices.md)
