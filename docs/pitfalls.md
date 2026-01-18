# Pitfalls & Limitations

> An honest guide to what can go wrong with HAP and the inherent limitations of treating Home Assistant as Infrastructure as Code.

## Overview

This document catalogs the known pitfalls, limitations, and "gotchas" you will encounter when using HAP. Understanding these upfront will save you frustration and help you plan appropriate workarounds.

---

## Bootstrap Problems

### The Secrets Bootstrap Problem

**Problem**: `secrets.yaml` must exist before any deployment works, but `secrets.yaml` cannot be in git.

**Scenario**:
1. You flash a fresh SD card
2. You try to deploy configuration via GitHub Actions
3. Deployment fails because `secrets.yaml` does not exist
4. Home Assistant cannot start because configuration references missing secrets

**Symptoms**:
```
ERROR (MainThread) [homeassistant.config] Unable to read secrets.yaml: ...
```

**Solution**:
Before first deployment, you must manually SSH into the Pi and create `secrets.yaml`:

```bash
ssh root@<PI_IP>
cd /config
nano secrets.yaml  # Create from your secrets.yaml.example
```

**Prevention**:
- Keep a copy of `secrets.yaml` in a secure password manager
- Create a `secrets.yaml.example` template with all required keys (no values)
- Document required secrets in your README

### The SSH Add-on Bootstrap Problem

**Problem**: GitHub Actions needs SSH access to deploy, but the SSH add-on must be installed via UI first.

**Scenario**:
1. Fresh Pi installation
2. No SSH access yet
3. Cannot deploy configuration
4. Must manually install SSH add-on via Home Assistant UI

**Solution**:
Accept that initial setup always requires manual UI access. Document the steps:

1. Access Home Assistant UI at `http://<PI_IP>:8123`
2. Complete onboarding
3. Install Terminal & SSH add-on
4. Configure authorized_keys
5. Start add-on and enable "Start on boot"

---

## State vs. Configuration

### Device Pairings Are STATE, Not Configuration

**Problem**: Zigbee/Z-Wave device pairings exist in coordinator memory, not YAML files.

**Why This Matters**:
- Device pairings cannot be recreated from git
- Replacing a coordinator means re-pairing every device
- Some devices require physical access to re-pair (press button, etc.)

**What You Lose**:
- All device associations if coordinator dies
- Network key (devices will not respond to new coordinator)
- Device-specific settings stored in coordinator

**Mitigation**:
```yaml
# Backup coordinator regularly
# Zigbee2MQTT: /app/data/coordinator_backup.json
# ZHA: Settings > Integrations > ZHA > Configure > Download backup
```

### Entity Registry Is STATE

**Problem**: Entity customizations (names, icons, areas) are stored in `.storage/`, not YAML.

**Scenario**:
You rename `sensor.entsoe_prices` to `sensor.electricity_spot_price` via the UI. This rename:
- Is stored in `.storage/core.entity_registry`
- Is NOT in your git repository
- Will be lost on fresh install

**Symptoms After Recovery**:
- Automations reference old entity names
- Dashboard cards show "Entity not available"
- Must manually re-customize all entities

**Mitigation Options**:

1. **Use customize.yaml** (partial solution):
```yaml
# customize.yaml - Only handles some attributes
sensor.entsoe_prices:
  friendly_name: "Electricity Spot Price"
  icon: mdi:flash
```

2. **Avoid entity renaming** - Use friendly_name instead of changing entity_id

3. **Backup .storage/ directory** - Include in your backup strategy

### History and Statistics Are STATE

**Problem**: All historical data lives in the SQLite database.

**What You Lose**:
- Energy dashboard historical data
- Sensor history graphs
- Statistics and long-term data
- Logbook entries

**This Cannot Be Prevented By IaC**: Historical data is runtime state by definition.

**Mitigation**:
- Use Home Assistant's built-in backup feature
- Accept that historical data may be lost
- For critical data, export to external database (InfluxDB)

