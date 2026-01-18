# Feature: Zaffer Roller Shutters

## Overview

Integrate Zaffer roller shutters ("rolluiken") into Home Assistant for smartphone-based control via the Home Assistant mobile app and dashboard.

## Problem Statement

The roller shutters are currently controlled via their native Zaffer system. To unify smart home control and enable future automation possibilities, the shutters need to be integrated into Home Assistant.

## User Stories

1. **As a user**, I want to open and close my roller shutters from my smartphone so I can control them from anywhere in the house (or remotely).

2. **As a user**, I want to see the current position of each roller shutter on my Home Assistant dashboard so I know their status at a glance.

3. **As a user**, I want to control individual shutters or groups of shutters so I can manage them efficiently.

4. **As a user**, I want to set shutters to a specific position (e.g., 50% closed) for partial shading.

## Research Required

### Protocol Discovery

**Status**: Needs investigation

**Note**: User has a Zigbee receiver available. If Zaffer uses Zigbee protocol, integration via Zigbee2MQTT is the preferred approach (more IaC-friendly than ZHA). However, the Zaffer protocol has NOT been confirmed as Zigbee - research is still required.

The communication protocol used by the Zaffer system must be identified. Common protocols for roller shutters include:

| Protocol | Detection Method | Home Assistant Support | Notes |
|----------|------------------|----------------------|-------|
| **Zigbee** | Check for Zigbee logo; often paired with hub | Native via ZHA or Zigbee2MQTT | **Preferred if applicable** - User has receiver |
| **Z-Wave** | Check for Z-Wave logo on motor/controller | Native via Z-Wave JS | Requires Z-Wave controller |
| **WiFi/Local API** | Check if device has WiFi setup; scan network | Custom integration or REST/MQTT | Good for IaC |
| **RF 433MHz** | Remote control with no hub; uses radio frequency | Via Broadlink RM or Sonoff RF Bridge | May need RF bridge |
| **Proprietary Hub** | Zaffer-branded bridge/gateway | May need reverse engineering or cloud API | Last resort |

### Research Tasks

- [ ] Identify Zaffer product model numbers
- [ ] Check physical devices for protocol logos (Z-Wave, Zigbee)
- [ ] Check if Zaffer has a hub/bridge device on the network
- [ ] Scan local network for Zaffer devices (if WiFi-based)
- [ ] Research Zaffer API documentation (if available)
- [ ] Check Home Assistant community for existing Zaffer integrations

### Research Script

A Python script will be created to help discover Zaffer devices on the network:

```python
# src/scripts/zaffer_discovery.py
"""
Zaffer device discovery script.
Scans local network for potential Zaffer devices.
"""

import socket
import subprocess
from typing import List, Dict

def scan_network(subnet: str = "192.168.1.0/24") -> List[Dict]:
    """
    Scan local network for devices.
    Returns list of discovered devices with IP and hostname.
    """
    # Implementation: Use nmap or ARP scan
    # Look for devices with Zaffer-related hostnames or known MAC prefixes
    pass

def check_common_ports(ip: str) -> Dict[str, bool]:
    """
    Check common smart home ports on a device.
    """
    ports = {
        80: "HTTP",
        443: "HTTPS",
        8080: "HTTP Alt",
        1883: "MQTT",
        8883: "MQTT SSL",
    }
    # Implementation: Port scanning
    pass

if __name__ == "__main__":
    print("Scanning for Zaffer devices...")
    # Run discovery
```

## Technical Implementation

### Integration Approach (TBD based on research)

#### Option A: Zigbee2MQTT Integration (Preferred if Zigbee)

If Zaffer uses Zigbee protocol, integrate via Zigbee2MQTT:

```yaml
# src/config/zigbee2mqtt/configuration.yaml
homeassistant: true
mqtt:
  base_topic: zigbee2mqtt
  server: mqtt://localhost:1883

frontend:
  port: 8080

devices:
  # Devices will be added automatically after pairing
  # Example after pairing:
  # '0x00158d0001234567':
  #   friendly_name: living_room_shutter

groups:
  # Optional: Group shutters for unified control
  # '1':
  #   friendly_name: all_shutters
  #   devices:
  #     - living_room_shutter
  #     - bedroom_shutter
```

**Benefits of Zigbee2MQTT over ZHA**:
- Configuration stored in YAML (IaC-friendly)
- Coordinator backup exportable
- More device compatibility
- Web-based frontend for debugging

#### Option B: Native Home Assistant Integration

If Zaffer uses Z-Wave or has a HACS integration:

```yaml
# src/config/configuration.yaml
# Example for Z-Wave
zwave_js:
  # Z-Wave JS configuration
```

#### Option C: Custom Python Integration

If no native integration exists, create a custom component:

```
src/
└── config/
    └── custom_components/
        └── zaffer/
            ├── __init__.py
            ├── manifest.json
            ├── cover.py        # Roller shutter entity
            ├── config_flow.py  # UI configuration
            └── const.py        # Constants
```

