# Startpage Tools

This directory contains tools for managing the Bernard startpage.

## generate_links.py

A Python script that extracts site addresses from caddy-docker-proxy labels on Docker containers and Swarm services, and generates a JSON file for the startpage.

### Requirements

- Python 3.10+ (uses type hint union syntax)
- Docker CLI installed and accessible
- Access to Docker socket (user must be in `docker` group or run as root)

No external Python dependencies required (uses only the standard library).

### Usage

```bash
# From the /srv/startpage directory
python3 tools/generate_links.py --out site/links.generated.json
```

### How It Works

1. Lists all running Docker containers using `docker ps -q`
2. Inspects each container to get labels using `docker inspect`
3. If Docker Swarm is active, also inspects Swarm services
4. Extracts site addresses from caddy-docker-proxy labels:
   - Labels with key `caddy` or `caddy_N` (where N is a number)
   - Values that don't start with `(` (which indicate snippets)
5. Normalizes URLs (adds `https://` if no scheme present)
6. Reads optional metadata from additional labels:
   - `startpage.name`: Display name (default: container/service name)
   - `startpage.desc`: Description text
   - `startpage.group`: Grouping category (default: "Services")
   - `startpage.icon`: Optional icon (emoji or text)
7. Deduplicates links by URL
8. Writes the result to `links.generated.json`

### Example Docker Compose Labels

```yaml
services:
  myapp:
    image: myapp:latest
    labels:
      # caddy-docker-proxy labels (required for site block)
      caddy: myapp.example.com
      caddy.reverse_proxy: "{{upstreams 8080}}"
      
      # Optional startpage metadata
      startpage.name: "My Application"
      startpage.desc: "A cool self-hosted app"
      startpage.group: "Media"
      startpage.icon: "🎬"
```

### Output Format

The generated `links.generated.json` file has this structure:

```json
{
  "generated_at": "2024-01-15T10:30:00+00:00",
  "items": [
    {
      "group": "Media",
      "name": "My Application",
      "href": "https://myapp.example.com",
      "description": "A cool self-hosted app",
      "icon": "🎬",
      "source": {
        "kind": "container",
        "id": "abc123def456",
        "name": "myapp"
      }
    }
  ]
}
```

## Serving the Startpage

The startpage is a static HTML file that can be served by any web server. Since you're already using caddy-docker-proxy, here's an example service definition:

### Docker Compose Example

```yaml
services:
  startpage:
    image: caddy:alpine
    volumes:
      - /srv/startpage/site:/srv:ro
    labels:
      caddy: bernard.example.com
      caddy.root: "* /srv"
      caddy.file_server: ""
    networks:
      - caddy
```

Or if you want to serve it from your existing Caddy instance, add a site block:

```caddyfile
bernard.example.com {
    root * /srv/startpage/site
    file_server
}
```

## Sanity Test

After setting up the startpage, run these tests to verify everything works:

### 1. Test the Generator

```bash
cd /srv/startpage

# Run the generator
python3 tools/generate_links.py --out site/links.generated.json

# Check the output file exists and has items
cat site/links.generated.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Generated at: {data.get(\"generated_at\", \"unknown\")}')
print(f'Item count: {len(data.get(\"items\", []))}')
for item in data.get('items', []):
    print(f'  - {item[\"name\"]}: {item[\"href\"]}')
"
```

### 2. Test the HTML Page

```bash
# Start a simple HTTP server for testing (optional, if not behind Caddy)
cd /srv/startpage/site
python3 -m http.server 8080

# Open in browser: http://localhost:8080
# OR if behind Caddy: https://bernard.example.com
```

Verify:
- ✅ "Curated" section shows manually configured links
- ✅ "Generated" section shows links from Docker containers
- ✅ Links are grouped correctly
- ✅ Clicking links opens in new tabs

### 3. Verify Label Detection

```bash
# Find containers with caddy labels
docker ps -q | xargs -I {} docker inspect {} --format '{{.Name}}: {{json .Config.Labels}}' | grep -i caddy
```

## Troubleshooting

### No links generated

1. Check that containers are running: `docker ps`
2. Verify containers have caddy labels: `docker inspect <container_id> | grep -i caddy`
3. Ensure label key is exactly `caddy` or `caddy_N` (not `caddy.something`)

### Permission denied

Ensure your user has access to the Docker socket:
```bash
sudo usermod -aG docker $USER
# Log out and back in, or run: newgrp docker
```

### Script errors

Run with verbose output:
```bash
python3 tools/generate_links.py --out site/links.generated.json 2>&1
```
