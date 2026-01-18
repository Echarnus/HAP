# HAP - Home Assistant Pi

## Product Requirements Document

### Overview

HAP (Home Assistant Pi) is a declarative, version-controlled Home Assistant OS deployment for Raspberry Pi. All configuration, automations, and custom scripts are managed as code in this repository and automatically synchronized to the Raspberry Pi via GitHub Actions.

### Vision

**Infrastructure as Code for Smart Home**: Treat Home Assistant configuration like software—version controlled, reviewable, and reproducible. If the SD card fails, a new Pi can be configured from scratch using this repository.

### Goals

1. **Declarative Configuration**: All Home Assistant YAML configs stored in git
2. **Automated Deployment**: GitHub Actions pushes changes to Pi via SSH on every commit
3. **Reproducibility**: Full setup can be restored from repository alone
4. **Auditability**: All changes tracked in git history with clear commit messages
5. **Extensibility**: Custom scripts and integrations managed alongside config
6. **Validation**: Configuration validated before deployment to prevent failures

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Repository                        │
│  ┌─────────────────────────────┐  ┌─────────────────────────┐  │
│  │           src/              │  │  .github/workflows/     │  │
│  │  ┌─────────┐ ┌──────────┐  │  │  ├── deploy.yml         │  │
│  │  │ config/ │ │ scripts/ │  │  │  └── validate.yml       │  │
│  │  │(HA YAML)│ │ (custom) │  │  └─────────────────────────┘  │
│  │  └─────────┘ └──────────┘  │                               │
│  └─────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SSH (on push/schedule)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Raspberry Pi                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   Home Assistant OS                          ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  ││
│  │  │ /config      │  │ Add-ons      │  │ Custom Scripts   │  ││
│  │  │ (synced)     │  │ (SSH, Z2M)   │  │ (synced)         │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Components

#### 1. Home Assistant OS on Raspberry Pi

- **Hardware**: Raspberry Pi 4 (recommended 4GB+ RAM)
- **OS**: Home Assistant OS (dedicated appliance image)
- **Storage**: SD card or SSD via USB boot (preferred for reliability)

#### 2. Repository Structure

```
HAP/
├── prd/                               # Product requirements
│   ├── README.md                      # This document
│   └── features/                      # Feature-specific PRDs
│       ├── belgium-electricity-prices.md
│       ├── zaffer-roller-shutters.md
│       ├── tesla-integration.md
│       ├── eevee-mobility.md
│       ├── fluvius-metering.md
│       └── local-dev-environment.md
├── src/                               # All implementation files
│   ├── config/                        # Home Assistant configuration
│   │   ├── configuration.yaml         # Main HA config
│   │   ├── automations.yaml           # Automation rules
│   │   ├── scripts.yaml               # HA scripts
│   │   ├── sensors.yaml               # Sensor definitions
│   │   ├── customize.yaml             # Entity customizations
│   │   ├── ui-lovelace.yaml           # Dashboard configuration
│   │   ├── secrets.yaml.example       # Template (actual secrets NOT in git)
│   │   ├── hacs.yaml                  # HACS integration manifest
│   │   ├── zigbee2mqtt/               # Zigbee2MQTT configuration
│   │   │   └── configuration.yaml
│   │   └── custom_components/         # Custom integrations
│   └── scripts/                       # Custom Python scripts
│       ├── config_validator.py        # Config validation utility
│       ├── eevee_sync.py              # EEVEE charging data sync
│       └── fluvius_cost_calculator.py # Energy cost calculations
├── docker-compose.yml                 # Local development environment
├── docker-compose.override.yml.example # Local overrides template
├── .github/
│   └── workflows/
│       ├── deploy.yml                 # Deploy to Pi on push
│       └── validate.yml               # Validate config on PR
└── README.md                          # Setup instructions
```

#### 3. GitHub Actions Deployment

The deployment workflow:

1. Triggers on push to `main` branch (or manual dispatch)
2. **Validates configuration** using Home Assistant's config check
3. Connects to Raspberry Pi via SSH (using repository secrets)
4. Syncs `src/config/` files to Pi's `/config` directory
5. Optionally restarts Home Assistant to apply changes
6. Reports deployment status

**Required GitHub Secrets**:
- `PI_HOST`: Raspberry Pi IP/hostname
- `PI_SSH_KEY`: Private SSH key for authentication
- `PI_USER`: SSH username (typically `root` for HA OS)

#### 4. SSH Add-on on Home Assistant

- Install "Terminal & SSH" add-on from HA Add-on Store
- Configure authorized keys for GitHub Actions access
- Enable on port 22 (or custom port for security)

#### 5. Zigbee2MQTT Add-on

For Zigbee device control (roller shutters, sensors, etc.):

- Install Zigbee2MQTT add-on from HA Add-on Store
- Configuration stored in `src/config/zigbee2mqtt/`
- More IaC-friendly than ZHA (native integration)
- Device pairings can be backed up via `coordinator_backup.json`