---

## HACS Limitations

### HACS Cannot Be Automated

**Problem**: HACS integrations must be installed via the HACS UI. There is no file-based installation.

**What This Means**:
- You cannot declare HACS integrations in YAML
- After fresh install, you must manually reinstall each integration
- Custom cards (frontend) must also be reinstalled manually

**Recovery Workflow**:
1. Install HACS (manual wget command)
2. Open HACS UI
3. Search for each integration
4. Click Install on each one
5. Restart Home Assistant
6. Repeat for all custom cards

**Mitigation**:
Maintain a manifest file (`hacs.yaml`) documenting all HACS dependencies:

```yaml
# src/config/hacs.yaml - Documentation only, not auto-applied
integrations:
  - name: ENTSO-E Tariff
    repository: JaccoR/hass-entso-e
    version: latest
    purpose: Belgian electricity spot prices

  - name: Fluvius
    repository: myTselworern/Fluvius
    version: latest
    purpose: Smart meter integration

frontend:
  - name: ApexCharts Card
    repository: RomRider/apexcharts-card
    purpose: Price charts on dashboard

  - name: Button Card
    repository: custom-cards/button-card
    purpose: Custom button styling
```

### HACS Updates Can Break Things

**Problem**: HACS integrations are community-maintained and can break with Home Assistant updates.

**Scenario**:
1. Home Assistant releases 2024.6.0
2. HACS integration has not been updated
3. Integration breaks, automations fail
4. Must wait for community fix or roll back HA

**Mitigation**:
- Wait a week before updating Home Assistant
- Check HACS integration GitHub issues before updating
- Have a rollback plan (backup before updates)

---

## Add-on Configuration

### Some Add-ons Only Configure Via UI

**Problem**: Not all add-on settings can be managed via files.

**Examples**:
- Some add-ons store config in Supervisor's internal database
- SSH add-on authorized_keys is YAML, but other settings may be UI-only
- Add-on-specific data directories may not be in expected locations

**Mitigation**:
- Document add-on settings in your repository
- Screenshot complex configurations
- Include add-on setup in recovery documentation

### Add-on Data Is Separate From /config

**Problem**: Add-on data lives in `/addon_configs/` or add-on-specific paths, not `/config`.

**What This Means**:
- Deploying to `/config` does not touch add-on data
- Zigbee2MQTT data is in `/addon_configs/zigbee2mqtt/`
- Must backup add-on directories separately

---

## Breaking Changes

### Home Assistant Updates Can Break Automations

**Problem**: Home Assistant frequently deprecates or changes features.

**Historical Examples**:
- YAML configuration for integrations deprecated in favor of UI
- Template syntax changes
- Service call format changes (`service_data` to `data`)
- Entity naming convention changes

**Symptoms**:
```
WARNING (MainThread) [homeassistant.components.automation]
Automation 'EV Smart Charging' is using deprecated feature...
```

**Mitigation**:
- Read release notes before updating
- Test updates in local Docker environment first
- Keep a backup before every update
- Subscribe to Home Assistant blog/announcements

### Integration Breaking Changes

**Problem**: Integrations (official and HACS) can change their entity structure.

**Scenario**:
1. ENTSO-E integration updates
2. `sensor.entsoe_prices` becomes `sensor.entsoe_be_day_ahead`
3. All your automations and templates break
4. No warning before this happens

**Mitigation**:
- Pin HACS integration versions where possible
- Test updates in local environment
- Use template sensors as abstraction layers:

```yaml
# Abstraction layer - change only here if integration changes
template:
  - sensor:
      - name: "Electricity Price"
        state: "{{ states('sensor.entsoe_prices') }}"  # Single point of change
```

---

## Rollback Complexity

### No True Atomic Rollback

**Problem**: HAP does not have Terraform-style state management. Rolling back is not atomic.

