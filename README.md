# Ansible Toolkit

[![lint](https://github.com/docaohieu2808/ansible-toolkit/actions/workflows/lint.yml/badge.svg)](https://github.com/docaohieu2808/ansible-toolkit/actions/workflows/lint.yml)

Reusable Ansible roles + playbooks for provisioning Linux servers (Docker, k3s, monitoring, security hardening, backup).

Designed to be a **toolkit** — bring your own inventory.

## Layout

```
ansible-toolkit/
├── ansible.cfg               # default config (override per deployment)
├── requirements.yml          # Galaxy collections deps
├── requirements.txt          # Python deps (ansible-core>=2.19)
├── .ansible-lint
├── inventories/
│   └── _examples/            # generic templates (TEST-NET IPs only)
├── playbooks/                # 7 playbooks (provision, security, k3s, monitoring, ...)
├── roles/                    # 11 roles (common, docker, nginx-proxy, security, ...)
└── plugins/
    └── inventory/            # terraform dynamic inventory
```

## Usage Pattern

### Option 1: Submodule (recommended for multi-server fleets)

In your inventory repo:

```bash
git submodule add https://github.com/<user>/ansible-toolkit.git
git commit -m 'add toolkit submodule'

# In your site.yml:
- ansible.builtin.import_playbook: ansible-toolkit/playbooks/full-provision.yml
- ansible.builtin.import_playbook: ansible-toolkit/playbooks/security.yml
```

### Option 2: Direct fork

```bash
git clone https://github.com/<user>/ansible-toolkit.git client-acme
cd client-acme
mkdir -p inventories/production
cp inventories/_examples/single-server.example.yml inventories/production/hosts.yml
# edit hosts.yml
ansible-playbook -i inventories/production playbooks/full-provision.yml
```

## Roles

| Role | Purpose |
|------|---------|
| common | Base packages, timezone, locale |
| docker | Install Docker CE + compose plugin |
| nginx-proxy | Nginx reverse proxy + certbot SSL |
| security | SSH hardening, fail2ban, unattended-upgrades |
| firewall | UFW rules + Docker UFW bypass fix |
| wireguard | WireGuard VPN server setup (legacy: my own fleet has since moved to Tailscale) |
| users | User management + SSH authorized keys |
| backup | Restic-based backup to S3/GCS |
| monitoring | node_exporter + Grafana Alloy log shipping to Loki (amd64 + arm64) |
| k3s | Lightweight Kubernetes (server + agent) |
| app-deploy | Generic Docker Compose app deploy |

## Playbooks

| Playbook | Use |
|----------|-----|
| full-provision.yml | Bootstrap a new server end-to-end |
| setup-server.yml | Common setup + SSH hardening only |
| deploy-docker.yml | Docker-only provision |
| security.yml | Security hardening (UFW + fail2ban + SSH) |
| k3s-setup.yml | Install k3s cluster |
| monitoring-setup.yml | Install node_exporter + Grafana Alloy |
| backup-setup.yml | Configure Restic backups |

## Requirements

- `ansible-core >= 2.19`
- Target: Ubuntu 22.04 / 24.04 (Debian also works)
- SSH key access to managed nodes
- Galaxy collections: `ansible.posix`, `community.general`, `community.docker`
  (see `requirements.yml`)

## ARM Support

Roles `monitoring`, `backup`, `docker` and `k3s` detect `ansible_architecture` at
runtime and select the correct release binary (`amd64` / `arm64`; `armv7` for node_exporter, restic and k3s; Grafana Alloy
ships no armv7 build and the role stops with a clear message there).
Oracle Cloud ARM (Neoverse-N1 / `aarch64`) is fully supported.

## License

MIT

## Supply chain

Every binary the roles download is verified before use:

| Role | Artifact | Verification |
|------|----------|--------------|
| monitoring | node_exporter, Grafana Alloy | `get_url` `checksum: sha256:<release checksums file>` |
| backup | restic | `get_url` `checksum: sha256:<SHA256SUMS of the release>` |
| k3s | k3s binary, install script | release `sha256sum-<arch>.txt`; install script pinned by `k3s_install_script_sha256` (bump with `k3s_version`) |
| docker | apt repository | `deb822_repository` with `Signed-By` keyring in `/etc/apt/keyrings` |

Versions are plain role variables (`node_exporter_version`, `alloy_version`,
`restic_version`, `k3s_version`) and are re-checked against upstream by the weekly CI run.

### Migrating from Promtail

Promtail reached end of life in 03/2026, so the monitoring role now installs
[Grafana Alloy](https://grafana.com/docs/alloy/latest/). Variables moved:
`promtail_loki_url` -> `alloy_loki_url`, `promtail_scrape_configs` -> `alloy_log_sources`
(same list shape), `promtail_port` -> `alloy_port` (default 12345, bound to
`alloy_listen_address` 127.0.0.1). The role does not remove an existing Promtail
service; stop and disable it on hosts that had it.

## Checks

Workflow `.github/workflows/lint.yml` runs on every push and pull request, on a
weekly schedule (Monday 02:00 UTC, to catch rot in upstream releases, collections
and runners) and on demand:

- `ansible-lint` with the `production` profile
- `ansible-playbook --syntax-check` on every playbook
- `molecule` converge + idempotence + verify of the `common`, `docker` and `monitoring`
  roles in a privileged systemd container (Debian 12) on the GitHub-hosted runner

Run the same locally with `ansible-lint` and `cd roles/<role> && molecule test`.

## License

MIT, see [LICENSE](LICENSE).
