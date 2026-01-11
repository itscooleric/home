# Home

Homelab startpage for Bernard that extracts site addresses from caddy-docker-proxy labels.

## Repository Structure

```
stacks/startpage/           # Startpage application
├── templates/              # HTML templates
├── tools/                  # Scripts (generator, deploy)
├── docker-compose.yml      # Docker stack definition
├── .env.example            # Configuration template
└── README.md               # Detailed documentation
```

## Quick Start

```bash
# Clone to /opt/stacks
sudo mkdir -p /opt/stacks
cd /opt/stacks
sudo git clone <repository-url> startpage
cd startpage

# Configure and deploy
cp .env.example .env
nano .env  # Set your hostname and network
chmod +x tools/deploy.sh
./tools/deploy.sh

# Generate links and start
python3 tools/generate_links.py
docker compose up -d
```

## Directory Convention

- **Code**: `/opt/stacks/startpage/` (git repository)
- **Data**: `/srv/startpage/` (runtime files, generated output)

See [stacks/startpage/README.md](stacks/startpage/README.md) for full documentation.
