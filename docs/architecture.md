# Architecture & Infrastructure as Code Analysis

> An honest assessment of what HAP achieves as Infrastructure as Code, its limitations, and the hybrid approach required for Home Assistant.

## Overview

HAP applies Infrastructure-as-Code (IaC) principles to Home Assistant, but with significant caveats. This document explains what IaC means in the context of HAP, what can be managed as code, what cannot, and the hybrid approach needed to bridge the gap.

---

## What IS Infrastructure as Code?

Infrastructure as Code is the practice of managing and provisioning computing resources through machine-readable definition files rather than manual processes.

### True IaC Characteristics

| Characteristic | Description | Example Tools |
|----------------|-------------|---------------|
| **Declarative** | Define desired state, not steps to achieve it | Terraform, Kubernetes YAML |
| **Idempotent** | Applying the same config multiple times yields the same result | Ansible, Puppet |
| **Version Controlled** | All changes tracked in git with history | Any IaC tool + git |
| **Reproducible** | Identical infrastructure from the same code | Terraform, CloudFormation |
| **Automated** | Changes applied without manual intervention | CI/CD pipelines |

### HAP's IaC Score

How does HAP measure up against true IaC principles?

| Characteristic | HAP Score | Reality |
|----------------|-----------|---------|
| Declarative | Partial | YAML is declarative, but not all state is YAML |
| Idempotent | Partial | Config is, but device pairings and state are not |
| Version Controlled | Yes | All YAML config is in git |
| Reproducible | Partial | Config yes, but not device pairings or history |
| Automated | Yes | GitHub Actions deploys on push |

**Honest Assessment**: HAP is approximately **60-70% IaC**. The remaining 30-40% requires manual intervention, backups, and documentation.

---

## HAP Architecture

```
+------------------------------------------------------------------+
|                        GITHUB REPOSITORY                          |
|   +------------------------------------------------------------+ |
|   |                    Version Controlled                       | |
|   |                                                             | |
|   |   src/config/          src/scripts/        .github/         | |
|   |   +------------+       +------------+      workflows/       | |
|   |   |YAML configs|       |Python utils|      +---------+     | |
|   |   |automations |       |validators  |      |deploy   |     | |
|   |   |dashboards  |       |bridges     |      |validate |     | |
|   |   +------------+       +------------+      +---------+     | |
|   +------------------------------------------------------------+ |
+------------------------------------------------------------------+
                               |
                               | SSH + rsync (on git push)
                               v
+------------------------------------------------------------------+
|                     RASPBERRY PI (HA OS)                          |
|   +----------------------------+  +----------------------------+ |
|   |   MANAGED BY IaC (synced)  |  | NOT IaC (local state only) | |
|   |                            |  |                            | |
|   |   /config/*.yaml           |  |   /config/.storage/        | |
|   |   - configuration.yaml     |  |   - entity_registry        | |
|   |   - automations.yaml       |  |   - device_registry        | |
|   |   - scripts.yaml           |  |   - core.config_entries    | |
|   |   - sensors.yaml           |  |                            | |
|   |   - ui-lovelace.yaml       |  |   Zigbee Coordinator       | |
|   |                            |  |   - Device pairings        | |
|   +----------------------------+  |   - Network key            | |
|                                   |                            | |
|                                   |   SQLite Database          | |
|                                   |   - History                | |
|                                   |   - Statistics             | |
|                                   |                            | |
|                                   |   Add-on Configurations    | |
|                                   |   - Some via UI only       | |
|                                   +----------------------------+ |
+------------------------------------------------------------------+
```

---

## What CAN Be Infrastructure as Code

These components live in git and are automatically deployed:

### 1. YAML Configuration Files

The core Home Assistant configuration:

```yaml
# configuration.yaml - Main configuration
homeassistant:
  name: Home
  unit_system: metric
  currency: EUR
  country: BE
  latitude: !secret ha_latitude
  longitude: !secret ha_longitude
  elevation: !secret ha_elevation

# Include other YAML files
automation: !include automations.yaml
script: !include scripts.yaml
sensor: !include sensors.yaml
```

**What This Includes**:
- Main configuration (`configuration.yaml`)
- Automation rules (`automations.yaml`)
- Scripts (`scripts.yaml`)
- Template sensors (`sensors.yaml`)
- Entity customizations (`customize.yaml`)
- Dashboard layouts (`ui-lovelace.yaml`) - if using YAML mode

### 2. Automation Rules

All automation logic can be defined in YAML:

```yaml
# automations.yaml
automation:
  - alias: "EV Smart Charging"
    description: "Start charging during cheapest hours"
    trigger:
      - platform: numeric_state
        entity_id: sensor.electricity_price_current
        below: 0.10
    condition:
      - condition: state
        entity_id: binary_sensor.tesla_plugged_in
        state: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.tesla_charger
```

### 3. Template Sensors

Custom sensors created from templates:

