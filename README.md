# HAP - Home Assistant Pi

Infrastructure-as-Code approach for Home Assistant on Raspberry Pi. Version-controlled configuration with automated deployment via GitHub Actions.

## What is HAP?

HAP treats Home Assistant configuration like software:
- **Version controlled** - All YAML configs in git
- **Automated deployment** - Push to deploy via GitHub Actions
- **Reproducible** - Rebuild from repository (with documented manual steps)
- **Testable** - Local Docker environment for validation

## Quick Start

```bash
# Clone repository
git clone https://github.com/Echarnus/HAP.git
cd HAP

# Start local development environment
docker compose up -d

# Access Home Assistant at http://localhost:8123
```

## Repository Structure

```
HAP/
├── prd/                    # Product Requirements Documents
│   ├── README.md           # Main PRD
│   └── features/           # Feature-specific PRDs
├── src/
│   ├── config/             # Home Assistant configuration
│   │   ├── configuration.yaml
│   │   ├── automations.yaml
│   │   ├── secrets.yaml.example
│   │   └── zigbee2mqtt/
│   └── scripts/            # Python utilities
├── docs/                   # Documentation
│   ├── getting-started.md
│   ├── architecture.md
│   ├── pitfalls.md
│   └── recovery.md
├── .github/workflows/      # CI/CD
│   ├── validate.yml        # Config validation
│   └── deploy.yml          # Deploy to Pi
└── docker-compose.yml      # Local development
```

## Features

| Feature | Description | Status |
|---------|-------------|--------|
| [Belgian Electricity Prices](prd/features/belgium-electricity-prices.md) | ENTSO-E spot prices for smart charging | Planned |
| [Tesla Integration](prd/features/tesla-integration.md) | Wall Charger + Vehicle control | Planned |
| [Fluvius Metering](prd/features/fluvius-metering.md) | Digital meter integration | Planned |
| [Zaffer Roller Shutters](prd/features/zaffer-roller-shutters.md) | Zigbee shutter control | Planned |
| [EEVEE Mobility](prd/features/eevee-mobility.md) | Public charging tracking | Planned |

## Documentation

- [Getting Started](docs/getting-started.md) - Hardware, software, and setup guide
- [Architecture](docs/architecture.md) - IaC analysis and what's possible
- [Pitfalls](docs/pitfalls.md) - Limitations and gotchas
- [Recovery](docs/recovery.md) - Disaster recovery procedures

## IaC Reality Check

HAP achieves **~60% Infrastructure-as-Code**. Some things cannot be managed as code:

| IaC (in git) | NOT IaC (manual) |
|--------------|------------------|
| YAML configuration | secrets.yaml |
| Automations | Device pairings |
| Template sensors | HACS integrations |
| Dashboards (YAML mode) | UI-configured integrations |
| Python scripts | Historical data |

See [Architecture](docs/architecture.md) for full details.

## Development

### Local Testing

```bash
# Start Home Assistant locally
docker compose up -d

# Validate configuration
python src/scripts/config_validator.py

# View logs
docker compose logs -f homeassistant
```

### Deployment

Push to `main` branch triggers GitHub Actions:
1. Validates configuration
2. Syncs to Raspberry Pi via SSH
3. Restarts Home Assistant

Required GitHub Secrets:
- `PI_HOST` - Raspberry Pi IP/hostname
- `PI_SSH_KEY` - SSH private key
- `PI_USER` - SSH username (usually `root`)

## License

Private repository - personal use only.
