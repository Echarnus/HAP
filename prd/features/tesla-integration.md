# Feature: Tesla Integration

## Overview

Integrate Tesla Wall Charger and Tesla Vehicle into Home Assistant for smart charging based on electricity prices and vehicle status monitoring.

## Problem Statement

With a Tesla Wall Charger at home and a dynamic electricity contract (Total Energies), there's an opportunity to optimize charging costs by automatically charging when electricity prices are lowest. Additionally, monitoring the vehicle's battery state, location, and climate control from Home Assistant enables unified smart home management.

## User Stories

1. **As a user**, I want my Tesla to automatically charge during the cheapest electricity hours so I save money without manual intervention.

2. **As a user**, I want to see my Tesla's battery percentage and estimated range on my Home Assistant dashboard so I know when charging is needed.

3. **As a user**, I want to manually start/stop charging from Home Assistant when needed, overriding automatic schedules.

4. **As a user**, I want to precondition my car's climate before departure so the cabin is comfortable when I leave.

5. **As a user**, I want to receive notifications when charging completes or if charging fails unexpectedly.

6. **As a user**, I want to see my vehicle's location on a map in Home Assistant for family coordination.

## Components

### 1. Tesla Wall Charger

**Capabilities via Home Assistant**:
- Start/stop charging
- Set charging current (amps)
- View charging status (charging, stopped, scheduled)
- View power consumption during charging

### 2. Tesla Vehicle

**Capabilities via Home Assistant**:
- Battery percentage and estimated range
- Charging state (plugged in, charging, complete)
- Location (GPS coordinates)
- Climate control (HVAC on/off, set temperature)
- Lock/unlock doors
- Sentry mode status

## Technical Implementation

### 1. Tesla Fleet API Setup

**Prerequisites**:
1. Tesla account with registered vehicle
2. Tesla Developer Account (developer.tesla.com)
3. Create application to obtain API credentials
4. Generate OAuth tokens for Home Assistant

**Note**: Tesla transitioned from the unofficial Owner's API to the official Fleet API in 2024. The Fleet API requires developer registration but provides stable, supported access.

### 2. Home Assistant Integration

**Option A: Native Tesla Integration (Recommended)**

Home Assistant has a built-in Tesla integration that uses the Fleet API:

```yaml
# Configuration is done via UI (Integrations page)
# After setup, the following entities are created automatically
```

**Setup via UI**:
1. Go to Settings > Devices & Services
2. Add Integration > Tesla Fleet
3. Follow OAuth flow to authorize Home Assistant

### 3. Entities Created

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.tesla_battery_level` | sensor | Battery percentage (0-100%) |
| `sensor.tesla_range` | sensor | Estimated range (km) |
| `sensor.tesla_charging_state` | sensor | Charging/Stopped/Complete |
| `binary_sensor.tesla_plugged_in` | binary_sensor | Is charger connected |
| `switch.tesla_charger` | switch | Start/stop charging |
| `climate.tesla_hvac` | climate | Climate control |
| `device_tracker.tesla_location` | device_tracker | Vehicle GPS location |
| `lock.tesla_doors` | lock | Door lock control |
| `number.tesla_charge_limit` | number | Target charge percentage |
| `number.tesla_charging_amps` | number | Charging current limit |

### 4. Smart Charging Automation

Integrate with the Belgian Electricity Prices feature for cost-optimized charging:

```yaml
# automations.yaml
automation:
  - alias: "Tesla Smart Charging - Start on Low Price"
    description: "Start Tesla charging when electricity price is cheap"
    trigger:
      - platform: time_pattern
        minutes: "/5"
    condition:
      - condition: state
        entity_id: binary_sensor.tesla_plugged_in
        state: "on"
      - condition: numeric_state
        entity_id: sensor.tesla_battery_level
        below: 80
      - condition: template
        value_template: >
          {% set current_price = states('sensor.electricity_price_current') | float %}
          {% set today_prices = state_attr('sensor.entsoe_prices', 'prices_today') %}
          {% set cheapest_4 = today_prices | sort | list[:4] %}
          {{ current_price <= cheapest_4[-1] }}
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.tesla_charger
      - service: notify.mobile_app
        data:
          title: "Tesla Charging Started"
          message: "Charging at {{ states('sensor.electricity_price_current') }} EUR/kWh"

  - alias: "Tesla Smart Charging - Stop on High Price"
    description: "Stop Tesla charging when price exceeds threshold"
    trigger:
      - platform: numeric_state
        entity_id: sensor.electricity_price_current
        above: 0.20
    condition:
      - condition: state
        entity_id: switch.tesla_charger
        state: "on"
      - condition: numeric_state
        entity_id: sensor.tesla_battery_level
        above: 50  # Don't stop if battery is too low
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.tesla_charger
      - service: notify.mobile_app
        data:
          title: "Tesla Charging Paused"
          message: "Price spike: {{ states('sensor.electricity_price_current') }} EUR/kWh. Battery at {{ states('sensor.tesla_battery_level') }}%"

  - alias: "Tesla Charging Complete Notification"
    trigger:
      - platform: state
        entity_id: sensor.tesla_charging_state
        to: "Complete"
    action:
      - service: notify.mobile_app
        data:
          title: "Tesla Fully Charged"
          message: "Battery at {{ states('sensor.tesla_battery_level') }}% ({{ states('sensor.tesla_range') }} km range)"
