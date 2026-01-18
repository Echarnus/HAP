# Disaster Recovery Guide

> Step-by-step procedures for recovering from common failure scenarios, with honest assessments of what can and cannot be recovered.

## Overview

This guide covers recovery procedures for common disaster scenarios. Each section includes:
- Scenario description
- What is recoverable
- What is lost
- Step-by-step recovery procedure
- Time and complexity estimates

---

## Quick Reference: Recovery Matrix

| Scenario | Time Estimate | Complexity | Data Loss |
|----------|---------------|------------|-----------|
| SD Card Failure (full backups) | 2-3 hours | Medium | Minimal |
| SD Card Failure (git only) | 5-15 hours | High | Significant |
| Bad Config Deployment | 15-60 min | Low | None |
| Zigbee Coordinator Replacement | 1-8 hours | Medium-High | Pairings (maybe) |
| Corrupted Database | 30-60 min | Low | History |
| Home Assistant Update Failure | 30-60 min | Low | None |

---

## Scenario 1: SD Card / Storage Failure (Complete Loss)

### Description

The SD card or SSD has failed completely. The Pi will not boot, or the storage is corrupted beyond repair.

### What Is Recoverable

| Component | Source | Recovery Method |
|-----------|--------|-----------------|
| YAML configuration | Git repository | Automatic deployment |
| Automations | Git repository | Automatic deployment |
| Custom scripts | Git repository | Automatic deployment |
| Secrets | Password manager / backup | Manual creation |
| Zigbee pairings | Coordinator memory | Usually survives (if coordinator OK) |
| Zigbee2MQTT config | Git repository | Automatic deployment |

### What Is Lost

| Component | Impact | Mitigation |
|-----------|--------|------------|
| Home Assistant database | All history, statistics, energy data | Pre-failure backup only |
| Entity registry | Custom names, icons, areas | Reconfigure manually |
| UI-configured integrations | Tesla, HomeWizard, etc. | Reconfigure via UI |
| HACS integrations | Must reinstall | Follow hacs.yaml manifest |
| Lovelace (if UI mode) | Dashboard layouts | Pre-failure backup only |

### Recovery Procedure

**Total Time**: 2-3 hours (with backups) / 5-15 hours (git only)

#### Phase 1: Hardware Preparation (30 minutes)

1. **Obtain new storage**
   - Recommended: USB SSD with adapter
   - Fallback: High-endurance SD card

2. **Download Home Assistant OS**
   ```bash
   # Download appropriate image
   # Pi 4: haos_rpi4-64-*.img.xz
   # Pi 5: haos_rpi5-64-*.img.xz
   ```

3. **Flash the image**
   - Use Raspberry Pi Imager
   - Select "Use custom" and choose the downloaded image
   - Flash to new storage device

4. **Boot the Pi**
   - Connect new storage
   - Connect Ethernet (recommended)
   - Power on
   - Wait 10-20 minutes for initial setup

#### Phase 2: Initial Configuration (30-60 minutes)

5. **Access Home Assistant**
   ```
   http://<PI_IP>:8123
   ```
   Complete onboarding wizard (create admin account, set location)

6. **Install SSH Add-on**
   - Go to Settings > Add-ons > Add-on Store
   - Install "Terminal & SSH"
   - Configure authorized_keys:
     ```yaml
     authorized_keys:
       - ssh-rsa AAAA...your-key...
     ```
   - Start the add-on
   - Enable "Start on boot"

7. **Create secrets.yaml**
   ```bash
   ssh root@<PI_IP>
   cd /config
   nano secrets.yaml
   ```
   Paste your secrets from your secure backup.

#### Phase 3: Deploy Configuration (15-30 minutes)

8. **Trigger GitHub Actions deployment**
   ```bash
   # On your development machine
   cd HAP
   git commit --allow-empty -m "Trigger recovery deployment"
   git push
   ```

9. **Verify deployment**
   - Check GitHub Actions for success
   - SSH to Pi and verify files exist:
     ```bash
     ssh root@<PI_IP>
     ls -la /config/
     ```

