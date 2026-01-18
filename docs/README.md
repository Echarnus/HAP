# HAP Documentation

> Comprehensive documentation for the Home Assistant Pi (HAP) project - an Infrastructure-as-Code approach for Home Assistant on Raspberry Pi.

## About HAP

HAP enables you to manage your Home Assistant configuration as code, with version control via Git and automated deployment via GitHub Actions. This documentation provides everything you need to set up, operate, and recover your HAP installation.

---

## Documentation Index

### Getting Started

| Document | Description |
|----------|-------------|
| [Getting Started Guide](./getting-started.md) | Complete setup from hardware to first deployment |

Covers hardware requirements, software prerequisites, Raspberry Pi setup, repository configuration, and first deployment.

### Understanding HAP

| Document | Description |
|----------|-------------|
| [Architecture & IaC Analysis](./architecture.md) | What is and is not Infrastructure as Code |
| [Pitfalls & Limitations](./pitfalls.md) | Honest assessment of challenges and limitations |

Before building your configuration, understand what HAP can and cannot achieve. These documents provide an honest assessment of the IaC gap and common issues you will encounter.

### Operations

| Document | Description |
|----------|-------------|
| [Disaster Recovery](./recovery.md) | Step-by-step recovery procedures |

When things go wrong (and they will), this guide provides detailed recovery procedures with time estimates and complexity ratings.

---

## Feature Documentation

Feature-specific requirements and implementation details are in the PRD directory:

| Feature | PRD Location |
|---------|--------------|
| Belgian Electricity Prices | [/prd/features/belgium-electricity-prices.md](/prd/features/belgium-electricity-prices.md) |
| Tesla Integration | [/prd/features/tesla-integration.md](/prd/features/tesla-integration.md) |
| EEVEE Mobility | [/prd/features/eevee-mobility.md](/prd/features/eevee-mobility.md) |
| Fluvius Metering | [/prd/features/fluvius-metering.md](/prd/features/fluvius-metering.md) |
| Zaffer Roller Shutters | [/prd/features/zaffer-roller-shutters.md](/prd/features/zaffer-roller-shutters.md) |
| Local Development | [/prd/features/local-dev-environment.md](/prd/features/local-dev-environment.md) |

---

## Quick Reference

### Essential Commands

```bash
# Local Development
docker compose up -d                    # Start local HA
docker compose logs -f homeassistant    # View logs
docker compose down                     # Stop local HA

# Configuration Validation
python src/scripts/config_validator.py  # Validate before deployment

# Raspberry Pi Access
ssh root@<PI_IP>                        # SSH to Pi
ha core logs                            # View HA logs (on Pi)
ha core restart                         # Restart HA (on Pi)

# Deployment
git push origin main                    # Trigger deployment
```

### Key Directories

| Location | Contents |
|----------|----------|
| `/Users/kennethdeclercq/Projects/HAP/src/config/` | Home Assistant configuration files |
| `/Users/kennethdeclercq/Projects/HAP/src/scripts/` | Python utility scripts |
| `/Users/kennethdeclercq/Projects/HAP/docs/` | This documentation |
| `/Users/kennethdeclercq/Projects/HAP/prd/` | Product requirements documents |
| `/config/` (on Pi) | Deployed configuration |
| `/config/.storage/` (on Pi) | Home Assistant state (not in git) |

### Important Files

| File | Purpose |
|------|---------|
| `configuration.yaml` | Main Home Assistant configuration |
| `automations.yaml` | Automation rules |
| `secrets.yaml` | Sensitive credentials (never in git) |
| `secrets.yaml.example` | Template for secrets |
| `hacs.yaml` | HACS integration manifest (documentation) |

---

## What HAP Achieves

HAP provides:

- Version-controlled Home Assistant configuration
- Automated deployment via GitHub Actions
- Local Docker testing environment
- Configuration validation before deployment
- Documented recovery procedures

HAP does NOT provide (and cannot provide):

- True Infrastructure as Code (like Terraform)
- Automatic device pairing recovery
- HACS integration automation
- UI-configured integration backup
- Historical data as code

Read [Architecture & IaC Analysis](./architecture.md) for a complete understanding.

---

## Support

### HAP-Specific Issues

For issues with this specific HAP implementation, check the GitHub repository issues.

### Home Assistant General

- [Home Assistant Documentation](https://www.home-assistant.io/docs/)
- [Home Assistant Community Forum](https://community.home-assistant.io/)
- [Home Assistant Discord](https://discord.gg/home-assistant)

### Integrations

- [Zigbee2MQTT Documentation](https://www.zigbee2mqtt.io/)
- [HACS Documentation](https://hacs.xyz/)
- [ENTSO-E Integration](https://github.com/JaccoR/hass-entso-e)
