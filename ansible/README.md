# Ansible Infrastructure Automation

Ansible project for automated configuration, deployment and management of a multi-server DevOps Home Lab.

## Infrastructure

| Host | OS | IP address | Purpose |
|---|---|---|---|
| AUTO01 | Rocky Linux 10 | 172.16.10.30 | Ansible control node |
| DEV01 | Debian 13 | 172.16.10.10 | Application and Docker |
| MON01 | Debian 13 | 172.16.10.20 | Monitoring stack |

## Architecture

- AUTO01 manages DEV01 and MON01 over SSH.
- Docker Engine and Docker Compose are configured through Ansible.
- Application and monitoring configurations are deployed from GitHub.
- Docker Compose manages application and monitoring containers.
- Prometheus and Grafana provide infrastructure monitoring.

## Project Structure

```text
ansible-lab/
├── ansible.cfg
├── inventory/
│   ├── hosts.ini
│   └── group_vars/
│       └── all.yml
├── playbooks/
│   ├── deploy-app.yml
│   ├── deploy-infrastructure.yml
│   ├── docker-setup.yml
│   ├── start-infrastructure.yml
│   ├── system-info.yml
│   ├── system-maintenance.yml
│   └── vmware-tools-network.yml
├── roles/
│   ├── application/
│   ├── docker/
│   ├── monitoring/
│   └── vmware_tools_network/
├── requirements.yml
└── site.yml
```

## Requirements

- Ansible Core 2.16.16
- Python 3.12+
- SSH access to managed hosts
- Docker Engine and Docker Compose support

### Ansible Collections

Install required collections:

```bash
ansible-galaxy collection install -r requirements.yml
```

Pinned dependencies:

- community.docker 3.13.0
- ansible.posix 2.2.2

## Configuration

Inventory is defined in `inventory/hosts.ini`.

Shared variables are stored in `inventory/group_vars/all.yml`.

SSH key-based authentication is used between AUTO01 and managed hosts.

## Deployment

Check connectivity:

```bash
ansible all -m ping
```

Check playbook syntax:

```bash
ansible-playbook site.yml --syntax-check
```

Run the complete infrastructure deployment:

```bash
ansible-playbook site.yml
```

## Available Playbooks

| Playbook | Purpose |
|---|---|
| `site.yml` | Complete infrastructure deployment |
| `docker-setup.yml` | Docker configuration |
| `vmware-tools-network.yml` | Protect Docker bridges from VMware Tools suspend/resume |
| `deploy-infrastructure.yml` | Deploy application and monitoring configuration |
| `start-infrastructure.yml` | Start application and monitoring |
| `deploy-app.yml` | Pull nginx and backend from GHCR and recreate those containers |
| `system-info.yml` | Collect system information |
| `system-maintenance.yml` | Perform system maintenance |

## VMware Tools and Docker networking

On VMware guests, `open-vm-tools` runs `/etc/vmware-tools/scripts/vmware/network` during suspend and resume.

The suspend path records active Ethernet interfaces and later flushes their addresses. Docker bridges (`docker0`, `br-*`) and `veth*` pairs are included by default, so gateway addresses such as `172.17.0.1/16` and `172.18.0.1/16` disappear. Published container ports then time out until the addresses are restored.

The `vmware_tools_network` role patches that script in place so container interfaces are skipped. The upstream script itself is not copied into the application tree.

Run only this fix:

```bash
ansible-playbook playbooks/vmware-tools-network.yml
```

## Monitoring

| Service | URL |
|---|---|
| Grafana | http://172.16.10.20:3000 |
| Prometheus | http://172.16.10.20:9090 |

## Idempotency

The complete deployment was executed repeatedly and verified with:

- `failed=0`
- `unreachable=0`
- `changed=0` on subsequent runs

## Safety

- Secrets and environment files must not be committed.
- Existing Docker volumes must be preserved.
- Deployment does not remove unmanaged files.