**Note**: Device pairings are stored in the Zigbee coordinator, not in YAML. Backup strategy needed for full recovery.

#### 6. HACS (Home Assistant Community Store)

Custom integrations managed via HACS manifest:

```yaml
# src/config/hacs.yaml
# Manifest of installed HACS integrations
# Used for documentation and recovery

integrations:
  - name: ENTSO-E Tariff
    repository: JaccoR/hass-entso-e
    version: "latest"
    purpose: Belgian electricity spot prices

  - name: Fluvius
    repository: myTselworern/Fluvius
    version: "latest"
    purpose: Fluvius smart meter integration

frontend:
  - name: ApexCharts Card
    repository: RomRider/apexcharts-card
    version: "latest"
    purpose: Price charts on dashboard

  - name: Button Card
    repository: custom-cards/button-card
    version: "latest"
    purpose: Custom button styling
```

**Note**: HACS integrations must be manually installed via HACS UI. This manifest is for documentation and recovery purposes.

#### 7. Custom Scripts (Python)

All custom scripts are written in **Python** as the primary scripting language.

**Location**: `src/scripts/`

**Use Cases**:
- Device discovery and network scanning
- API bridges for unsupported integrations
- Data processing and transformation
- Configuration validation
- Automation helpers and utilities

**Requirements**:
- Python 3.x (available in Home Assistant OS via add-ons)
- Dependencies managed via `requirements.txt`
- Scripts follow PEP 8 style guidelines

### Security Considerations

1. **Secrets Management**:
   - `secrets.yaml` is gitignored and stored only on Pi
   - API keys, passwords never committed to repository
   - Use `secrets.yaml.example` as template
   - For fresh Pi setup: manually create `secrets.yaml` from example

2. **SSH Access**:
   - Use SSH key authentication only (no passwords)
   - Consider non-standard SSH port
   - GitHub Actions IP ranges can be allowlisted if needed

3. **Network**:
   - Pi should be on secured local network
   - Consider VPN/Tailscale for remote deployments

### Initial Setup Checklist

- [ ] Flash Home Assistant OS to Raspberry Pi
- [ ] Configure network and initial HA setup
- [ ] Install SSH add-on and configure keys
- [ ] Install Zigbee2MQTT add-on (if using Zigbee devices)
- [ ] Install HACS and required integrations
- [ ] Set up GitHub repository with this structure
- [ ] Configure GitHub Actions secrets
- [ ] Create `secrets.yaml` on Pi from example
- [ ] Test deployment workflow
- [ ] Set up backup strategy for coordinator and database

### Configuration Validation

Validation runs automatically on PRs and before deployment:

1. **YAML Syntax Check**: Verify all YAML files parse correctly
2. **Home Assistant Config Check**: Run `hass --script check_config`
3. **Secret References**: Verify all `!secret` references have corresponding entries

Run locally:
```bash
python src/scripts/config_validator.py
```

### Local Development

See [Local Development Environment PRD](./features/local-dev-environment.md) for Docker-based testing.

Quick start:
```bash
docker compose up -d
# Access at http://localhost:8123
```

### Backup & Recovery

#### What's in Git (IaC)
- All YAML configuration
- Automation rules
- Dashboard layouts
- Python scripts

#### What's NOT in Git (requires separate backup)
- `secrets.yaml` (manual backup)
- Zigbee device pairings (coordinator backup)
- Home Assistant database (history, statistics)
- HACS integrations (reinstall via manifest)

#### Recovery Procedure
1. Flash fresh Home Assistant OS
2. Install SSH, Zigbee2MQTT, HACS add-ons
3. Create `secrets.yaml` from template
4. Deploy configuration via GitHub Actions
5. Restore Zigbee coordinator backup (if available)
6. Reinstall HACS integrations per manifest
7. Accept loss of historical data (or restore database backup)

### Future Considerations

- Bi-directional sync (UI changes back to git)
- Automated testing of configurations before deployment
- Blue/green deployments with rollback capability
- Multi-environment support (dev Pi, prod Pi)
- Automatic rollback on health check failure

---

## Features

Feature-specific PRDs are located in the [`features/`](./features/) directory:

### Energy Management
- [Belgian Electricity Prices](./features/belgium-electricity-prices.md) - Dynamic electricity pricing for EV charging optimization
- [Fluvius Energy Metering](./features/fluvius-metering.md) - Digital meter integration for consumption tracking

### EV Charging
- [Tesla Integration](./features/tesla-integration.md) - Smart charging based on electricity prices
- [EEVEE Mobility](./features/eevee-mobility.md) - Public charging session tracking

### Home Automation
- [Zaffer Roller Shutters](./features/zaffer-roller-shutters.md) - Smartphone control for roller shutters

### Development
- [Local Development Environment](./features/local-dev-environment.md) - Docker-based testing before deployment