```yaml
# sensors.yaml
template:
  - sensor:
      - name: "Total Energy Cost"
        unit_of_measurement: "EUR"
        state: >
          {% set consumption = states('sensor.daily_energy') | float %}
          {% set price = states('sensor.electricity_price') | float %}
          {{ (consumption * price) | round(2) }}
```

### 4. Dashboard Configuration (YAML Mode)

If dashboards are configured in YAML mode rather than via UI:

```yaml
# ui-lovelace.yaml
views:
  - title: Energy
    cards:
      - type: gauge
        entity: sensor.electricity_price_current
        name: Current Price
```

**Note**: Dashboard created via UI are stored in `.storage/` and are NOT IaC.

### 5. Zigbee2MQTT Configuration

If using Zigbee2MQTT (recommended over ZHA for IaC):

```yaml
# zigbee2mqtt/configuration.yaml
homeassistant: true
mqtt:
  base_topic: zigbee2mqtt
  server: mqtt://localhost:1883
frontend:
  port: 8080
```

### 6. Python Scripts

Custom scripts for automation and integration:

```
src/scripts/
  config_validator.py     # Validate before deployment
  eevee_sync.py          # EEVEE API integration
  fluvius_cost_calculator.py
```

---

## What CANNOT Be Infrastructure as Code

These components require separate backup and recovery strategies:

### 1. secrets.yaml

Contains API keys, passwords, and sensitive credentials.

```yaml
# secrets.yaml (NEVER in git)
entsoe_api_key: "actual-api-key"
tesla_client_id: "actual-client-id"
```

**Why Not IaC**: Security - credentials should never be in version control.

**Recovery Strategy**: Manual creation from template, or secure backup (e.g., 1Password, Bitwarden).

### 2. Device Pairings (Zigbee, Z-Wave)

Zigbee and Z-Wave devices are "paired" with their coordinator. This pairing:
- Is stored in the coordinator's memory, not in YAML
- Creates a network key that devices use to communicate
- Cannot be exported to a simple configuration file

```
Zigbee Coordinator
  └── Network Key (generated on first pair)
  └── Device 1 (paired, knows network key)
  └── Device 2 (paired, knows network key)
  └── ...
```

**If You Replace the Coordinator**: All devices must be re-paired manually.

**Recovery Strategy**:
- Zigbee2MQTT: Export `coordinator_backup.json` regularly
- ZHA: Use "Download Network Backup" in settings
- Test restore procedure before you need it

### 3. Entity and Device Registry

Home Assistant maintains registries in `/config/.storage/`:

- `core.entity_registry` - Entity IDs, friendly names, areas
- `core.device_registry` - Device information
- `core.config_entries` - Integration configurations

These are created when:
- You add integrations via UI
- You customize entity names/icons
- You assign entities to areas

**Not IaC Because**: These files are binary/JSON, auto-generated, and edited via UI.

### 4. Integration Configurations (UI-Based)

Many integrations are configured entirely via the UI:

```
Settings > Devices & Services > Add Integration > [Tesla Fleet]
  └── OAuth authentication flow
  └── Stored in .storage/core.config_entries
```

**Examples**:
- Tesla Fleet (OAuth flow)
- HomeWizard P1 (auto-discovered)
- HACS integrations

**Recovery Strategy**: Document the setup steps in your repo.

### 5. HACS Integrations

HACS (Home Assistant Community Store) integrations:
- Must be installed via the HACS UI
- Cannot be automated via configuration
- Custom components go in `custom_components/` but installation is manual

**Recovery Strategy**: Maintain a manifest file (`hacs.yaml`) documenting what should be installed:

```yaml
# hacs.yaml (documentation only - not automatically applied)
integrations:
  - name: ENTSO-E Tariff
    repository: JaccoR/hass-entso-e
    purpose: Belgian electricity spot prices

  - name: Fluvius
    repository: myTselworern/Fluvius
    purpose: Smart meter integration
```

### 6. Home Assistant Database

The SQLite database (`home-assistant_v2.db`) contains:
- Historical sensor data
- Statistics (energy dashboards)
- Event logs

**Not IaC Because**: This is runtime state, not configuration.

