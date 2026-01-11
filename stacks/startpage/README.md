# Startpage

A simple homelab startpage that displays links extracted from caddy-docker-proxy labels on Docker containers and services.

## Architecture

This project separates **code** (git repository) from **data** (runtime files):

```
/opt/stacks/startpage/          # Code (git clone target)
├── templates/
│   └── index.html              # HTML template
├── tools/
│   ├── generate_links.py       # Link generator script
│   └── deploy.sh               # Deployment script
├── docker-compose.yml          # Stack definition
├── .env.example                # Environment variable template
└── README.md                   # This file

/srv/startpage/                 # Data (runtime files)
└── site/
    ├── index.html              # Deployed from template
    ├── links.curated.json      # User-edited links
    └── links.generated.json    # Generated from Docker labels
```

## Quick Start

### 1. Clone the Repository

```bash
# Clone to /opt/stacks (or /opt/apps if that's your convention)
sudo mkdir -p /opt/stacks
cd /opt/stacks
sudo git clone <repository-url> startpage
sudo chown -R $USER:$USER startpage
cd startpage
```

### 2. Configure Environment

```bash
# Copy and edit the environment file
cp .env.example .env

# Edit with your settings:
# - STARTPAGE_HOSTNAME: your desired hostname (e.g., bernard.home.lan)
# - CADDY_NETWORK: name of your caddy-docker-proxy network
nano .env
```

### 3. Deploy to /srv

```bash
# Run the deployment script (creates /srv/startpage and copies template)
chmod +x tools/deploy.sh
./tools/deploy.sh
```

### 4. Generate Links

```bash
# Extract links from Docker containers with caddy labels
python3 tools/generate_links.py
```

### 5. Start the Stack

```bash
# Verify the Caddy network exists
docker network ls | grep caddy

# Start the startpage container
docker compose up -d
```

### 6. Access the Startpage

Open your browser to the hostname you configured (e.g., `https://bernard.home.lan`).

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STARTPAGE_CODE_DIR` | `/opt/stacks/startpage` | Path to code directory |
| `STARTPAGE_DATA_DIR` | `/srv/startpage` | Path to data directory |
| `STARTPAGE_HOSTNAME` | `startpage.localhost` | Hostname for caddy routing |
| `CADDY_NETWORK` | `caddy` | Name of external Caddy network |
| `PUID` | `1000` | User ID for file permissions |
| `PGID` | `1000` | Group ID for file permissions |

### Adding caddy-docker-proxy Labels

For a container to appear on the startpage, it needs caddy labels:

```yaml
services:
  myapp:
    image: myapp:latest
    labels:
      # Required: caddy site address
      caddy: myapp.example.com
      caddy.reverse_proxy: "{{upstreams 8080}}"
      
      # Optional: startpage metadata
      startpage.name: "My Application"
      startpage.desc: "A cool self-hosted app"
      startpage.group: "Media"
      startpage.icon: "🎬"
```

### Curated Links

Edit `/srv/startpage/site/links.curated.json` directly, or enable FileBrowser (see below).

Example:
```json
{
  "items": [
    {
      "group": "External",
      "name": "GitHub",
      "href": "https://github.com",
      "description": "Code hosting platform",
      "icon": "🐙"
    }
  ]
}
```

## Optional: FileBrowser

To enable in-browser editing of `links.curated.json`:

1. Edit `docker-compose.yml` and uncomment the `filebrowser` service
2. Run: `docker compose up -d`
3. Access at `https://edit-<your-hostname>`
4. Default login: `admin` / `admin` (change immediately!)

## Updating

### Regenerate Links

Run this manually after deploying or updating other stacks:

```bash
python3 /opt/stacks/startpage/tools/generate_links.py
```

### Update HTML Template

If the template changes in git:

```bash
cd /opt/stacks/startpage
git pull
./tools/deploy.sh
```

## Troubleshooting

### No generated links

1. Check containers are running: `docker ps`
2. Verify caddy labels exist: `docker inspect <container> | grep -i caddy`
3. Ensure label key is exactly `caddy` or `caddy_N`

### Permission denied

```bash
# Ensure your user can run docker commands
sudo usermod -aG docker $USER
newgrp docker

# Fix /srv permissions if needed
sudo chown -R $USER:$USER /srv/startpage
```

### Network not found

```bash
# Find your Caddy network name
docker network ls | grep -i caddy

# Update .env with the correct network name
echo "CADDY_NETWORK=your_network_name" >> .env
```

## Sanity Test

```bash
# 1. Test the generator
python3 tools/generate_links.py
cat /srv/startpage/site/links.generated.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Generated: {data.get(\"generated_at\", \"unknown\")}')
print(f'Items: {len(data.get(\"items\", []))}')
"

# 2. Verify container is running
docker compose ps

# 3. Test HTTP response (from the host)
curl -s http://localhost:$(docker port startpage 80 | cut -d: -f2) | head -20
```
