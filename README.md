# home

```text

  ██╗  ██╗ ██████╗ ███╗   ███╗███████╗
  ██║  ██║██╔═══██╗████╗ ████║██╔════╝
  ███████║██║   ██║██╔████╔██║█████╗
  ██╔══██║██║   ██║██║╚██╔╝██║██╔══╝
  ██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗
  ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝

  homelab startpage — auto-generated from Docker labels
  ──────────────────────────────────────────────────────

  caddy-docker-proxy labels
          │
          ▼
  generate_links.py ──► links.json
          │
          ▼
  templates/index.html ──► startpage

```

Self-hosted homelab startpage that auto-discovers services by reading [caddy-docker-proxy](https://github.com/lucaslorentz/caddy-docker-proxy) labels from running Docker containers. No manual link management — deploy a container with the right labels and it appears on your dashboard.

![Startpage Screenshot](https://github.com/user-attachments/assets/4173c33c-6ba3-419d-8e39-606d2bdf66f1)

## Quick Start

```bash
git clone https://github.com/itscooleric/home.git && cd home
cp .env.example .env
# edit .env — set STARTPAGE_HOSTNAME and CADDY_NETWORK
./tools/deploy.sh
python3 tools/generate_links.py
docker compose up -d
```

Open `https://<your-hostname>` in a browser.

## How it works

`generate_links.py` reads caddy-docker-proxy labels from running containers and writes `links.json`. The HTML template renders that file as a clean dashboard. Re-run the script after adding or removing services.

## Updating

```bash
git pull && ./tools/deploy.sh && python3 tools/generate_links.py
```

## Further Reading

- [Configuration](docs/configuration.md) — env vars, caddy labels, curated links
- [Troubleshooting](docs/troubleshooting.md) — common issues and fixes
