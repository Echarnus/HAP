#!/usr/bin/env python3
"""
HAP - Configuration Validator

Validates Home Assistant configuration files before deployment.
Run this script locally before committing changes.

Usage:
    python src/scripts/config_validator.py

Returns:
    0 - All validations passed
    1 - Validation failed
"""

import subprocess
import sys
import os
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent / "config"
SECRETS_EXAMPLE = CONFIG_DIR / "secrets.yaml.example"


def check_yaml_syntax() -> list:
    """
    Check YAML syntax for all configuration files.

    Returns:
        List of (file_path, error_message) tuples for any errors found.
    """
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not installed. Run: pip install pyyaml")
        sys.exit(1)

    errors = []

    for yaml_file in CONFIG_DIR.glob("**/*.yaml"):
        # Skip secrets and example files
        if "secret" in yaml_file.name and "example" not in yaml_file.name:
            continue

        try:
            with open(yaml_file) as f:
                content = f.read()

                # Handle Home Assistant's !secret, !include, etc. tags
                # by replacing them with safe placeholders
                safe_content = content
                for tag in ["!secret", "!include", "!include_dir_list",
                           "!include_dir_named", "!include_dir_merge_list",
                           "!include_dir_merge_named", "!env_var"]:
                    safe_content = safe_content.replace(tag, "placeholder_")

                yaml.safe_load(safe_content)
            print(f"  OK: {yaml_file.relative_to(CONFIG_DIR.parent.parent)}")

        except yaml.YAMLError as e:
            errors.append((yaml_file, str(e)))
            print(f"  ERROR: {yaml_file.relative_to(CONFIG_DIR.parent.parent)}")
            print(f"    {e}")

    return errors


def check_secret_references() -> list:
    """
    Check that all !secret references have corresponding entries in secrets.yaml.example.

    Returns:
        List of missing secret names.
    """
    import re

    missing = []
    secret_pattern = re.compile(r"!secret\s+(\w+)")

    # Get all secrets defined in example file
    defined_secrets = set()
    if SECRETS_EXAMPLE.exists():
        with open(SECRETS_EXAMPLE) as f:
            for line in f:
                # Match lines like "secret_name: value"
                match = re.match(r"^(\w+):", line)
                if match:
                    defined_secrets.add(match.group(1))

    # Find all !secret references in config files
    for yaml_file in CONFIG_DIR.glob("**/*.yaml"):
        if "secret" in yaml_file.name:
            continue

        try:
            with open(yaml_file) as f:
                content = f.read()

            for match in secret_pattern.finditer(content):
                secret_name = match.group(1)
                if secret_name not in defined_secrets:
                    missing.append((secret_name, yaml_file))

        except Exception:
            pass  # Skip files we can't read

    return missing


def check_homeassistant_config() -> bool:
    """
    Run Home Assistant's config check if Docker is available.

    Returns:
        True if validation passed or Docker not available, False if failed.
    """
    try:
        # Check if Docker is available
        result = subprocess.run(
            ["docker", "compose", "ps"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=CONFIG_DIR.parent.parent.parent  # HAP root directory
        )

        # Check if homeassistant container is running
        if "hap-dev-homeassistant" not in result.stdout:
            print("  Docker container not running, skipping HA config check")
            print("  (Start with: docker compose up -d)")
            return True

        # Run config check in container
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "homeassistant",
             "python", "-m", "homeassistant", "--script", "check_config",
             "--config", "/config"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=CONFIG_DIR.parent.parent.parent
        )

        if result.returncode == 0:
            print("  Home Assistant config check: PASSED")
            return True
        else:
            print("  Home Assistant config check: FAILED")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("  Config check timed out")
        return False
    except FileNotFoundError:
        print("  Docker not available, skipping HA config check")
        return True
    except Exception as e:
        print(f"  Could not run HA config check: {e}")
        return True


def check_for_hardcoded_secrets() -> list:
    """
    Look for potentially hardcoded secrets in config files.

    Returns:
        List of (file, line_number, line) tuples for suspicious content.
    """
    import re

    suspicious = []

    # Patterns that might indicate hardcoded secrets
    patterns = [
        (r"api_key:\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?", "API key"),
        (r"password:\s*['\"]?(?!!)(?!\s*$).+['\"]?", "Password"),
        (r"token:\s*['\"]?[a-zA-Z0-9_.-]{30,}['\"]?", "Token"),
    ]

    for yaml_file in CONFIG_DIR.glob("**/*.yaml"):
        # Skip secrets files
        if "secret" in yaml_file.name:
            continue

        try:
            with open(yaml_file) as f:
                for line_num, line in enumerate(f, 1):
                    # Skip lines with !secret references
                    if "!secret" in line:
                        continue

                    for pattern, pattern_name in patterns:
                        if re.search(pattern, line):
                            suspicious.append((yaml_file, line_num, line.strip(), pattern_name))

        except Exception:
            pass

    return suspicious


def main():
    """Run all validations and report results."""
    print("=" * 60)
    print("HAP - Configuration Validator")
    print("=" * 60)

    all_passed = True

    # 1. YAML Syntax Check
    print("\n1. Checking YAML syntax...")
    yaml_errors = check_yaml_syntax()
    if yaml_errors:
        all_passed = False

    # 2. Secret References Check
    print("\n2. Checking secret references...")
    missing_secrets = check_secret_references()
    if missing_secrets:
        print("  WARNING: The following secrets are used but not in secrets.yaml.example:")
        for secret_name, file_path in missing_secrets:
            print(f"    - {secret_name} (in {file_path.name})")
        # Warning only, don't fail

    # 3. Hardcoded Secrets Check
    print("\n3. Checking for hardcoded secrets...")
    suspicious = check_for_hardcoded_secrets()
    if suspicious:
        print("  WARNING: Potential hardcoded secrets found:")
        for file_path, line_num, line, pattern_name in suspicious:
            print(f"    - {file_path.name}:{line_num} ({pattern_name})")
        # Warning only, don't fail

    # 4. Home Assistant Config Check (if Docker available)
    print("\n4. Running Home Assistant config check...")
    ha_check = check_homeassistant_config()
    if not ha_check:
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("VALIDATION PASSED")
        print("=" * 60)
        return 0
    else:
        print("VALIDATION FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