**What "Rollback" Actually Means in HAP**:
1. Revert git commit
2. Push to trigger redeploy
3. Wait for deployment
4. Restart Home Assistant
5. Hope nothing else broke in the meantime

**Partial Failure Scenarios**:
- Files synced but HA fails to restart
- Some automations work, others fail validation
- Integration state corrupted

**Mitigation**:
- Always validate configuration before deployment
- Use Home Assistant's built-in backup before changes
- Have SSH access ready for manual intervention

### Configuration Validation Is Imperfect

**Problem**: `hass --script check_config` does not catch all errors.

**What Validation Catches**:
- YAML syntax errors
- Missing required fields
- Unknown configuration keys

**What Validation Misses**:
- Runtime errors (entity does not exist)
- Logic errors in templates
- Integration-specific issues
- Service call target validation

**Scenario**:
```yaml
automation:
  - alias: "Broken Automation"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.nonexistent_entity  # Validation passes, runtime fails
```

---

## Testing Limitations

### Mock Sensors Cannot Replicate Real Behavior

**Problem**: Local Docker testing uses mock sensors that behave differently from real devices.

**What You Cannot Test Locally**:
- Actual device response times
- Device unavailability handling
- Cloud API rate limits and failures
- Real-time data variations
- Physical device quirks

**Scenario**:
Your automation works perfectly with `input_number.mock_electricity_price`, but fails in production because the real `sensor.entsoe_prices` occasionally returns `unknown` or `unavailable`.

**Mitigation**:
Always handle edge cases in templates:

```yaml
template:
  - sensor:
      - name: "Safe Electricity Price"
        state: >
          {% set price = states('sensor.entsoe_prices') %}
          {% if price in ['unknown', 'unavailable'] %}
            0.30  {# Fallback to safe default #}
          {% else %}
            {{ price | float(0.30) }}
          {% endif %}
```

### No Integration Testing Framework

**Problem**: There is no built-in way to test automations and integrations end-to-end.

**What This Means**:
- You cannot automatically verify an automation triggers correctly
- No unit tests for templates
- Must test manually or in production

**Mitigation**:
- Use `input_boolean` helpers to manually test automations
- Create test dashboards with manual trigger buttons
- Log extensively during development

---

## Network Dependencies

### Cloud API Availability

**Problem**: Many integrations depend on cloud APIs that can be unavailable.

**Affected Features**:
- Tesla Fleet API (car control)
- ENTSO-E API (electricity prices)
- EEVEE Mobility (if API exists)
- Weather services

**Failure Modes**:
- API rate limited
- API temporarily down
- API permanently deprecated
- OAuth tokens expired

**Mitigation**:
```yaml
# Always have fallback values
template:
  - sensor:
      - name: "Electricity Price Safe"
        state: >
          {% set price = states('sensor.entsoe_prices') %}
          {% if price in ['unknown', 'unavailable', 'None'] %}
            0.25  {# Use average price as fallback #}
          {% else %}
            {{ price }}
          {% endif %}
```

### Zigbee Coordinator Connection

**Problem**: USB Zigbee coordinators can disconnect or fail.

**Symptoms**:
- All Zigbee devices become unavailable
- Zigbee2MQTT add-on crashes
- USB device disappears from `/dev/`

**Common Causes**:
- USB power issues (use powered hub)
- Radio interference
- Coordinator hardware failure
- USB port failure

**Mitigation**:
- Use a quality USB extension cable (reduces interference)
- Monitor coordinator status in automations
- Have a spare coordinator for emergencies

### MQTT Broker Dependency

**Problem**: If using MQTT (Zigbee2MQTT, etc.), the broker is a single point of failure.

**If MQTT Broker Fails**:
- Zigbee devices stop responding
- Any MQTT-based sensors fail
- Automations using MQTT entities break

**Mitigation**:
- Use the Mosquitto add-on with watchdog enabled
- Monitor broker status
- Consider MQTT broker redundancy for critical installations

---

