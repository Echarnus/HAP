# Feature: EEVEE Mobility Integration

## Overview

Track public EV charging sessions from the EEVEE Mobility subscription on the Home Assistant dashboard, providing visibility into charging costs and history.

## Problem Statement

With an EEVEE Mobility subscription for public charging in Belgium, charging sessions and costs are tracked separately from home charging. To have a complete overview of all EV-related energy consumption and costs, public charging data needs to be integrated into Home Assistant.

## User Stories

1. **As a user**, I want to see my recent public charging sessions on my Home Assistant dashboard so I have visibility into my EV usage.

2. **As a user**, I want to track monthly public charging costs alongside home charging costs so I can compare and optimize.

3. **As a user**, I want to see total kWh consumed at public chargers to track my overall EV energy usage.

4. **As a user**, I want to receive a notification when a public charging session completes so I know my car is ready.

## Research Required

### API Discovery

**Status**: Needs investigation

EEVEE Mobility may or may not have a public API. Research tasks:

- [ ] Check EEVEE Mobility app for API hints (network inspection)
- [ ] Contact EEVEE support about API availability
- [ ] Research if EEVEE uses a white-label platform (e.g., has-to-be, Hubject) that might have documented APIs
- [ ] Check for unofficial API documentation or community integrations
- [ ] Investigate if data can be exported (CSV, PDF) for manual import

### Potential Data Sources

| Source | Feasibility | Notes |
|--------|-------------|-------|
| **Official API** | Unknown | Best option if available |
| **App API (reverse engineered)** | Medium | May break with app updates |
| **Email parsing** | Low effort | Parse charging receipts from email |
| **Manual CSV export** | Fallback | If EEVEE has data export feature |
| **OCPP integration** | Unlikely | Requires charge point operator access |

## Technical Implementation

### Option A: EEVEE API Integration (if API exists)

If EEVEE provides an API, create a custom integration or Python script:

```python
# src/scripts/eevee_sync.py
"""
Sync EEVEE Mobility charging sessions to Home Assistant.
"""

import requests
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import json

@dataclass
class ChargingSession:
    """Represents a public charging session."""
    session_id: str
    start_time: datetime
    end_time: datetime
    location: str
    energy_kwh: float
    cost_eur: float
    charge_point_id: str

class EEVEEClient:
    """Client for EEVEE Mobility API."""

    def __init__(self, username: str, password: str):
        self.base_url = "https://api.eevee.be"  # TBD: Actual API endpoint
        self.session = requests.Session()
        self._authenticate(username, password)

    def _authenticate(self, username: str, password: str):
        """Authenticate with EEVEE API."""
        # Implementation depends on actual API
        pass

    def get_sessions(self, from_date: datetime, to_date: datetime) -> List[ChargingSession]:
        """Fetch charging sessions for date range."""
        # Implementation depends on actual API
        pass

    def get_latest_session(self) -> Optional[ChargingSession]:
        """Get the most recent charging session."""
        pass

def sync_to_home_assistant(sessions: List[ChargingSession], ha_url: str, token: str):
    """Push charging session data to Home Assistant."""
    headers = {"Authorization": f"Bearer {token}"}

    # Update sensors via REST API
    for session in sessions:
        # Implementation
        pass

if __name__ == "__main__":
    # This script can be run via Home Assistant's shell_command
    # or scheduled via cron on the Pi
    pass
```

### Option B: Email Parsing Fallback

If no API exists, parse charging receipts from email:

```python
# src/scripts/eevee_email_parser.py
"""
Parse EEVEE charging receipts from email.
"""

import imaplib
import email
from email.header import decode_header
import re
from dataclasses import dataclass

@dataclass
class ParsedReceipt:
    date: str
    location: str
    energy_kwh: float
    cost_eur: float

def connect_to_email(server: str, username: str, password: str):
    """Connect to IMAP email server."""
    mail = imaplib.IMAP4_SSL(server)
    mail.login(username, password)
    return mail

def search_eevee_emails(mail, folder: str = "INBOX"):
    """Search for EEVEE charging receipt emails."""
    mail.select(folder)
    # Search for emails from EEVEE
    _, messages = mail.search(None, 'FROM "eevee"')
    return messages[0].split()

def parse_receipt(email_body: str) -> ParsedReceipt:
    """Extract charging data from receipt email."""
    # Regex patterns to extract data
    # Implementation depends on actual email format
    pass
```

### Option C: Manual Entry via Input Helpers

Fallback for manual tracking:

