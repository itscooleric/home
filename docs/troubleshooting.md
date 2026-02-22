# Troubleshooting

## No Generated Links

1. Check containers are running: `docker ps`
2. Verify caddy labels exist: `docker inspect <container> | grep -i caddy`
3. Ensure label key is exactly `caddy` or `caddy_N`

## Permission Denied

```bash
# Ensure your user can run docker commands
sudo usermod -aG docker $USER
newgrp docker

# Fix /srv permissions if needed
sudo chown -R $USER:$USER /srv/startpage
```

## Network Not Found

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
