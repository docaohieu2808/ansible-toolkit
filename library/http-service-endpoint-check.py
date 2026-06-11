#!/usr/bin/python
# -*- coding: utf-8 -*-
# =============================================================================
# Ansible Custom Module: http-service-endpoint-check
# Checks if an HTTP/HTTPS endpoint is responding with expected status code.
# Uses urllib (stdlib only) — no pip dependencies.
# =============================================================================

DOCUMENTATION = r'''
---
module: service_endpoint_check
short_description: Check if an HTTP/HTTPS endpoint is responding
description:
  - Performs an HTTP GET request to the given URL using Python urllib.
  - Returns status code, response time, and a healthy boolean.
  - No external dependencies — uses Python standard library only.
options:
  url:
    description: Full URL to check (http:// or https://).
    required: true
    type: str
  expected_status:
    description: HTTP status code considered healthy.
    required: false
    type: int
    default: 200
  timeout:
    description: Seconds to wait for a response before failing.
    required: false
    type: int
    default: 10
author:
  - hieudc
'''

EXAMPLES = r'''
- name: Check service login page
  service_endpoint_check:
    url: https://example.com/login
    expected_status: 200
    timeout: 10
  register: result

- debug:
    var: result

- name: Fail if endpoint is unhealthy
  fail:
    msg: "Endpoint {{ result.url }} is down ({{ result.status_code }})"
  when: not result.healthy
'''

RETURN = r'''
url:
  description: The URL that was checked.
  type: str
status_code:
  description: HTTP status code received, or -1 on connection error.
  type: int
response_time:
  description: Round-trip response time in seconds (2 decimal places).
  type: float
healthy:
  description: True when status_code matches expected_status.
  type: bool
error:
  description: Error message on connection failure, empty string otherwise.
  type: str
'''

import time
import ssl

from ansible.module_utils.basic import AnsibleModule

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
except ImportError:
    # Python 2 fallback (unlikely on Ansible 2.16 but kept for completeness)
    from urllib2 import urlopen, Request, URLError, HTTPError  # noqa: F401


def check_endpoint(url, expected_status, timeout):
    """Perform HTTP GET and return (status_code, response_time, error)."""
    # Allow self-signed certs (monitoring use case)
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    req = Request(url, headers={"User-Agent": "ansible-service-endpoint-check/1.0"})

    start = time.time()
    try:
        with urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
            status_code = resp.getcode()
    except HTTPError as exc:
        # HTTPError is a valid response with an error status code
        status_code = exc.code
    except URLError as exc:
        elapsed = round(time.time() - start, 2)
        return -1, elapsed, str(exc.reason)
    except Exception as exc:
        elapsed = round(time.time() - start, 2)
        return -1, elapsed, str(exc)

    elapsed = round(time.time() - start, 2)
    return status_code, elapsed, ""


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type="str", required=True),
            expected_status=dict(type="int", required=False, default=200),
            timeout=dict(type="int", required=False, default=10),
        ),
        supports_check_mode=True,
    )

    url = module.params["url"]
    expected_status = module.params["expected_status"]
    timeout = module.params["timeout"]

    status_code, response_time, error = check_endpoint(url, expected_status, timeout)

    healthy = status_code == expected_status

    module.exit_json(
        changed=False,
        url=url,
        status_code=status_code,
        response_time=response_time,
        healthy=healthy,
        error=error,
    )


if __name__ == "__main__":
    main()
