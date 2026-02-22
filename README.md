# Startpage

A simple homelab startpage that displays links extracted from caddy-docker-proxy labels on Docker containers and services.

![Startpage Screenshot](https://github.com/user-attachments/assets/4173c33c-6ba3-419d-8e39-606d2bdf66f1)

## Quick Start

```bash
# 1. Clone and configure
git clone <repository-url> startpage && cd startpage
cp .env.example .env
nano .env  # set STARTPAGE_HOSTNAME and CADDY_NETWORK

# 2. Deploy and generate links
chmod +x tools/deploy.sh && ./tools/deploy.sh
python3 tools/generate_links.py

# 3. Start
docker compose up -d
```

Open your browser to the hostname you configured (e.g., `https://bernard.home.lan`).

## Updating

```bash
cd /opt/stacks/startpage
git pull
./tools/deploy.sh                # re-deploy template
python3 tools/generate_links.py  # refresh links
```

## Further Reading

- [Configuration](docs/configuration.md) — environment variables, caddy labels, curated links, FileBrowser
- [Troubleshooting](docs/troubleshooting.md) — common issues and sanity tests