10. **Restart Home Assistant**
    - Settings > System > Restart
    - Wait for restart to complete

#### Phase 4: Restore Integrations (1-4 hours)

11. **Install HACS**
    ```bash
    ssh root@<PI_IP>
    wget -O - https://get.hacs.xyz | bash -
    ```
    - Restart Home Assistant
    - Add HACS integration via Settings > Devices & Services

12. **Install HACS integrations** (from hacs.yaml manifest)
    - HACS > Integrations > search for each
    - Install each integration
    - Restart after installing

13. **Reconfigure UI-based integrations**
    - Tesla Fleet: Settings > Integrations > Add > Tesla Fleet (OAuth flow)
    - HomeWizard: Usually auto-discovered
    - Other integrations: Add via UI

#### Phase 5: Restore Zigbee Devices (0-4 hours)

14. **If Zigbee coordinator is the same**
    - Devices should reconnect automatically
    - Wait 30 minutes for mesh to stabilize
    - Check Zigbee2MQTT for device status

15. **If devices do not reconnect**
    - Power cycle individual devices
    - May need to re-pair some devices (see Scenario 3)

#### Phase 6: Verification (30 minutes)

16. **Verify core functionality**
    - [ ] Home Assistant accessible at :8123
    - [ ] SSH access working
    - [ ] Automations listed in Settings > Automations
    - [ ] Zigbee devices responding
    - [ ] Integrations showing connected

17. **Verify specific features**
    - [ ] Electricity prices updating
    - [ ] Tesla integration connected
    - [ ] Energy dashboard configured
    - [ ] Dashboards rendering correctly

---

## Scenario 2: Bad Configuration Deployment

### Description

A configuration change was deployed that prevents Home Assistant from starting, or causes significant malfunction.

### Symptoms

- Home Assistant does not start after deployment
- Web interface inaccessible
- Error messages in logs about invalid configuration
- Automations not running

### Recovery Procedure

**Total Time**: 15-60 minutes
**Complexity**: Low

#### Option A: Revert via Git (Preferred)

1. **Identify the breaking commit**
   ```bash
   git log --oneline -10
   ```

2. **Revert the commit**
   ```bash
   git revert HEAD  # Revert last commit
   # Or for specific commit:
   git revert <commit-hash>
   ```

3. **Push the revert**
   ```bash
   git push origin main
   ```

4. **Wait for deployment** and verify HA starts

#### Option B: Manual Fix via SSH

If you cannot wait for deployment or need to debug:

1. **SSH into the Pi**
   ```bash
   ssh root@<PI_IP>
   ```

2. **Check Home Assistant logs**
   ```bash
   ha core logs
   ```

3. **Identify the problematic file** from error messages

4. **Edit the file directly**
   ```bash
   nano /config/automations.yaml  # or problematic file
   ```

5. **Validate configuration**
   ```bash
   ha core check
   ```

6. **Restart Home Assistant**
   ```bash
   ha core restart
   ```

7. **Sync fix back to git**
   - Copy corrected file to your local repo
   - Commit and push the fix

#### Option C: Restore from Backup

If the configuration is too broken to debug:

1. **Access Home Assistant** (may need to use `ha` CLI via SSH if UI down)
   ```bash
   ssh root@<PI_IP>
   ha backups list
   ```

2. **Restore most recent backup**
   ```bash
   ha backups restore <backup_slug>
   ```

3. **Wait for restore** to complete

4. **Sync restored config back to git** (important!)

### Prevention

- Always run validation before pushing:
  ```bash
  python src/scripts/config_validator.py
  ```
- Test in local Docker environment first
- Make small, incremental changes
- Create backup before major changes

---

## Scenario 3: Zigbee Coordinator Replacement

### Description

The Zigbee coordinator has failed and needs to be replaced, or you are upgrading to a different coordinator.

### The Hard Truth

When you replace a Zigbee coordinator:
- **The new coordinator has a different network key**
- **All devices were paired to the OLD network key**
- **Devices will NOT automatically connect to the new coordinator**

