# DevOps Home Lab

Personal DevOps learning and portfolio project.

## Infrastructure

- DEV01: Debian 13
- Virtualization: VMware Workstation 17
- Network: Isolated Host-Only Network
- Docker Engine
- Docker Compose

## Current Services

### Nginx

- Custom Docker image
- Base image: nginx:stable
- Custom HTML website
- Port mapping: 8080:80
- Restart policy: unless-stopped

## Project Structure

```text
devops-lab/
├── compose.yaml
├── README.md
└── nginx/
    ├── Dockerfile
    └── html/
        └── index.html