**Recovery Strategy**: Regular backups (via Home Assistant's built-in backup feature) or accept data loss.

### 7. Add-on Configurations

Some add-ons configure via UI rather than files:
- Settings stored in Supervisor's configuration
- Not accessible as YAML files

**Recovery Strategy**: Document settings, screenshot configurations.

---

## The IaC Gap: An Honest Assessment

### What "Reproducible" Really Means for HAP

When we say HAP enables you to recreate your setup from the repository, here is what that actually means:

| Layer | Reproducible? | Effort Required |
|-------|---------------|-----------------|
| YAML configuration | Yes, automatic | Deploy via GitHub Actions |
| Automations | Yes, automatic | Deploy via GitHub Actions |
| Custom scripts | Yes, automatic | Deploy via GitHub Actions |
| Integrations | Partial | Must re-add via UI |
| Device pairings | No | Must re-pair each device |
| Historical data | No | Lost unless backed up separately |
| HACS integrations | No | Must reinstall via HACS UI |
| Entity customizations | Partial | May need to rename/reconfigure |

### Time to Recovery Estimates

If your SD card fails today and you have:

**Best Case** (all backups available):
- 1-2 hours to flash and initial setup
- 1 hour to deploy configuration and restore backups
- Device pairings already in coordinator
- Total: **2-3 hours**

**Typical Case** (configuration in git, some backups):
- 1-2 hours to flash and initial setup
- 1 hour to deploy configuration
- 2-4 hours to re-configure integrations via UI
- 1-2 hours to re-pair some devices
- Total: **5-9 hours**

**Worst Case** (only git, no backups):
- 1-2 hours to flash and initial setup
- 1 hour to deploy configuration
- 3-4 hours to re-configure all integrations
- 4-8 hours to re-pair all Zigbee devices
- Historical data lost
- Total: **9-15+ hours**

---

## Hybrid Approach: Bridging the Gap

HAP uses a hybrid approach combining IaC with additional strategies:

### 1. Configuration as Code (IaC)

Everything that CAN be YAML goes in git:

```
src/config/
  configuration.yaml
  automations.yaml
  scripts.yaml
  sensors.yaml
  ui-lovelace.yaml  (if YAML mode)
  zigbee2mqtt/configuration.yaml
```

### 2. Manifest Documentation

For things that cannot be automated, maintain documentation:

```yaml
# src/config/hacs.yaml - Documentation manifest
integrations:
  - name: ENTSO-E Tariff
    repository: JaccoR/hass-entso-e
    version: latest
    purpose: Belgian electricity prices
    setup_notes: |
      1. Install via HACS > Integrations
      2. Add API key to secrets.yaml
      3. Configure via Settings > Integrations
```

### 3. Regular Backups

For state that cannot be in git:

```
Backup Strategy:
  - Home Assistant backup: Weekly (via UI or automation)
  - Zigbee2MQTT coordinator backup: Weekly
  - secrets.yaml: Secure password manager
  - Database: Accept potential loss, or include in HA backup
```

### 4. Setup Documentation

Document manual steps required for recovery:

```markdown
## Manual Setup Steps (After Deployment)

1. Install SSH add-on and configure authorized_keys
2. Install HACS: `wget -O - https://get.hacs.xyz | bash -`
3. Install HACS integrations (see hacs.yaml manifest)
4. Configure Tesla integration via OAuth flow
5. Restore Zigbee coordinator backup
```

---

## Comparison with True IaC Tools

### HAP vs. Terraform

| Aspect | Terraform | HAP |
|--------|-----------|-----|
| State Management | Remote state file tracks all resources | No state file - syncs files only |
| Drift Detection | Detects and reports drift | No drift detection |
| Plan Before Apply | `terraform plan` shows changes | No preview mechanism |
| Rollback | State-based rollback possible | Must revert git commit and redeploy |
| Provider Ecosystem | Official providers for most clouds | Home Assistant only |

### HAP vs. Ansible

| Aspect | Ansible | HAP |
|--------|---------|-----|
| Idempotency | Modules ensure idempotent operations | File sync is idempotent, but not all state |
| Inventory | Manages multiple hosts | Single Raspberry Pi |
| Roles | Reusable configuration packages | No equivalent |
| Handlers | React to changes | No equivalent (must restart HA) |

### What HAP Actually Is

HAP is best described as:

> **Git-based Configuration Sync with Automated Deployment**

It is NOT:
- True Infrastructure as Code (lacks state management, drift detection)
- Configuration Management (like Ansible/Puppet)
- Container Orchestration (like Kubernetes)

It IS:
- Version-controlled configuration
- Automated deployment via CI/CD
- A significant improvement over manual UI-based management
- A foundation for reproducibility (with documented manual steps)

---

## Recommendations

### Embrace the Hybrid Model

1. **Put in git**: Everything that can be YAML
2. **Document**: Everything that requires manual steps
3. **Backup**: Everything that is state (coordinator, database)
4. **Test**: Your recovery procedure before you need it

### Choose YAML Mode Where Possible

Some components can be configured either via UI or YAML. Prefer YAML:

| Component | UI Mode | YAML Mode | Recommendation |
|-----------|---------|-----------|----------------|
| Dashboards | Default | `ui-lovelace.yaml` | YAML for IaC |
| Automations | Via UI editor | `automations.yaml` | YAML for IaC |
| Scripts | Via UI editor | `scripts.yaml` | YAML for IaC |
| Scenes | Via UI | Can be YAML | YAML for IaC |

### Use Zigbee2MQTT Over ZHA

For Zigbee devices, Zigbee2MQTT is more IaC-friendly than ZHA:
- Configuration is YAML-based
- Device naming in YAML files
- Easier coordinator backup/restore
- Better for version control

---

## Related Documentation

- [Getting Started](./getting-started.md) - Initial setup guide
- [Pitfalls & Limitations](./pitfalls.md) - Detailed limitations and gotchas
- [Disaster Recovery](./recovery.md) - Recovery procedures
- [Main PRD](/prd/README.md) - Project vision and goals
