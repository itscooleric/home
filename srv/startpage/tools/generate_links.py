#!/usr/bin/env python3
"""
generate_links.py - Extract site addresses from caddy-docker-proxy labels.

This script inspects Docker containers (and optionally Swarm services) to find
caddy-docker-proxy labels that define site addresses. It generates a JSON file
of links suitable for a startpage.

Usage:
    python3 tools/generate_links.py --out site/links.generated.json

Requirements:
    - Python 3 standard library only (no external dependencies)
    - Docker CLI available in PATH
    - Access to Docker socket (via docker command)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any


# Regex to match caddy label keys (caddy, caddy_0, caddy_1, etc.)
CADDY_KEY_PATTERN = re.compile(r"^caddy(_\d+)?$")


def run_docker_command(args: list[str]) -> tuple[int, str, str]:
    """
    Run a docker command and return (returncode, stdout, stderr).

    Args:
        args: List of command arguments (without 'docker' prefix)

    Returns:
        Tuple of (return_code, stdout_text, stderr_text)
    """
    try:
        result = subprocess.run(
            ["docker"] + args,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "docker: command not found"
    except subprocess.TimeoutExpired:
        return 1, "", "docker: command timed out"


def is_swarm_active() -> bool:
    """
    Check if Docker Swarm mode is active.

    Returns:
        True if Swarm is active, False otherwise.
    """
    code, stdout, stderr = run_docker_command(["info", "--format", "{{.Swarm.LocalNodeState}}"])
    if code != 0:
        return False
    return stdout.strip().lower() == "active"


def get_container_ids() -> list[str]:
    """
    Get list of running container IDs.

    Returns:
        List of container ID strings.

    Raises:
        RuntimeError: If docker command fails.
    """
    code, stdout, stderr = run_docker_command(["ps", "-q"])
    if code != 0:
        raise RuntimeError(f"Failed to list containers: {stderr.strip()}")
    return [cid.strip() for cid in stdout.strip().split("\n") if cid.strip()]


def get_service_ids() -> list[str]:
    """
    Get list of Swarm service IDs.

    Returns:
        List of service ID strings.

    Raises:
        RuntimeError: If docker command fails.
    """
    code, stdout, stderr = run_docker_command(["service", "ls", "-q"])
    if code != 0:
        raise RuntimeError(f"Failed to list services: {stderr.strip()}")
    return [sid.strip() for sid in stdout.strip().split("\n") if sid.strip()]


def inspect_containers(container_ids: list[str]) -> list[dict[str, Any]]:
    """
    Inspect containers and return their JSON data.

    Args:
        container_ids: List of container IDs to inspect.

    Returns:
        List of container inspection dictionaries.

    Raises:
        RuntimeError: If docker command fails.
    """
    if not container_ids:
        return []

    code, stdout, stderr = run_docker_command(["inspect"] + container_ids)
    if code != 0:
        raise RuntimeError(f"Failed to inspect containers: {stderr.strip()}")

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse container inspection: {e}")


def inspect_services(service_ids: list[str]) -> list[dict[str, Any]]:
    """
    Inspect Swarm services and return their JSON data.

    Args:
        service_ids: List of service IDs to inspect.

    Returns:
        List of service inspection dictionaries.

    Raises:
        RuntimeError: If docker command fails.
    """
    if not service_ids:
        return []

    code, stdout, stderr = run_docker_command(["service", "inspect"] + service_ids)
    if code != 0:
        raise RuntimeError(f"Failed to inspect services: {stderr.strip()}")

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse service inspection: {e}")


def extract_site_address(value: str) -> str | None:
    """
    Extract a valid site address from a caddy label value.

    Args:
        value: The label value to check.

    Returns:
        The site address if valid, None if it should be skipped.
    """
    value = value.strip()

    # Skip empty values
    if not value:
        return None

    # Skip snippet definitions (values starting with "(")
    if value.startswith("("):
        return None

    return value


def normalize_href(site_address: str) -> str:
    """
    Normalize a site address to a full URL.

    Args:
        site_address: The site address (may or may not have scheme).

    Returns:
        A full URL with scheme.
    """
    # If already has a scheme, use as-is
    if "://" in site_address:
        return site_address

    # Default to https://
    return f"https://{site_address}"


def extract_links_from_labels(
    labels: dict[str, str],
    source_kind: str,
    source_id: str,
    source_name: str
) -> list[dict[str, Any]]:
    """
    Extract link entries from a set of labels.

    Args:
        labels: Dictionary of Docker labels.
        source_kind: "container" or "service".
        source_id: The container/service ID.
        source_name: The container/service name.

    Returns:
        List of link dictionaries.
    """
    links = []

    # Get optional startpage metadata labels
    startpage_name = labels.get("startpage.name", "")
    startpage_desc = labels.get("startpage.desc", "")
    startpage_group = labels.get("startpage.group", "")
    startpage_icon = labels.get("startpage.icon", "")

    for key, value in labels.items():
        # Check if this is a caddy site block label
        if not CADDY_KEY_PATTERN.match(key):
            continue

        site_address = extract_site_address(value)
        if site_address is None:
            continue

        href = normalize_href(site_address)

        link = {
            "group": startpage_group if startpage_group else "Services",
            "name": startpage_name if startpage_name else source_name,
            "href": href,
            "description": startpage_desc,
            "source": {
                "kind": source_kind,
                "id": source_id,
                "name": source_name
            }
        }

        # Only include icon if present
        if startpage_icon:
            link["icon"] = startpage_icon

        links.append(link)

    return links


def collect_container_links() -> list[dict[str, Any]]:
    """
    Collect links from all running Docker containers.

    Returns:
        List of link dictionaries.
    """
    links = []

    container_ids = get_container_ids()
    if not container_ids:
        return links

    containers = inspect_containers(container_ids)

    for container in containers:
        container_id = container.get("Id", "")[:12]
        container_name = container.get("Name", "").lstrip("/")

        # Get labels from Config
        config = container.get("Config", {})
        labels = config.get("Labels", {}) or {}

        container_links = extract_links_from_labels(
            labels,
            source_kind="container",
            source_id=container_id,
            source_name=container_name
        )
        links.extend(container_links)

    return links


def collect_service_links() -> list[dict[str, Any]]:
    """
    Collect links from all Swarm services.

    Returns:
        List of link dictionaries.
    """
    links = []

    if not is_swarm_active():
        return links

    service_ids = get_service_ids()
    if not service_ids:
        return links

    services = inspect_services(service_ids)

    for service in services:
        service_id = service.get("ID", "")[:12]

        # Get service name from Spec
        spec = service.get("Spec", {})
        service_name = spec.get("Name", "")

        # Get labels from Spec.Labels (service-level labels)
        labels = spec.get("Labels", {}) or {}

        service_links = extract_links_from_labels(
            labels,
            source_kind="service",
            source_id=service_id,
            source_name=service_name
        )
        links.extend(service_links)

    return links


def deduplicate_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Deduplicate links by href, keeping the first occurrence.

    Args:
        links: List of link dictionaries.

    Returns:
        Deduplicated list of link dictionaries.
    """
    seen_hrefs = set()
    unique_links = []

    for link in links:
        href = link.get("href", "")
        if href not in seen_hrefs:
            seen_hrefs.add(href)
            unique_links.append(link)

    return unique_links