### What Is Recoverable

| Situation | Recovery |
|-----------|----------|
| Same coordinator model + backup | Restore backup, devices reconnect |
| Different coordinator + backup | May work if coordinator supports import |
| No backup | Must re-pair ALL devices manually |

### Recovery Procedure

**Total Time**: 1-8 hours depending on backup availability and device count
**Complexity**: Medium to High

#### If You Have a Coordinator Backup

1. **Install new coordinator** (same model preferred)
   - Physically connect to Pi via USB
   - Note the device path: usually `/dev/ttyUSB0` or `/dev/ttyACM0`

2. **Stop Zigbee2MQTT**
   ```bash
   ha addons stop core_zigbee2mqtt  # or your addon slug
   ```

3. **Restore coordinator backup**
   - For Zigbee2MQTT: Copy `coordinator_backup.json` to `/addon_configs/zigbee2mqtt/`
   - For ZHA: Use "Upload backup" in ZHA integration settings

4. **Start Zigbee2MQTT**
   ```bash
   ha addons start core_zigbee2mqtt
   ```

5. **Wait for devices to reconnect** (can take 30-60 minutes)
   - Mains-powered devices reconnect first
   - Battery devices reconnect on next wake

6. **Power cycle stubborn devices**
   - Remove power / battery for 30 seconds
   - Restore power
   - Device should reconnect

#### If You Do NOT Have a Backup

This is the painful path. You must re-pair every device.

1. **Install new coordinator**
   - Connect to Pi
   - Configure in Zigbee2MQTT settings

2. **Start Zigbee2MQTT** with fresh configuration

3. **Re-pair each device** (one at a time)

   For each device:
   - Enable pairing mode in Zigbee2MQTT (Permit Join)
   - Put device in pairing mode (varies by device):
     - Switches/plugs: Often hold button 5+ seconds
     - Sensors: May have small reset button
     - Check device manual
   - Wait for device to appear in Zigbee2MQTT
   - Rename device to match your configuration

4. **Update entity IDs if changed**
   - If device gets new entity ID, update automations
   - Consider using entity registry to restore old IDs

5. **Rebuild Zigbee mesh**
   - Allow 24-48 hours for mesh to stabilize
   - Router devices (mains-powered) strengthen mesh

### Time Estimates by Device Count

| Devices | With Backup | Without Backup |
|---------|-------------|----------------|
| 1-5 | 30 min | 1-2 hours |
| 5-15 | 30-60 min | 2-4 hours |
| 15-30 | 1-2 hours | 4-6 hours |
| 30+ | 2+ hours | 6-8+ hours |

### Prevention

**Create regular coordinator backups**:

For Zigbee2MQTT:
```bash
# Backup is automatically created in /addon_configs/zigbee2mqtt/
# Copy coordinator_backup.json to secure location
```

For ZHA:
- Settings > Integrations > ZHA > Configure > Download Network Backup

Automate backups with a script or calendar reminder (weekly recommended).

---

## Scenario 4: What Data Is Lost and What Is Recoverable

### Complete Recovery Matrix

#### Fully Recoverable (from git)

| Item | Location | Recovery |
|------|----------|----------|
| configuration.yaml | src/config/ | Auto-deployed |
| automations.yaml | src/config/ | Auto-deployed |
| scripts.yaml | src/config/ | Auto-deployed |
| sensors.yaml | src/config/ | Auto-deployed |
| ui-lovelace.yaml | src/config/ | Auto-deployed |
| zigbee2mqtt/configuration.yaml | src/config/zigbee2mqtt/ | Auto-deployed |
| Python scripts | src/scripts/ | Auto-deployed |

#### Recoverable with Manual Steps

| Item | Backup Location | Recovery Steps |
|------|-----------------|----------------|
| secrets.yaml | Password manager | Create manually from template |
| HACS integrations | hacs.yaml manifest | Install via HACS UI |
| UI integrations | Documentation | Reconfigure via UI |
| Coordinator backup | External backup | Restore to new coordinator |

