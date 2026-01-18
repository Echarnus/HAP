# Feature: Local Development Environment

## Overview

Set up a local Docker-based Home Assistant development environment to test configuration changes before deploying to the Raspberry Pi, ensuring YAML syntax is valid and automations work as expected.

## Problem Statement

Deploying broken configuration to the Raspberry Pi can cause Home Assistant to fail to start, requiring manual intervention to fix. A local development environment enables:

1. Pre-deployment validation of YAML syntax
2. Testing automations with mock sensors
3. Dashboard development without affecting production
4. Faster iteration cycles

## User Stories

1. **As a developer**, I want to test my Home Assistant configuration locally before deploying so I don't break my production instance.

2. **As a developer**, I want to validate YAML syntax automatically so I catch errors before committing.

3. **As a developer**, I want to test automations with mock sensors so I can verify logic without real devices.

4. **As a developer**, I want to develop dashboards locally so I can iterate quickly on UI changes.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Local Development Machine                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      Docker Compose                          ││
│  │  ┌─────────────────────┐  ┌─────────────────────────────┐  ││
│  │  │   Home Assistant    │  │     Zigbee2MQTT (optional)   │  ││
│  │  │   Container         │  │     Container                │  ││
│  │  │   Port: 8123        │  │     Port: 8080               │  ││
│  │  │                     │  │     (no hardware - config    │  ││
│  │  │   Mounts:           │  │      validation only)        │  ││
│  │  │   ./src/config →    │  │                              │  ││
│  │  │     /config         │  │     Mounts:                  │  ││
│  │  └─────────────────────┘  │     ./src/config/zigbee2mqtt │  ││
│  │                           │       → /app/data            │  ││
│  │                           └─────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Mock Sensors Script                       ││
│  │     Simulates device data for testing automations            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ After testing: git push
                              ▼
                    GitHub Actions deploys
                    to Raspberry Pi
```

## Technical Implementation

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  homeassistant:
    container_name: hap-dev-homeassistant
    image: ghcr.io/home-assistant/home-assistant:stable
    volumes:
      - ./src/config:/config
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "8123:8123"
    environment:
      - TZ=Europe/Brussels
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8123/api/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Optional: Zigbee2MQTT for config validation (no actual hardware)
  zigbee2mqtt:
    container_name: hap-dev-zigbee2mqtt
    image: koenkk/zigbee2mqtt:latest
    volumes:
      - ./src/config/zigbee2mqtt:/app/data
    ports:
      - "8080:8080"
    environment:
      - TZ=Europe/Brussels
    # Will fail without hardware, but validates config
    profiles:
      - zigbee  # Only start with: docker-compose --profile zigbee up
    restart: "no"

volumes:
  ha-config:
```

### Local Secrets Template

```yaml
# src/config/secrets.yaml.local (for development only, gitignored)
# Copy from secrets.yaml.example and fill with test values

# API Keys (use dummy values for local testing)
entsoe_api_key: "test-api-key-not-real"
tesla_client_id: "test-client-id"
tesla_client_secret: "test-client-secret"

# Home Assistant
ha_latitude: 50.8503
ha_longitude: 4.3517
ha_elevation: 13
```

### Mock Sensors for Testing

```yaml
# src/config/mock_sensors.yaml (only loaded in development)
# Include this file conditionally in configuration.yaml

input_number:
  mock_electricity_price:
    name: "Mock Electricity Price"
    min: 0
    max: 1
    step: 0.001
    unit_of_measurement: "EUR/kWh"
    initial: 0.15

  mock_tesla_battery:
    name: "Mock Tesla Battery"
    min: 0
    max: 100
    step: 1
    unit_of_measurement: "%"
    initial: 50

  mock_p1_consumption:
    name: "Mock P1 Consumption"
    min: 0
    max: 10000
    step: 10
    unit_of_measurement: "W"
    initial: 500

input_boolean:
  mock_tesla_plugged_in:
    name: "Mock Tesla Plugged In"
    initial: true

  mock_tesla_charging:
    name: "Mock Tesla Charging"
    initial: false

# Template sensors that mimic real sensors
template:
  - sensor:
      - name: "electricity_price_current"
        unit_of_measurement: "EUR/kWh"
        state: "{{ states('input_number.mock_electricity_price') }}"

      - name: "tesla_battery_level"
        unit_of_measurement: "%"
        state: "{{ states('input_number.mock_tesla_battery') | int }}"

      - name: "p1_electricity_consumption"
        unit_of_measurement: "W"
        state: "{{ states('input_number.mock_p1_consumption') | int }}"

  - binary_sensor:
      - name: "tesla_plugged_in"
        state: "{{ is_state('input_boolean.mock_tesla_plugged_in', 'on') }}"

      - name: "tesla_charging"
        state: "{{ is_state('input_boolean.mock_tesla_charging', 'on') }}"
```

### Configuration Validator Script

