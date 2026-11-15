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
| `postgres-backup.yml` | Dump PostgreSQL, copy it to AUTO01, rotate old dumps |
| `postgres-restore-test.yml` | Restore a dump into a temporary database and compare row count and content checksum |
| `postgres-restore.yml` | Restore a dump over the production database; requires an explicit confirmation |
| `postgres-backup-schedule.yml` | Install the daily backup crontab on AUTO01 |

## VMware Tools and Docker networking

On VMware guests, `open-vm-tools` runs `/etc/vmware-tools/scripts/vmware/network` during suspend and resume.

The suspend path records active Ethernet interfaces and later flushes their addresses. Docker bridges (`docker0`, `br-*`) and `veth*` pairs are included by default, so gateway addresses such as `172.17.0.1/16` and `172.18.0.1/16` disappear. Published container ports then time out until the addresses are restored.

The `vmware_tools_network` role patches that script in place so container interfaces are skipped. The upstream script itself is not copied into the application tree.

Run only this fix:

```bash
ansible-playbook playbooks/vmware-tools-network.yml
```

## PostgreSQL backups

Backups are logical `pg_dump -Fc` dumps of the running `dev01-postgres` container. PostgreSQL stays up, and the `devops-lab_postgres_data` volume is not replaced. The database role is the container's `POSTGRES_USER` (`devops_user`). Local socket authentication is `trust`, so the playbook does not put `POSTGRES_PASSWORD` on a command line.

Each successful run writes `devops-lab-<UTC-timestamp>.dump` to `/var/backups/devops-lab/postgres/` on DEV01 (`root:root`, directory `0700`, file `0600`) and copies it to `~/backups/devops-lab/postgres/` on AUTO01. The run fails if the AUTO01 copy is missing, a different size, or a different SHA-256 checksum. Only after both copies match does rotation keep the 7 newest dumps in those two directories. MON01 is not used. Dump files are not committed.

`postgres-backup.yml`, `postgres-restore-test.yml`, and `postgres-restore.yml` share one non-blocking `flock` on `~/backups/devops-lab/postgres/backup.lock`. The same Ansible process takes that lock, runs the tasks, and prints their results. A helper process holds the lock file open until the play releases it or the Ansible process exits, including when a task fails. If the lock is already held, the playbook exits before creating a dump or touching production. The safety dump inside a restore reuses the backup tasks and does not take the lock again. Temporary file names include a UUID. The published name stays `devops-lab-<UTC-timestamp>.dump`, and an existing file with that name is not overwritten.

Manual backup:

```bash
ansible-playbook playbooks/postgres-backup.yml
```

Restore test, using a dump path on AUTO01. This starts a temporary container and volume named `devops-lab-pg-restore-test`, restores into them, and removes only those resources. It does not write to production `lab_status`. The test compares both the row count and an MD5 checksum of the JSONB representation of `lab_status`: `jsonb_agg(jsonb_build_array(id, service_name, status, created_at) ORDER BY id)`. An empty table hashes as `[]`. The same checksum is read on production before and after the test, and the test fails if production changed. Row-change statistics are not part of the comparison. The restore test takes the same shared lock as backup and production restore.

```bash
ansible-playbook playbooks/postgres-restore-test.yml \
  -e restore_file=/absolute/path/to/backup.dump
```

Daily schedule, installed only by a separate playbook and not by `site.yml`. Run that playbook as `user`. The cron module then writes `user`'s crontab directly, without sudo. `crond` runs that entry without a login session and without systemd linger:

```bash
ansible-playbook playbooks/postgres-backup-schedule.yml
```

The entry runs at 03:15 and appends output to `~/backups/devops-lab/postgres/cron.log`.

Production restore is implemented and has not been executed against the production database. It stops `dev01-backend`, restores into the existing database, and starts the backend again. It does not run on a schedule. Without `confirm_restore=true` it makes no changes. While holding the shared lock it takes a fresh safety dump before restoring. If `pg_restore` fails, the playbook reports that command's return code and output after the backend has been started again.

```bash
ansible-playbook playbooks/postgres-restore.yml \
  -e confirm_restore=true \
  -e restore_file=/absolute/path/to/backup.dump
```

This overwrites objects in the production database. Do not run it to test the backup path.

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

