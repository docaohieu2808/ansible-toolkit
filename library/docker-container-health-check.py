#!/usr/bin/python
# -*- coding: utf-8 -*-
# =============================================================================
# Ansible Custom Module: docker-container-health-check
# Checks if a Docker container is running and healthy via docker CLI.
# No docker SDK required — uses subprocess to call docker inspect/ps.
# =============================================================================

DOCUMENTATION = r'''
---
module: docker_health_check
short_description: Check Docker container running state and health status
description:
  - Uses docker CLI (not docker SDK) to inspect a named container.
  - Returns container status, health status, uptime, exposed ports, and image.
options:
  container_name:
    description: Name or ID of the Docker container to inspect.
    required: true
    type: str
  timeout:
    description: Seconds to wait for docker CLI response.
    required: false
    type: int
    default: 30
author:
  - hieudc
'''

EXAMPLES = r'''
- name: Check Jenkins container health
  docker_health_check:
    container_name: jenkins
  register: result

- debug:
    var: result
'''

RETURN = r'''
container_name:
  description: Name of the inspected container.
  type: str
status:
  description: Container running state (running, exited, paused, etc.).
  type: str
health_status:
  description: Docker HEALTHCHECK status (healthy, unhealthy, starting, none).
  type: str
uptime:
  description: Container start time as ISO-8601 string.
  type: str
ports:
  description: List of exposed port mappings.
  type: list
image:
  description: Image name used by the container.
  type: str
healthy:
  description: True when status is running AND health is healthy or none.
  type: bool
'''

import json
import subprocess

from ansible.module_utils.basic import AnsibleModule


def run_docker_inspect(container_name, timeout):
    """Run `docker inspect <container>` and return parsed JSON or error."""
    try:
        result = subprocess.run(
            ["docker", "inspect", container_name],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, "docker inspect timed out after {}s".format(timeout)
    except FileNotFoundError:
        return None, "docker binary not found in PATH"

    if result.returncode != 0:
        stderr = result.stderr.strip()
        return None, "docker inspect failed (rc={}): {}".format(result.returncode, stderr)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, "failed to parse docker inspect output: {}".format(exc)

    if not data:
        return None, "container '{}' not found".format(container_name)

    return data[0], None


def extract_ports(network_settings):
    """Extract readable port mappings from NetworkSettings.Ports dict."""
    ports = []
    raw_ports = network_settings.get("Ports") or {}
    for container_port, bindings in raw_ports.items():
        if bindings:
            for b in bindings:
                ports.append("{}->{}".format(b.get("HostPort", "?"), container_port))
        else:
            ports.append(container_port)
    return ports


def main():
    module = AnsibleModule(
        argument_spec=dict(
            container_name=dict(type="str", required=True),
            timeout=dict(type="int", required=False, default=30),
        ),
        supports_check_mode=True,
    )

    container_name = module.params["container_name"]
    timeout = module.params["timeout"]

    inspect_data, error = run_docker_inspect(container_name, timeout)
    if error:
        module.fail_json(msg=error, container_name=container_name)

    state = inspect_data.get("State", {})
    config = inspect_data.get("Config", {})
    network_settings = inspect_data.get("NetworkSettings", {})

    status = state.get("Status", "unknown")
    started_at = state.get("StartedAt", "")
    image = config.get("Image", "unknown")
    ports = extract_ports(network_settings)

    # Health status — only present when HEALTHCHECK is defined in image
    health = state.get("Health")
    if health:
        health_status = health.get("Status", "unknown")
    else:
        health_status = "none"

    # Consider healthy: running + (health ok or no healthcheck defined)
    healthy = status == "running" and health_status in ("healthy", "none")

    module.exit_json(
        changed=False,
        container_name=container_name,
        status=status,
        health_status=health_status,
        uptime=started_at,
        ports=ports,
        image=image,
        healthy=healthy,
    )


if __name__ == "__main__":
    main()