```python
#!/usr/bin/env python3
# src/scripts/config_validator.py
"""
Validate Home Assistant configuration files.
Run before committing or deploying.
"""

import subprocess
import sys
import os
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"

def check_yaml_syntax():
    """Check YAML syntax for all configuration files."""
    import yaml

    errors = []
    for yaml_file in CONFIG_DIR.glob("**/*.yaml"):
        # Skip secrets files
        if "secret" in yaml_file.name:
            continue

        try:
            with open(yaml_file) as f:
                yaml.safe_load(f)
            print(f"OK: {yaml_file.name}")
        except yaml.YAMLError as e:
            errors.append((yaml_file, str(e)))
            print(f"ERROR: {yaml_file.name}")
            print(f"  {e}")

    return errors

def check_config_with_ha():
    """Use Home Assistant's config check if available."""
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", "homeassistant",
             "python", "-m", "homeassistant", "--script", "check_config",
             "--config", "/config"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("Home Assistant config check: PASSED")
            return True
        else:
            print("Home Assistant config check: FAILED")
            print(result.stdout)
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("Config check timed out")
        return False
    except FileNotFoundError:
        print("Docker not available, skipping HA config check")
        return True

def main():
    print("Validating Home Assistant configuration...")
    print("=" * 50)

    # Check YAML syntax
    print("\n1. Checking YAML syntax...")
    yaml_errors = check_yaml_syntax()

    # Check with Home Assistant (if running)
    print("\n2. Running Home Assistant config check...")
    ha_check = check_config_with_ha()

    # Summary
    print("\n" + "=" * 50)
    if yaml_errors or not ha_check:
        print("VALIDATION FAILED")
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### Development Workflow

```bash
# Start local Home Assistant
docker compose up -d

# View logs
docker compose logs -f homeassistant

# Validate configuration
python src/scripts/config_validator.py

# Restart after config changes
docker compose restart homeassistant

# Stop environment
docker compose down

# Full rebuild (after Docker image updates)
docker compose pull && docker compose up -d --force-recreate
```

### Git Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit (make executable: chmod +x)

echo "Running config validation..."
python src/scripts/config_validator.py

if [ $? -ne 0 ]; then
    echo "Config validation failed. Commit aborted."
    exit 1
fi

echo "Config validation passed."
exit 0
```

### Conditional Development Configuration

```yaml
# src/config/configuration.yaml

# ... normal configuration ...

# Load mock sensors only in development
# Comment out or remove when deploying to Pi
# Or use environment variable detection
packages:
  # Uncomment for local development testing:
  # mock: !include mock_sensors.yaml
```

## Development vs Production

| Aspect | Local Development | Production (Pi) |
|--------|-------------------|-----------------|
| **Platform** | Docker container | Home Assistant OS |
| **Config source** | Local `src/config/` | Synced via GitHub Actions |
| **Secrets** | `secrets.yaml.local` (test values) | `secrets.yaml` (real credentials) |
| **Hardware** | None (mock sensors) | Real devices |
| **URL** | `http://localhost:8123` | `http://<pi-ip>:8123` |
| **Add-ons** | Limited (containers only) | Full add-on support |

## Limitations

- **No real hardware access**: Cannot test actual Zigbee, Z-Wave, or other hardware integrations
- **No Supervisor**: Home Assistant add-ons don't work in Docker (only HA OS)
- **Limited integrations**: Cloud integrations may not work without real credentials
- **State not persistent**: Database resets when container is removed

## Best Practices

1. **Always validate before committing**: Run `config_validator.py`
2. **Use mock sensors for automation testing**: Don't rely on real data
3. **Keep secrets separate**: Use `.local` suffix for dev secrets
4. **Test dashboard changes locally first**: Faster iteration
5. **Document deviations**: Note what can't be tested locally

## Requirements

### Must Have

- [ ] Docker Compose file for local HA instance
- [ ] Configuration validation script
- [ ] Mock sensors for automation testing
- [ ] Documentation for development workflow

### Should Have

- [ ] Pre-commit hook for validation
- [ ] Example secrets file for development
- [ ] Docker Compose override for development tweaks

### Could Have (Future)

- [ ] Integration test framework
- [ ] Automated UI testing
- [ ] CI/CD pipeline integration for PR validation

## Configuration Files

```
HAP/
├── docker-compose.yml              # Main Docker Compose file
├── docker-compose.override.yml.example  # Development overrides template
├── src/
│   ├── config/
│   │   ├── configuration.yaml
│   │   ├── secrets.yaml.example
│   │   ├── secrets.yaml.local      # Development secrets (gitignored)
│   │   ├── mock_sensors.yaml       # Mock sensors for testing
│   │   └── ...
│   └── scripts/
│       └── config_validator.py     # Validation script
└── .gitignore                      # Includes secrets.yaml.local
```

## Setup Steps

1. **Install Prerequisites**
   - Docker Desktop (Mac/Windows) or Docker Engine (Linux)
   - Python 3.x (for validation script)

2. **Create Development Secrets**
   ```bash
   cp src/config/secrets.yaml.example src/config/secrets.yaml.local
   # Edit with test values
   ```

3. **Start Environment**
   ```bash
   docker compose up -d
   ```

4. **Access Home Assistant**
   - Open `http://localhost:8123`
   - Complete onboarding (first time only)

5. **Install Pre-commit Hook** (optional)
   ```bash
   cp .git/hooks/pre-commit.sample .git/hooks/pre-commit
   # Edit to add validation script call
   chmod +x .git/hooks/pre-commit
   ```

## Success Metrics

- Zero deployment failures due to YAML syntax errors
- Dashboard changes tested locally before production
- Automation logic validated with mock data
- Faster development iteration cycles

## References

- [Home Assistant Docker Installation](https://www.home-assistant.io/installation/linux#docker-compose)
- [Home Assistant Config Check Script](https://www.home-assistant.io/docs/tools/check_config/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
