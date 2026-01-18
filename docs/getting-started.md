# Getting Started with HAP

> A complete guide to setting up HAP (Home Assistant Pi) from scratch, including hardware requirements, software prerequisites, and first deployment.

## Overview

HAP is an Infrastructure-as-Code approach for managing Home Assistant on Raspberry Pi. This guide will walk you through setting up both the Raspberry Pi running Home Assistant OS and your local development environment.

**Time Estimate**: 2-4 hours for complete setup

---

## Hardware Requirements

### Essential Hardware

| Component | Recommendation | Purpose |
|-----------|----------------|---------|
| **Raspberry Pi** | Pi 4 Model B (4GB+ RAM) | Primary Home Assistant host |
| **Storage** | 32GB+ SSD via USB adapter | Boot drive (preferred over SD card) |
| **Power Supply** | Official Pi 4 USB-C (5.1V/3A) | Stable power delivery |
| **Network** | Ethernet cable or WiFi | Network connectivity |
| **Case** | Passive cooling case recommended | Heat management |

**Why SSD over SD Card?**

SD cards have limited write cycles and frequently fail under Home Assistant's continuous database writes. A USB-attached SSD provides:
- 10x longer lifespan
- Faster read/write speeds
- More reliable operation

**Budget Alternative**: Use a high-endurance SD card (e.g., Samsung PRO Endurance) if SSD is not feasible, but expect to replace it every 1-2 years.

### Feature-Specific Hardware

Depending on which HAP features you plan to use, you may need additional hardware:

#### For Fluvius Energy Metering

| Component | Options | Estimated Cost |
|-----------|---------|----------------|
| **P1 Reader** | HomeWizard P1 Meter, SlimmeLezer+ | EUR 25-35 |

The P1 reader connects to your Fluvius digital meter's P1 port (RJ12 connector) and provides real-time energy consumption data via WiFi.

#### For Zigbee Devices (Zaffer Roller Shutters)

| Component | Options | Estimated Cost |
|-----------|---------|----------------|
| **Zigbee Coordinator** | Sonoff Zigbee 3.0 USB, ConBee II, SLZB-06 | EUR 20-50 |

The Zigbee coordinator acts as the central hub for all Zigbee devices. Choose based on:
- **Sonoff Zigbee 3.0 USB**: Budget-friendly, well-supported
- **SLZB-06**: Ethernet-connected, more reliable for large networks
- **ConBee II**: Popular choice, good compatibility

**Important**: The coordinator stores device pairings in its memory. This is NOT configuration-as-code and requires separate backup strategies.

### Network Diagram

```
                                    Internet
                                       |
                                   [Router]
                                       |
            +---------+---------+------+-------+
            |         |         |              |
        [Pi + HA]  [P1 Reader] [Zigbee      [Your
         :8123     (WiFi)     Coordinator]   Devices]
            |                      |
            +------[USB]-----------+
```

---

## Software Prerequisites

### On Your Development Machine

Install the following before proceeding:

