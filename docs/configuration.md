# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STARTPAGE_CODE_DIR` | `/opt/stacks/startpage` | Path to code directory |
| `STARTPAGE_DATA_DIR` | `/srv/startpage` | Path to data directory |
| `STARTPAGE_HOSTNAME` | `startpage.localhost` | Hostname for caddy routing |
| `CADDY_NETWORK` | `caddy` | Name of external Caddy network |
| `PUID` | `1000` | User ID for file permissions |
| `PGID` | `1000` | Group ID for file permissions |

## Adding caddy-docker-proxy Labels

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

## Curated Links

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