#### Option D: Python Script + REST/MQTT Bridge

If Zaffer has an API but no HA integration, create a bridge:

```python
# src/scripts/zaffer_bridge.py
"""
Bridge between Zaffer API and Home Assistant via MQTT.
"""

import paho.mqtt.client as mqtt
import requests
from dataclasses import dataclass

@dataclass
class RollerShutter:
    id: str
    name: str
    position: int  # 0 = closed, 100 = open

    def open(self):
        """Open the shutter completely."""
        pass

    def close(self):
        """Close the shutter completely."""
        pass

    def set_position(self, position: int):
        """Set shutter to specific position (0-100)."""
        pass

class ZafferBridge:
    """Bridge Zaffer devices to Home Assistant via MQTT."""

    def __init__(self, zaffer_host: str, mqtt_host: str):
        self.zaffer_host = zaffer_host
        self.mqtt_client = mqtt.Client()
        # Implementation
        pass

    def discover_shutters(self) -> list[RollerShutter]:
        """Discover all roller shutters from Zaffer system."""
        pass

    def publish_state(self, shutter: RollerShutter):
        """Publish shutter state to MQTT for Home Assistant."""
        pass

    def handle_command(self, shutter_id: str, command: str):
        """Handle commands from Home Assistant."""
        pass
```

### Home Assistant Entity Configuration

Once integrated, shutters appear as `cover` entities:

```yaml
# src/config/configuration.yaml
cover:
  - platform: mqtt  # Or native integration
    covers:
      living_room_shutter:
        name: "Living Room Roller Shutter"
        command_topic: "zaffer/living_room/set"
        state_topic: "zaffer/living_room/state"
        position_topic: "zaffer/living_room/position"
        set_position_topic: "zaffer/living_room/set_position"
```

### Dashboard Controls

```yaml
# Lovelace card for roller shutter control
type: entities
title: Roller Shutters
entities:
  - entity: cover.living_room_shutter
    name: Living Room
  - entity: cover.bedroom_shutter
    name: Bedroom
  - entity: cover.kitchen_shutter
    name: Kitchen

# Or use a custom button card for visual control
type: custom:button-card
entity: cover.living_room_shutter
name: Living Room
icon: mdi:window-shutter
tap_action:
  action: toggle
hold_action:
  action: more-info
```

### Mobile App Control

Once integrated, shutters will automatically appear in the Home Assistant Companion App:

- **Quick Actions**: Open/Close/Stop buttons
- **Position Slider**: Set specific position
- **Grouping**: Can create groups for "All Shutters" control

## Requirements

### Must Have (MVP)

- [ ] Identify Zaffer communication protocol
- [ ] Basic open/close control from Home Assistant
- [ ] Individual shutter control via smartphone app
- [ ] Shutter status visible on dashboard

### Should Have

- [ ] Position control (0-100%)
- [ ] Group control (e.g., "All Shutters", "Ground Floor")
- [ ] Stop command for mid-position control

### Could Have (Future)

- [ ] Sun-based automation (open at sunrise, close at sunset)
- [ ] Temperature-based automation (close when hot)
- [ ] Scheduled automation
- [ ] Integration with weather forecast (close before rain/storm)

### Won't Have (Out of Scope for MVP)

- Voice control (requires separate Alexa/Google integration)
- Physical button integration
- Motor calibration/setup

## Configuration Files

This feature will add/modify the following files:

```
src/
├── config/
│   ├── configuration.yaml      # Zaffer integration config
│   └── custom_components/      # If custom integration needed
│       └── zaffer/
└── scripts/
    ├── zaffer_discovery.py     # Network discovery script
    └── zaffer_bridge.py        # API bridge (if needed)
```

## Setup Steps

1. **Research Phase**
   - Run discovery script to find Zaffer devices
   - Identify protocol and available APIs
   - Document findings

2. **Integration Phase**
   - Install appropriate integration (native or custom)
   - Configure devices in Home Assistant
   - Test basic open/close functionality

3. **Dashboard Phase**
   - Add shutter controls to Lovelace dashboard
   - Verify mobile app access
   - Create shutter groups if needed

## Success Metrics

- All roller shutters controllable from Home Assistant app
- Response time under 2 seconds for commands
- Reliable status updates in dashboard
- No dependency on Zaffer's native app for daily use

## Dependencies

- Home Assistant OS running on Raspberry Pi
- Network connectivity to Zaffer system (or appropriate hardware bridge)
- Python 3.x for custom scripts

## References

- [Home Assistant Cover Integration](https://www.home-assistant.io/integrations/cover/)
- [Home Assistant MQTT Cover](https://www.home-assistant.io/integrations/cover.mqtt/)
- [Custom Component Development](https://developers.home-assistant.io/docs/creating_component_index)
- Zaffer documentation (TBD after research)