| Software | Version | Purpose | Installation |
|----------|---------|---------|--------------|
| **Git** | 2.x+ | Version control | [git-scm.com](https://git-scm.com) |
| **Docker Desktop** | Latest | Local HA testing | [docker.com](https://docker.com/products/docker-desktop) |
| **Python** | 3.9+ | Config validation scripts | [python.org](https://python.org) |
| **SSH Client** | Built-in | Pi access | Included in macOS/Linux |
| **VS Code** (optional) | Latest | YAML editing | [code.visualstudio.com](https://code.visualstudio.com) |

**Verify Installation**:

```bash
git --version      # Should show 2.x+
docker --version   # Should show 20.x+ or newer
python3 --version  # Should show 3.9+
ssh -V             # Should show OpenSSH version
```

### VS Code Extensions (Recommended)

If using VS Code, install these extensions for better YAML editing:

- **YAML** by Red Hat
- **Home Assistant Config Helper**
- **Docker** by Microsoft

---

## Initial Raspberry Pi Setup

### Step 1: Download Home Assistant OS

1. Go to [home-assistant.io/installation/raspberrypi](https://www.home-assistant.io/installation/raspberrypi)
2. Download the image for your Pi model:
   - Raspberry Pi 4: `haos_rpi4-64-*.img.xz`
   - Raspberry Pi 5: `haos_rpi5-64-*.img.xz`

### Step 2: Flash the Image

**Using Raspberry Pi Imager (Recommended)**:

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert your SSD/SD card
3. Open Imager:
   - **Choose OS**: "Use custom" and select the downloaded `.img.xz` file
   - **Choose Storage**: Select your SSD/SD card
4. Click **Write** (this will erase the drive)
5. Wait for write and verification to complete (~5-10 minutes)

**Alternative - Using Command Line**:

```bash
# macOS
diskutil list                          # Find your disk (e.g., /dev/disk2)
diskutil unmountDisk /dev/disk2
xzcat haos_rpi4-64-*.img.xz | sudo dd of=/dev/rdisk2 bs=4M
```

### Step 3: Network Configuration (Optional)

If using WiFi instead of Ethernet, you need to pre-configure network settings:

1. After flashing, the drive has a partition called `hassos-boot`
2. Create a USB drive with a folder named `CONFIG/network/`
3. Create file `my-network` inside with content:

```ini
[connection]
id=my-network
type=wifi

[wifi]
mode=infrastructure
ssid=YOUR_WIFI_SSID

[wifi-security]
auth-alg=open
key-mgmt=wpa-psk
psk=YOUR_WIFI_PASSWORD

[ipv4]
method=auto

[ipv6]
method=auto
```

4. Insert this USB drive into the Pi on first boot

**Recommendation**: Use Ethernet for initial setup, then configure WiFi via the UI if needed.

### Step 4: First Boot

1. Connect the SSD/SD card to the Pi
2. Connect Ethernet cable (recommended)
3. Connect power supply
4. Wait 10-20 minutes for initial setup

The Pi will:
- Resize the filesystem
- Download and install Home Assistant
- Prepare the system

### Step 5: Access Home Assistant

1. Find your Pi's IP address:
   - Check your router's DHCP leases
   - Or use: `ping homeassistant.local` (if mDNS works on your network)

2. Open a browser to: `http://<PI_IP>:8123`

3. Complete the onboarding wizard:
   - Create your admin account
   - Set location (for sunrise/sunset automations)
   - Configure basic settings

**Important**: Note down the credentials you create - you will need them later.

---

## Install Required Add-ons

Before HAP can deploy configurations, you need to install and configure several add-ons.

### SSH Add-on (Required)

The SSH add-on enables GitHub Actions to deploy configurations to your Pi.

1. Go to **Settings** > **Add-ons** > **Add-on Store**
2. Search for "Terminal & SSH"
3. Click **Install**
4. After installation, go to the **Configuration** tab
5. Add your SSH public key:

```yaml
authorized_keys:
  - ssh-rsa AAAA...your-public-key... user@machine
```

6. Start the add-on
7. Enable "Start on boot" and "Watchdog"

**Generate an SSH Key** (if you do not have one):

```bash
# On your development machine
ssh-keygen -t ed25519 -C "hap-deployment"

# View the public key to copy
cat ~/.ssh/id_ed25519.pub
```

**Test SSH Connection**:

```bash
ssh root@<PI_IP>
# You should get a Home Assistant CLI prompt
```

### Zigbee2MQTT Add-on (For Zigbee Devices)

If you are using Zigbee devices (roller shutters, sensors, etc.):

1. Go to **Settings** > **Add-ons** > **Add-on Store**
2. Click the three dots menu > **Repositories**
3. Add: `https://github.com/zigbee2mqtt/hassio-zigbee2mqtt`
4. Install "Zigbee2MQTT"
5. Configure your Zigbee coordinator in the add-on settings
6. Start the add-on

### HACS (Home Assistant Community Store)

HACS provides additional integrations not in the official store:

1. Open the SSH add-on terminal (or use SSH)
2. Run:

```bash
wget -O - https://get.hacs.xyz | bash -
```

3. Restart Home Assistant: **Settings** > **System** > **Restart**
4. Go to **Settings** > **Devices & Services** > **Add Integration**
5. Search for "HACS" and complete setup

**After HACS Installation**, install these integrations via HACS > Integrations:

- **ENTSO-E Tariff** (for electricity prices)
- **Fluvius** (if using Fluvius API instead of P1 reader)

---

## Repository Setup

### Step 1: Clone the Repository

```bash
# On your development machine
git clone https://github.com/YOUR_USERNAME/HAP.git
cd HAP
```

### Step 2: Create Local Secrets

The `secrets.yaml` file contains sensitive credentials and is never committed to git.

```bash
# Copy the example file
cp src/config/secrets.yaml.example src/config/secrets.yaml

# Edit with your actual values
nano src/config/secrets.yaml  # or use your preferred editor
```

**Example secrets.yaml**:

```yaml
# Home Assistant location
ha_latitude: 50.8503
ha_longitude: 4.3517
ha_elevation: 13

# ENTSO-E API Key (get from transparency.entsoe.eu)
entsoe_api_key: "your-api-key-here"

# Other API keys as needed
# tesla_client_id: "..."
# tesla_client_secret: "..."
```

### Step 3: Create secrets.yaml on the Raspberry Pi

The Pi needs its own copy of secrets.yaml (with production values):

```bash
# SSH into your Pi
ssh root@<PI_IP>

# Create secrets file
cd /config
nano secrets.yaml
```

Paste your production secrets and save.

### Step 4: Configure GitHub Secrets

For automated deployment via GitHub Actions, add these secrets to your repository:

1. Go to your GitHub repository
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Add the following secrets:

| Secret Name | Value |
|-------------|-------|
| `PI_HOST` | Your Pi's IP address or hostname |
| `PI_SSH_KEY` | Your private SSH key (contents of `~/.ssh/id_ed25519`) |
| `PI_USER` | `root` |

**Getting Your Private Key**:

```bash
cat ~/.ssh/id_ed25519
# Copy the entire output including BEGIN and END lines
```

### Step 5: Test Local Development Environment

Before deploying to the Pi, test locally:

```bash
# Start local Home Assistant
docker compose up -d

# View logs
docker compose logs -f homeassistant

# Access at http://localhost:8123
```

### Step 6: First Deployment

Once everything is configured:

```bash
# Validate configuration
python src/scripts/config_validator.py

# Commit and push to trigger deployment
git add .
git commit -m "Initial configuration"
git push origin main
```

The GitHub Actions workflow will:
1. Validate the configuration
2. SSH into your Pi
3. Sync the configuration files
4. Optionally restart Home Assistant

---

## Verification Checklist

After completing setup, verify each component:

- [ ] Pi is accessible at `http://<PI_IP>:8123`
- [ ] SSH connection works: `ssh root@<PI_IP>`
- [ ] Local Docker environment runs: `http://localhost:8123`
- [ ] Zigbee2MQTT add-on is running (if applicable)
- [ ] HACS is installed and accessible
- [ ] GitHub Actions deployment completes successfully
- [ ] Configuration changes from git appear on Pi

---

## Troubleshooting First Setup

### Pi Not Booting

- Verify power supply provides adequate power (5.1V/3A)
- Try a different USB port for the SSD
- Check the activity LED on the Pi
- Re-flash the image

### Cannot Find Pi on Network

- Ensure Ethernet is connected before first boot
- Check router DHCP leases
- Try `nmap -sn 192.168.1.0/24` to scan your network
- Connect a monitor to see boot messages

### SSH Connection Refused

- Verify the SSH add-on is started
- Check that your public key is in authorized_keys
- Ensure you are using the correct IP address
- Try: `ssh -v root@<PI_IP>` for verbose output

### Docker Compose Fails Locally

- Ensure Docker Desktop is running
- Check port 8123 is not in use: `lsof -i :8123`
- Try: `docker compose down && docker compose up -d`

---

## Next Steps

After completing initial setup:

1. **Read the Architecture Guide** - Understand what can and cannot be managed as code: [architecture.md](./architecture.md)
2. **Review Pitfalls** - Know the limitations before building: [pitfalls.md](./pitfalls.md)
3. **Plan for Recovery** - Prepare for disasters: [recovery.md](./recovery.md)
4. **Feature PRDs** - Review available features in `/prd/features/`

---

## Related Documentation

- [Architecture & IaC Analysis](./architecture.md) - Understanding HAP's approach to Infrastructure as Code
- [Pitfalls & Limitations](./pitfalls.md) - Honest assessment of what can go wrong
- [Disaster Recovery](./recovery.md) - How to recover from failures
- [Belgian Electricity Prices PRD](/prd/features/belgium-electricity-prices.md)
- [Tesla Integration PRD](/prd/features/tesla-integration.md)
- [Fluvius Metering PRD](/prd/features/fluvius-metering.md)
