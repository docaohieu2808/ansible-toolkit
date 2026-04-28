#!/usr/bin/env python3
# =============================================================================
# Ansible Dynamic Inventory - reads Terraform output JSON
# =============================================================================
# Usage:
#   ansible-playbook -i inventory/terraform-dynamic-inventory.py playbook.yml
#
# Expects Terraform output in one of two ways:
#   1. TERRAFORM_STATE_FILE env var pointing to a terraform.tfstate file
#   2. TERRAFORM_OUTPUT_FILE env var pointing to a pre-generated output JSON
#      (produced by: terraform output -json > tf_output.json)
#
# Expected Terraform output structure:
#   servers = {
#     value = {
#       "server-1" = {
#         ip         = "1.2.3.4"
#         group      = "backend_cluster"
#         user       = "root"               # optional, defaults to root
#         tags       = { role = "primary" } # optional
#       }
#     }
#   }
# =============================================================================

import json
import os
import subprocess
import sys


def get_terraform_output():
    """Load Terraform output JSON from file or by running terraform output."""
    output_file = os.environ.get("TERRAFORM_OUTPUT_FILE")
    state_file = os.environ.get("TERRAFORM_STATE_FILE")

    if output_file:
        with open(output_file) as f:
            return json.load(f)

    if state_file:
        result = subprocess.run(
            ["terraform", "output", "-json", "-state", state_file],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            sys.stderr.write(f"terraform output failed: {result.stderr}\n")
            sys.exit(1)
        return json.loads(result.stdout)

    # Try running terraform output in current directory
    result = subprocess.run(
        ["terraform", "output", "-json"],
        capture_output=True,
        text=True,
        cwd=os.environ.get("TERRAFORM_DIR", "."),
    )
    if result.returncode != 0:
        # Return empty inventory gracefully if terraform not available
        sys.stderr.write("Warning: terraform output failed, returning empty inventory\n")
        return {}
    return json.loads(result.stdout)


def build_inventory(tf_output):
    """Convert Terraform output to Ansible inventory format."""
    inventory = {
        "_meta": {"hostvars": {}},
        "all": {"children": [], "hosts": [], "vars": {}},
    }

    # Extract servers output key (supports 'servers' or 'instances' key)
    servers_raw = tf_output.get("servers", tf_output.get("instances", {}))
    if not servers_raw:
        return inventory

    servers = servers_raw.get("value", servers_raw)

    groups = {}

    for hostname, attrs in servers.items():
        ip = attrs.get("ip", attrs.get("public_ip", attrs.get("private_ip", "")))
        group = attrs.get("group", "ungrouped")
        user = attrs.get("user", "root")
        tags = attrs.get("tags", {})

        # Build hostvars
        hostvars = {
            "ansible_host": ip,
            "ansible_user": user,
        }
        # Merge any extra tags as hostvars
        for k, v in tags.items():
            hostvars[k] = v

        inventory["_meta"]["hostvars"][hostname] = hostvars

        # Add to group
        if group not in groups:
            groups[group] = {"hosts": [], "vars": {}}
        groups[group]["hosts"].append(hostname)

    # Add groups to inventory
    for group_name, group_data in groups.items():
        inventory[group_name] = group_data
        if group_name not in inventory["all"]["children"]:
            inventory["all"]["children"].append(group_name)

    return inventory


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        tf_output = get_terraform_output()
        inventory = build_inventory(tf_output)
        print(json.dumps(inventory, indent=2))

    elif len(sys.argv) > 1 and sys.argv[1] == "--host":
        # hostvars are returned in _meta, so this can be empty
        print(json.dumps({}))

    else:
        # Default: return full inventory (same as --list)
        tf_output = get_terraform_output()
        inventory = build_inventory(tf_output)
        print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