def generate_links_json(output_path: str) -> None:
    """
    Generate the links.generated.json file.

    Args:
        output_path: Path to write the JSON file.

    Raises:
        RuntimeError: If there are errors collecting links.
    """
    print("Collecting links from Docker containers...", file=sys.stderr)
    links = collect_container_links()
    print(f"  Found {len(links)} link(s) from containers", file=sys.stderr)

    print("Collecting links from Swarm services...", file=sys.stderr)
    service_links = collect_service_links()
    print(f"  Found {len(service_links)} link(s) from services", file=sys.stderr)

    links.extend(service_links)

    # Deduplicate by href
    original_count = len(links)
    links = deduplicate_links(links)
    if original_count != len(links):
        print(f"  Deduplicated: {original_count} -> {len(links)} links", file=sys.stderr)

    # Sort by group then name for consistent output
    links.sort(key=lambda x: (x.get("group", ""), x.get("name", "")))

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": links
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {len(links)} link(s) to {output_path}", file=sys.stderr)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate links.json from caddy-docker-proxy labels"
    )
    parser.add_argument(
        "--out",
        default="site/links.generated.json",
        help="Output path for generated JSON (default: site/links.generated.json)"
    )

    args = parser.parse_args()

    try:
        generate_links_json(args.out)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
