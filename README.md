# Ansible Toolkit

Reusable Ansible roles + playbooks for provisioning Linux servers (Docker, k3s, monitoring, security hardening, backup).

Designed to be a **toolkit** — bring your own inventory.

## Layout

```
ansible-toolkit/
├── ansible.cfg               # default config (override per deployment)
├── requirements.yml          # Galaxy collections deps
├── requirements.txt          # Python deps (ansible-core>=2.14)
├── .ansible-lint
├── inventories/
│   └── _examples/            # generic templates (TEST-NET IPs only)
├── playbooks/                # 7 playbooks (provision, security, k3s, monitoring, ...)
├── roles/                    # 11 roles (common, docker, nginx-proxy, security, ...)
├── library/                  # custom modules
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
- import_playbook: ansible-toolkit/playbooks/full-provision.yml
- import_playbook: ansible-toolkit/playbooks/security.yml
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
| wireguard | WireGuard VPN server setup |
| users | User management + SSH authorized keys |
| backup | Restic-based backup to S3/GCS |
| monitoring | Node exporter + promtail (amd64 + arm64) |
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
| monitoring-setup.yml | Install node_exporter + promtail |
| backup-setup.yml | Configure Restic backups |

## Requirements

- `ansible-core >= 2.14`
- Target: Ubuntu 22.04 / 24.04 (Debian also works)
- SSH key access to managed nodes
- Galaxy collections: `ansible.posix`, `community.general`, `community.docker`
  (see `requirements.yml`)

## ARM Support

Roles `monitoring`, `backup`, and `docker` detect `ansible_architecture` at
runtime and select the correct release binary (`amd64` / `arm64` / `armv7`).
Oracle Cloud ARM (Neoverse-N1 / `aarch64`) is fully supported.

## License

MIT
