# Feature: Belgian Electricity Prices

## Overview

Integrate real-time and day-ahead Belgian electricity spot prices into Home Assistant to enable smart EV charging during the cheapest hours.

## Problem Statement

With a dynamic electricity contract (Total Energies), electricity prices vary hourly based on the EPEX/Belpex spot market. Manually checking prices and timing EV charging is impractical. Automation is needed to:

1. Fetch current and upcoming electricity prices
2. Identify the cheapest charging windows
3. Automatically control EV charging based on price thresholds

## User Stories

1. **As a user**, I want to see current electricity prices on my Home Assistant dashboard so I can make informed decisions about energy usage.

2. **As a user**, I want Home Assistant to automatically start EV charging during the cheapest hours overnight so I save money without manual intervention.

3. **As a user**, I want to receive notifications when electricity prices drop below a threshold so I can run high-consumption appliances.

4. **As a user**, I want to see a forecast of tomorrow's prices (available after 13:00 CET) so I can plan accordingly.

## Data Sources

### Primary: ENTSO-E Transparency Platform

- **What**: Official EU platform for electricity market data
- **Coverage**: Belgian bidding zone (BE) day-ahead prices
- **Update Frequency**: Day-ahead prices published ~13:00 CET daily
- **Cost**: Free (requires registration for API key)
- **API**: RESTful XML/JSON API
- **Home Assistant Integration**: Available via HACS

### Alternative: EPEX Spot

- **What**: European Power Exchange spot market
- **Note**: Direct API access typically requires commercial agreement
- **Better Option**: Use ENTSO-E which publishes EPEX data

### Total Energies Consideration

Total Energies dynamic contracts in Belgium are based on EPEX spot prices plus:
- Energy component markup
- Distribution costs (grid operator)
- Transmission costs
- Taxes and levies

The ENTSO-E data provides the base spot price. Additional costs can be configured as fixed offsets in Home Assistant.

## Technical Implementation

### 1. Home Assistant Integration

**Option A: ENTSO-E Integration (Recommended)**

```yaml
# configuration.yaml
sensor:
  - platform: entsoe
    api_key: !secret entsoe_api_key
    region: "BE"  # Belgium
    currency: "EUR"
```

Install via HACS: `ENTSO-E Tariff` integration

**Option B: Nordpool Integration**

```yaml
# Also available via HACS, supports Belgian prices
sensor:
  - platform: nordpool
    region: "BE"
```

### 2. Sensors Created

The integration will create sensors such as:

| Sensor | Description |
|--------|-------------|
| `sensor.electricity_price_current` | Current hour's spot price (EUR/kWh) |
| `sensor.electricity_price_next_hour` | Next hour's price |
| `sensor.electricity_price_today_min` | Lowest price today |
| `sensor.electricity_price_today_max` | Highest price today |
| `sensor.electricity_price_average` | Average price today |
| `sensor.electricity_price_tomorrow_*` | Tomorrow's prices (after 13:00) |

### 3. Total Cost Calculation

Create a template sensor that adds Total Energies margins:

```yaml
# sensors.yaml
template:
  - sensor:
      - name: "Electricity Total Cost"
        unit_of_measurement: "EUR/kWh"
        state: >
          {% set spot_price = states('sensor.electricity_price_current') | float %}
          {% set markup = 0.005 %}        {# Total Energies markup per kWh #}
          {% set distribution = 0.05 %}   {# Grid costs estimate #}
          {% set taxes = 0.03 %}          {# Taxes estimate #}
          {{ (spot_price + markup + distribution + taxes) | round(4) }}
```

*Note: Actual values for markup/distribution/taxes should be taken from your Total Energies contract.*

### 4. EV Charging Automation

**Note**: For Tesla Wall Charger integration, see [Tesla Integration PRD](./tesla-integration.md) which provides detailed automations that build on these price sensors.

```yaml
# automations.yaml
automation:
  - alias: "EV Smart Charging - Start"
    description: "Start charging when price is in cheapest 4 hours of night"
    trigger:
      - platform: time_pattern
        minutes: "/15"
    condition:
      - condition: time
        after: "22:00:00"
        before: "07:00:00"
      - condition: state
        entity_id: binary_sensor.tesla_plugged_in  # Tesla entity
        state: "on"
      - condition: numeric_state
        entity_id: sensor.electricity_price_current
        below: "sensor.electricity_price_today_min"
        value_template: "{{ state_attr('sensor.entsoe_prices', 'prices_today') | sort | list[:4] | max }}"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.tesla_charger  # Tesla entity

  - alias: "EV Smart Charging - Stop"
    description: "Stop charging when price exceeds threshold"
    trigger:
      - platform: numeric_state
        entity_id: sensor.electricity_price_current
        above: 0.15  # EUR/kWh threshold
    condition:
      - condition: state
        entity_id: switch.tesla_charger  # Tesla entity
        state: "on"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.tesla_charger  # Tesla entity
```

### 5. Dashboard Card

```yaml
# Lovelace card example
type: custom:apexcharts-card
header:
  title: Electricity Prices Today
  show: true
graph_span: 24h
span:
  start: day
series:
  - entity: sensor.entsoe_prices
    data_generator: |
      return entity.attributes.prices_today.map((price, index) => {
        return [new Date().setHours(index, 0, 0, 0), price];
      });
```

## Requirements

### Must Have (MVP)

- [ ] ENTSO-E API integration configured
- [ ] Current price sensor visible in dashboard
- [ ] Price graph showing today's prices
- [ ] Basic automation: charge EV when price below threshold

### Should Have

- [ ] Tomorrow's prices displayed (after 13:00 publication)
- [ ] Total cost sensor including Total Energies margins
- [ ] Notification when prices are exceptionally low/high
- [ ] Weekly/monthly cost tracking

### Could Have

- [ ] Price prediction beyond day-ahead
- [ ] Integration with solar production forecast
- [ ] Battery storage optimization (if applicable)
- [ ] Multi-tariff support (day/night rates as backup)

### Won't Have (Out of Scope)

- Direct Total Energies API integration (not publicly available)
- Real-time (sub-hourly) pricing
- Automatic contract optimization recommendations

## Configuration Files

This feature will add/modify the following files in the repository:

```
src/
└── config/
    ├── configuration.yaml    # ENTSO-E integration setup
    ├── sensors.yaml          # Total cost template sensor
    ├── automations.yaml      # EV charging automations
    └── secrets.yaml          # ENTSO-E API key (not in git)
```

## Setup Steps

1. Register at ENTSO-E Transparency Platform and obtain API key
2. Install ENTSO-E integration via HACS
3. Add API key to `secrets.yaml` on Raspberry Pi
4. Configure sensors and automations per this PRD
5. Create dashboard cards for price visualization
6. Test automations with EV charger integration

## Success Metrics

- Electricity costs reduced by 15-30% for EV charging
- Charging automatically occurs during cheapest hours
- No manual intervention required for daily charging
- Dashboard provides clear visibility into pricing

## Dependencies

- ENTSO-E API account (free registration)
- Home Assistant with HACS installed
- For EV charging: [Tesla Integration](./tesla-integration.md)
- For cost tracking: [Fluvius Metering](./fluvius-metering.md)

## References

- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)
- [ENTSO-E API Documentation](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- [HACS ENTSO-E Integration](https://github.com/JaccoR/hass-entso-e)
- [Belgian Electricity Market Info (CREG)](https://www.creg.be/)
- [Tesla Integration PRD](./tesla-integration.md) - Smart charging with Tesla Wall Charger
- [Fluvius Metering PRD](./fluvius-metering.md) - Consumption tracking and cost calculation