```

### 5. Climate Preconditioning

```yaml
# automations.yaml
automation:
  - alias: "Tesla Precondition for Morning Commute"
    description: "Warm up/cool down car before departure"
    trigger:
      - platform: time
        at: "07:30:00"
    condition:
      - condition: time
        weekday:
          - mon
          - tue
          - wed
          - thu
          - fri
      - condition: state
        entity_id: binary_sensor.tesla_plugged_in
        state: "on"  # Only precondition if plugged in (uses grid, not battery)
    action:
      - service: climate.turn_on
        target:
          entity_id: climate.tesla_hvac
      - service: climate.set_temperature
        target:
          entity_id: climate.tesla_hvac
        data:
          temperature: 20
```

### 6. Dashboard Cards

```yaml
# ui-lovelace.yaml
type: vertical-stack
cards:
  - type: entity
    entity: sensor.tesla_battery_level
    name: Tesla Battery
    icon: mdi:battery-car

  - type: gauge
    entity: sensor.tesla_battery_level
    name: Battery Level
    min: 0
    max: 100
    severity:
      green: 60
      yellow: 30
      red: 10

  - type: entities
    title: Tesla Controls
    entities:
      - entity: switch.tesla_charger
        name: Charging
      - entity: lock.tesla_doors
        name: Door Lock
      - entity: climate.tesla_hvac
        name: Climate
      - entity: number.tesla_charge_limit
        name: Charge Limit

  - type: map
    title: Tesla Location
    entities:
      - device_tracker.tesla_location
    aspect_ratio: 16:9
```

## Requirements

### Must Have (MVP)

- [ ] Tesla Fleet API credentials configured
- [ ] Home Assistant Tesla integration connected
- [ ] Battery level and range visible on dashboard
- [ ] Manual start/stop charging from dashboard
- [ ] Basic smart charging automation (charge when cheap)

### Should Have

- [ ] Charging completion notifications
- [ ] Climate preconditioning automation
- [ ] Vehicle location on dashboard map
- [ ] Integration with electricity price forecasts for scheduling

### Could Have (Future)

- [ ] Departure time-based charging optimization
- [ ] Multiple vehicle support
- [ ] Charging cost tracking and statistics
- [ ] Integration with calendar for automatic departure times

### Won't Have (Out of Scope)

- [ ] Direct Wall Charger hardware integration (uses vehicle API)
- [ ] Third-party charging network integration
- [ ] Autonomous driving features

## Configuration Files

```
src/
├── config/
│   ├── configuration.yaml    # Tesla integration reference
│   ├── automations.yaml      # Smart charging automations
│   ├── sensors.yaml          # Any template sensors needed
│   └── secrets.yaml          # Tesla API credentials (not in git)
└── scripts/
    └── tesla_charging_optimizer.py  # Optional: advanced scheduling logic
```

## Setup Steps

1. **Create Tesla Developer Account**
   - Go to developer.tesla.com
   - Register application
   - Note Client ID and Client Secret

2. **Configure Home Assistant**
   - Install Tesla Fleet integration via UI
   - Complete OAuth authorization flow
   - Verify entities appear in Home Assistant

3. **Add Secrets**
   - Add any API credentials to `secrets.yaml` on Pi

4. **Configure Automations**
   - Add smart charging automations from this PRD
   - Customize thresholds and schedules

5. **Create Dashboard**
   - Add Tesla cards to Lovelace dashboard
   - Verify all controls work

## Dependencies

- Belgian Electricity Prices feature (for smart charging optimization)
- Working internet connection on Pi
- Tesla account with active vehicle subscription (for API access)

## Security Considerations

- Tesla API tokens are sensitive - store in `secrets.yaml` only
- Consider token refresh automation (handled by integration)
- Lock/climate controls should not be exposed externally without authentication

## Success Metrics

- 15-30% reduction in charging costs through price optimization
- No manual intervention needed for daily charging
- Climate preconditioning works reliably
- All vehicle status visible in Home Assistant

## References

- [Tesla Fleet API Documentation](https://developer.tesla.com/docs/fleet-api)
- [Home Assistant Tesla Integration](https://www.home-assistant.io/integrations/tesla_fleet/)
- [Belgian Electricity Prices PRD](./belgium-electricity-prices.md)
