# postgres_backup

Logical backups of `dev01-postgres`, a restore test, and a separate production restore.

Playbooks:

- `playbooks/postgres-backup.yml` holds `~/backups/devops-lab/postgres/backup.lock` in the same Ansible process
- `playbooks/postgres-restore-test.yml` compares `lab_status` row count and content checksum
- `playbooks/postgres-restore.yml` uses the same lock, then the backup tasks, and does not lock again
- `playbooks/postgres-backup-schedule.yml` installs user `user`'s crontab when run as that user

The production restore playbook is implemented. It has not been run against the production database.

Operational details are in the Ansible README.