#### Partially Recoverable (from backups only)

| Item | Backup Source | Notes |
|------|---------------|-------|
| Entity registry | HA backup (.storage/) | Entity names, areas, icons |
| Device registry | HA backup (.storage/) | Device configurations |
| UI dashboards | HA backup (.storage/lovelace) | If using UI mode |
| Home Assistant database | HA backup | History, statistics |

#### NOT Recoverable

| Item | Reason | Mitigation |
|------|--------|------------|
| History without backup | Runtime state | Accept loss or restore backup |
| Coordinator pairings without backup | Hardware state | Re-pair devices |
| OAuth tokens | Security tokens | Re-authenticate |
| Cloud service states | External | Automatic resync usually |

### Data Loss Severity Matrix

| Failure Type | Config Loss | History Loss | Pairing Loss | Effort |
|--------------|-------------|--------------|--------------|--------|
| SD card (with backups) | None | None | None | Low |
| SD card (git only) | None | Total | None | Medium |
| Coordinator (with backup) | None | None | None | Low |
| Coordinator (no backup) | None | None | Total | High |
| Corrupt database | None | Total | None | Low |
| HA update failure | None | None | None | Low |

---

## Recovery Checklists

### Pre-Disaster Preparation Checklist

Complete these BEFORE disaster strikes:

- [ ] secrets.yaml backed up to password manager
- [ ] Coordinator backup exported (weekly)
- [ ] Home Assistant backup created (weekly)
- [ ] GitHub Actions tested and working
- [ ] SSH access verified
- [ ] hacs.yaml manifest up to date
- [ ] Integration setup steps documented
- [ ] Recovery procedure tested (at least once)

### Post-Recovery Verification Checklist

After any recovery, verify:

#### Core Functionality
- [ ] Web interface accessible at :8123
- [ ] SSH access working
- [ ] All users can log in
- [ ] Mobile app connects

#### Configuration
- [ ] Automations listed and enabled
- [ ] Scripts available
- [ ] Scenes defined
- [ ] Helpers exist

#### Integrations
- [ ] Electricity prices updating
- [ ] Tesla integration connected (if applicable)
- [ ] Fluvius/P1 meter reading (if applicable)
- [ ] Weather data available

#### Devices
- [ ] Zigbee devices responding
- [ ] Z-Wave devices responding (if applicable)
- [ ] WiFi devices discovered

#### Dashboards
- [ ] Main dashboard renders
- [ ] Energy dashboard shows data
- [ ] All cards displaying correctly
- [ ] Custom cards loaded (if HACS)

#### Automations (Test Each)
- [ ] EV charging automation
- [ ] Roller shutter controls
- [ ] Alert notifications
- [ ] Scheduled automations

---

## Emergency Contacts and Resources

### Immediate Help

| Resource | URL/Command |
|----------|-------------|
| Home Assistant CLI | `ha core logs` (via SSH) |
| Home Assistant Logs | Settings > System > Logs |
| Zigbee2MQTT Logs | Zigbee2MQTT Add-on > Log tab |

### Community Support

| Resource | URL |
|----------|-----|
| Home Assistant Community | [community.home-assistant.io](https://community.home-assistant.io) |
| Home Assistant Discord | [discord.gg/home-assistant](https://discord.gg/home-assistant) |
| Zigbee2MQTT GitHub Issues | [github.com/Koenkk/zigbee2mqtt/issues](https://github.com/Koenkk/zigbee2mqtt/issues) |

### Documentation

| Resource | URL |
|----------|-----|
| Home Assistant Docs | [home-assistant.io/docs](https://www.home-assistant.io/docs) |
| Zigbee2MQTT Docs | [zigbee2mqtt.io](https://www.zigbee2mqtt.io) |
| HAP Repository | Your GitHub repo |

---

## Related Documentation

- [Getting Started](./getting-started.md) - Initial setup guide
- [Architecture & IaC Analysis](./architecture.md) - What is and is not IaC
- [Pitfalls & Limitations](./pitfalls.md) - Known issues and limitations