## Dashboard and UI Pitfalls

### YAML vs UI Dashboard Mode

**Problem**: Dashboards can be YAML mode (IaC) or UI mode (not IaC), and switching is complex.

**UI Mode** (Default):
- Edited via Lovelace UI
- Stored in `.storage/lovelace`
- NOT version controlled
- Easy to use

**YAML Mode**:
- Defined in `ui-lovelace.yaml`
- Version controlled
- Requires restart to apply changes
- Cannot be edited via UI

**Gotcha**: You cannot easily convert between modes.

**Recommendation**: Choose YAML mode from the start if IaC is important:

```yaml
# configuration.yaml
lovelace:
  mode: yaml
```

### Resource Management

**Problem**: Custom cards (Lovelace resources) must be registered separately.

**Even With YAML Dashboards**:
```yaml
# ui-lovelace.yaml
resources:
  - url: /hacsfiles/apexcharts-card/apexcharts-card.js
    type: module
```

This requires:
1. HACS to be installed
2. The card to be installed via HACS
3. The path to be correct

**If HACS Not Installed**: Custom cards fail silently.

---

## Security Pitfalls

### Secrets in Git History

**Problem**: If you accidentally commit secrets, they remain in git history forever.

**Even If You Delete The File**: The secret exists in previous commits.

**Recovery**:
- Rotate all exposed credentials immediately
- Use `git filter-branch` or BFG Repo-Cleaner (complex)
- Consider creating a new repository

**Prevention**:
- Add `secrets.yaml` to `.gitignore` from day one
- Use pre-commit hooks to check for secrets
- Never copy-paste real credentials into example files

### SSH Key Security

**Problem**: The SSH private key in GitHub Secrets has root access to your Pi.

**If Compromised**:
- Attacker has full root access to your home network
- Can access any device Home Assistant controls
- Can read your secrets.yaml

**Mitigation**:
- Use a dedicated SSH key for HAP (not your personal key)
- Rotate the key periodically
- Monitor for unauthorized access
- Consider IP allowlisting if your network has static IP

---

## Performance Pitfalls

### Large Configuration Files

**Problem**: Very large YAML files can slow down Home Assistant startup.

**Symptoms**:
- Slow startup times
- High CPU during config reload
- Memory pressure on Pi

**Mitigation**:
- Split configuration into multiple files using `!include`
- Use packages for logical grouping
- Avoid excessive template sensors

### Template Evaluation

**Problem**: Complex templates are evaluated frequently and can impact performance.

**Example of Expensive Template**:
```yaml
# Bad: Evaluated every state change of every entity
template:
  - sensor:
      - name: "Expensive Sensor"
        state: >
          {% for entity in states %}
            {{ entity.state }}
          {% endfor %}
```

**Mitigation**:
- Use `availability` to limit when templates run
- Specify explicit entities in template listeners
- Profile with Home Assistant's built-in tools

---

## Summary: What To Expect

### Things That WILL Go Wrong (Eventually)

1. SD card will fail (use SSD instead)
2. Home Assistant update will break something
3. HACS integration will become incompatible
4. You will forget to backup secrets.yaml
5. A Zigbee device will refuse to pair
6. Cloud API will be down when you need it

### Things You CANNOT Prevent With IaC

1. Hardware failures
2. Device pairing loss
3. Historical data loss (without backups)
4. UI-configured integration loss
5. HACS reinstallation requirement

### Your Defense Strategy

1. **Backup regularly**: Use Home Assistant's built-in backup
2. **Document everything**: Keep setup steps in your repo
3. **Test locally**: Validate before deploying
4. **Monitor actively**: Know when things break
5. **Accept limitations**: HAP helps but is not magic

---

## Related Documentation

- [Getting Started](./getting-started.md) - Initial setup guide
- [Architecture & IaC Analysis](./architecture.md) - What is and is not IaC
- [Disaster Recovery](./recovery.md) - How to recover from failures