```yaml
# configuration.yaml
input_number:
  eevee_last_session_kwh:
    name: "Last EEVEE Session (kWh)"
    min: 0
    max: 100
    step: 0.1
    unit_of_measurement: "kWh"
    icon: mdi:ev-station

  eevee_last_session_cost:
    name: "Last EEVEE Session Cost"
    min: 0
    max: 100
    step: 0.01
    unit_of_measurement: "EUR"
    icon: mdi:currency-eur

input_text:
  eevee_last_session_location:
    name: "Last EEVEE Session Location"
    max: 100
    icon: mdi:map-marker
```

### Home Assistant Sensors

```yaml
# sensors.yaml
template:
  - sensor:
      - name: "EEVEE Monthly Sessions"
        state: "{{ state_attr('sensor.eevee_sessions', 'sessions_this_month') | default(0) }}"
        unit_of_measurement: "sessions"
        icon: mdi:ev-station

      - name: "EEVEE Monthly Cost"
        state: "{{ state_attr('sensor.eevee_sessions', 'cost_this_month') | default(0) | round(2) }}"
        unit_of_measurement: "EUR"
        icon: mdi:currency-eur

      - name: "EEVEE Monthly Energy"
        state: "{{ state_attr('sensor.eevee_sessions', 'kwh_this_month') | default(0) | round(1) }}"
        unit_of_measurement: "kWh"
        icon: mdi:lightning-bolt

      - name: "Total EV Charging Cost"
        state: >
          {% set home = states('sensor.tesla_charging_cost_monthly') | float(0) %}
          {% set public = states('sensor.eevee_monthly_cost') | float(0) %}
          {{ (home + public) | round(2) }}
        unit_of_measurement: "EUR"
        icon: mdi:car-electric
```

### Dashboard Card

```yaml
# ui-lovelace.yaml
type: vertical-stack
title: Public Charging (EEVEE)
cards:
  - type: entities
    entities:
      - entity: sensor.eevee_monthly_sessions
        name: Sessions This Month
      - entity: sensor.eevee_monthly_energy
        name: Energy This Month
      - entity: sensor.eevee_monthly_cost
        name: Cost This Month

  - type: statistic
    entity: sensor.eevee_monthly_cost
    period:
      calendar:
        period: month
    stat_type: sum
    name: Monthly Public Charging

  - type: markdown
    title: Last Session
    content: |
      **Location**: {{ state_attr('sensor.eevee_last_session', 'location') }}
      **Date**: {{ state_attr('sensor.eevee_last_session', 'date') }}
      **Energy**: {{ state_attr('sensor.eevee_last_session', 'kwh') }} kWh
      **Cost**: {{ state_attr('sensor.eevee_last_session', 'cost') }}
```

## Requirements

### Must Have (MVP)

- [ ] Research EEVEE API availability
- [ ] Display recent charging sessions on dashboard
- [ ] Track monthly public charging costs
- [ ] Manual entry fallback if no API

### Should Have

- [ ] Automated sync of charging sessions
- [ ] Combined view of home + public charging costs
- [ ] Charging location map

### Could Have (Future)

- [ ] Historical cost comparison (home vs public)
- [ ] Price per kWh analysis by location
- [ ] Charging station recommendations based on cost

### Won't Have (Out of Scope)

- [ ] Live charging status (no control over public chargers)
- [ ] Reservation or payment functionality
- [ ] Charge point map (use EEVEE app for this)

## Configuration Files

```
src/
├── config/
│   ├── configuration.yaml    # Input helpers for manual entry
│   ├── sensors.yaml          # Template sensors
│   └── secrets.yaml          # EEVEE credentials (if API exists)
└── scripts/
    ├── eevee_sync.py         # API integration script
    └── eevee_email_parser.py # Email parsing fallback
```

## Setup Steps

1. **Research Phase**
   - Investigate EEVEE API availability
   - Test API endpoints if found
   - Document authentication method

2. **Implementation Phase**
   - If API: Implement `eevee_sync.py`
   - If no API: Set up email parsing or manual entry
   - Add secrets to Pi

3. **Dashboard Phase**
   - Add EEVEE section to dashboard
   - Create combined EV charging cost view

## Dependencies

- EEVEE Mobility account and subscription
- Internet connectivity for API/email access
- Optional: Email account access for receipt parsing

## Priority

**Medium** - This feature enhances visibility but doesn't enable new automation capabilities. Home charging optimization (Tesla integration) is higher priority.

## Success Metrics

- All public charging sessions tracked in Home Assistant
- Monthly cost overview includes both home and public charging
- No manual effort required for session tracking (if API available)

## References

- [EEVEE Mobility Website](https://www.eevee.be/)
- [Tesla Integration PRD](./tesla-integration.md) - For combined EV cost tracking
