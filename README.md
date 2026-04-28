# Ansible Toolkit

Reusable Ansible roles + playbooks for provisioning Linux servers (Docker, k3s, Patroni, monitoring, security hardening).

Designed to be a **toolkit** — bring your own inventory.

## Layout

```
ansible-toolkit/
├── ansible.cfg               # default config (override per deployment)
├── requirements.yml          # Galaxy collections deps
├── requirements.txt          # Python deps
├── .ansible-lint
├── inventories/
│   └── _examples/            # generic templates
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
| docker | Install Docker + compose |
| nginx-proxy | Nginx reverse proxy |
| security | SSH hardening, fail2ban, auto-update |
| firewall | UFW rules |
| wireguard | VPN setup |
| users | User management + SSH keys |
| backup | Restic-based backup |
| monitoring | Node exporter + cadvisor + promtail |
| k3s | Lightweight Kubernetes |
| app-deploy | Generic Docker app deploy |

## Playbooks

| Playbook | Use |
|----------|-----|
| full-provision.yml | Bootstrap a new server end-to-end |
| setup-server.yml | Common setup only |
| deploy-docker.yml | Docker-only provision |
| security.yml | Security hardening |
| k3s-setup.yml | Install k3s |
| monitoring-setup.yml | Install monitoring stack |
| backup-setup.yml | Configure Restic backups |

## Requirements

- Ansible >= 2.14
- Target: Ubuntu 22.04 / 24.04 (Debian also works)
- SSH key access to managed nodes

## License

MIT
