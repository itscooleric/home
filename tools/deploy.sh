#!/bin/bash
#
# deploy.sh - Deploy startpage to /srv
#
# This script:
# 1. Creates the data directory structure under /srv/startpage
# 2. Copies the HTML template to the site directory
# 3. Creates placeholder JSON files if they don't exist
# 4. Sets appropriate permissions
#
# Usage:
#   ./tools/deploy.sh
#
# Environment variables:
#   STARTPAGE_CODE_DIR - Path to code directory (default: script's parent dir)
#   STARTPAGE_DATA_DIR - Path to data directory (default: /srv/startpage)
#

set -euo pipefail

# Determine directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE_DIR="${STARTPAGE_CODE_DIR:-$(dirname "$SCRIPT_DIR")}"
DATA_DIR="${STARTPAGE_DATA_DIR:-/srv/startpage}"

echo "Deploying startpage..."
echo "  Code directory: $CODE_DIR"
echo "  Data directory: $DATA_DIR"

# Create data directory structure
echo "Creating directory structure..."
mkdir -p "$DATA_DIR/site"
mkdir -p "$DATA_DIR/filebrowser"
mkdir -p "$DATA_DIR/logs"

# Copy HTML template
echo "Copying index.html template..."
cp "$CODE_DIR/templates/index.html" "$DATA_DIR/site/index.html"

# Create links.curated.json if it doesn't exist
if [ ! -f "$DATA_DIR/site/links.curated.json" ]; then
    echo "Creating default links.curated.json..."
    cat > "$DATA_DIR/site/links.curated.json" << 'EOF'
{
  "description": "Manually curated links for the startpage. Edit this file to add your own links.",
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
EOF
fi

# Create links.generated.json if it doesn't exist
if [ ! -f "$DATA_DIR/site/links.generated.json" ]; then
    echo "Creating placeholder links.generated.json..."
    cat > "$DATA_DIR/site/links.generated.json" << 'EOF'
{
  "generated_at": "1970-01-01T00:00:00+00:00",
  "items": []
}
EOF
fi

# Create filebrowser config if it doesn't exist
if [ ! -f "$DATA_DIR/filebrowser/config.json" ]; then
    echo "Creating filebrowser config..."
    cat > "$DATA_DIR/filebrowser/config.json" << 'EOF'
{
  "port": 80,
  "baseURL": "",
  "address": "",
  "log": "stdout",
  "database": "/database.db",
  "root": "/srv"
}
EOF
    touch "$DATA_DIR/filebrowser/database.db"
fi

# Set permissions (readable by all, writable by owner)
echo "Setting permissions..."
chmod 755 "$DATA_DIR"
chmod 755 "$DATA_DIR/site"
chmod 644 "$DATA_DIR/site/"*.html 2>/dev/null || true
chmod 644 "$DATA_DIR/site/"*.json 2>/dev/null || true

echo ""
echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Run the link generator:"
echo "     python3 $CODE_DIR/tools/generate_links.py --out $DATA_DIR/site/links.generated.json"
echo ""
echo "  2. Start the stack:"
echo "     cd $CODE_DIR && docker compose up -d"
echo ""
echo "  3. Access the startpage at your configured hostname"
