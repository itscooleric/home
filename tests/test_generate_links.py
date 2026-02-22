#!/usr/bin/env python3
"""
Tests for generate_links.py using dummy site data.

These tests mock Docker CLI output to validate link extraction
logic without requiring a running Docker daemon.

Usage:
    python3 -m pytest tests/test_generate_links.py -v
    # or
    python3 tests/test_generate_links.py
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add parent directory to path so we can import the tool
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import generate_links


# --- Dummy site data: simulates docker inspect output for containers ---

DUMMY_CONTAINERS = [
    {
        "Id": "aabbccddee11223344556677889900ff",
        "Name": "/jellyfin",
        "Config": {
            "Labels": {
                "caddy": "jellyfin.home.lan",
                "caddy.reverse_proxy": "{{upstreams 8096}}",
                "startpage.name": "Jellyfin",
                "startpage.desc": "Media server",
                "startpage.group": "Media",
                "startpage.icon": "🎬"
            }
        }
    },
    {
        "Id": "bbccddee1122334455667788990011aa",
        "Name": "/portainer",
        "Config": {
            "Labels": {
                "caddy": "portainer.home.lan",
                "caddy.reverse_proxy": "{{upstreams 9000}}",
                "startpage.name": "Portainer",
                "startpage.desc": "Container management",
                "startpage.group": "System",
                "startpage.icon": "🐳"
            }
        }
    },
    {
        "Id": "ccddee112233445566778899001122bb",
        "Name": "/pihole",
        "Config": {
            "Labels": {
                "caddy": "pihole.home.lan",
                "caddy.reverse_proxy": "{{upstreams 80}}",
                "startpage.name": "Pi-hole",
                "startpage.desc": "DNS ad blocker",
                "startpage.group": "Network",
                "startpage.icon": "🛡️"
            }
        }
    },
    {
        "Id": "ddee11223344556677889900112233cc",
        "Name": "/navidrome",
        "Config": {
            "Labels": {
                "caddy": "navidrome.home.lan",
                "caddy.reverse_proxy": "{{upstreams 4533}}",
                "startpage.name": "Navidrome",
                "startpage.desc": "Music server",
                "startpage.group": "Media",
                "startpage.icon": "🎵"
            }
        }
    },
    {
        "Id": "eeff112233445566778899001122ddaa",
        "Name": "/gitea",
        "Config": {
            "Labels": {
                "caddy": "git.home.lan",
                "caddy.reverse_proxy": "{{upstreams 3000}}"
            }
        }
    },
]

# Container with no caddy labels (should be skipped)
DUMMY_NO_CADDY = [
    {
        "Id": "ff00112233445566778899aabbccddee",
        "Name": "/redis",
        "Config": {
            "Labels": {
                "com.docker.compose.service": "redis"
            }
        }
    }
]

# Container with a snippet definition (should be skipped)
DUMMY_SNIPPET = [
    {
        "Id": "0011223344556677889900aabbccddee",
        "Name": "/caddy",
        "Config": {
            "Labels": {
                "caddy": "(tls_policy)",
                "caddy.tls": "internal"
            }
        }
    }
]


class TestExtractSiteAddress(unittest.TestCase):
    """Test the extract_site_address function."""

    def test_valid_address(self):
        self.assertEqual(generate_links.extract_site_address("app.home.lan"), "app.home.lan")

    def test_address_with_scheme(self):
        self.assertEqual(generate_links.extract_site_address("https://app.home.lan"), "https://app.home.lan")

    def test_empty_string(self):
        self.assertIsNone(generate_links.extract_site_address(""))

    def test_whitespace(self):
        self.assertIsNone(generate_links.extract_site_address("   "))

    def test_snippet_definition(self):
        self.assertIsNone(generate_links.extract_site_address("(tls_policy)"))

    def test_stripped_whitespace(self):
        self.assertEqual(generate_links.extract_site_address("  app.home.lan  "), "app.home.lan")


class TestNormalizeHref(unittest.TestCase):
    """Test the normalize_href function."""

    def test_plain_hostname(self):
        self.assertEqual(generate_links.normalize_href("app.home.lan"), "https://app.home.lan")

    def test_already_https(self):
        self.assertEqual(generate_links.normalize_href("https://app.home.lan"), "https://app.home.lan")

    def test_http_scheme(self):
        self.assertEqual(generate_links.normalize_href("http://app.home.lan"), "http://app.home.lan")


class TestExtractLinksFromLabels(unittest.TestCase):
    """Test extract_links_from_labels with dummy site data."""

    def test_full_metadata(self):
        """Container with all startpage labels should produce a complete link."""
        labels = DUMMY_CONTAINERS[0]["Config"]["Labels"]
        links = generate_links.extract_links_from_labels(
            labels, "container", "aabbccddee11", "jellyfin"
        )
        self.assertEqual(len(links), 1)
        link = links[0]
        self.assertEqual(link["name"], "Jellyfin")
        self.assertEqual(link["href"], "https://jellyfin.home.lan")
        self.assertEqual(link["group"], "Media")
        self.assertEqual(link["icon"], "🎬")
        self.assertEqual(link["description"], "Media server")

    def test_minimal_labels(self):
        """Container with only caddy label should use defaults."""
        labels = DUMMY_CONTAINERS[4]["Config"]["Labels"]
        links = generate_links.extract_links_from_labels(
            labels, "container", "eeff11223344", "gitea"
        )
        self.assertEqual(len(links), 1)
        link = links[0]
        self.assertEqual(link["name"], "gitea")
        self.assertEqual(link["group"], "Services")
        self.assertEqual(link["href"], "https://git.home.lan")
        self.assertNotIn("icon", link)

    def test_no_caddy_labels(self):
        """Container without caddy labels should produce no links."""
        labels = DUMMY_NO_CADDY[0]["Config"]["Labels"]
        links = generate_links.extract_links_from_labels(
            labels, "container", "ff0011223344", "redis"
        )
        self.assertEqual(len(links), 0)

    def test_snippet_label_skipped(self):
        """Caddy snippet definitions should be skipped."""
        labels = DUMMY_SNIPPET[0]["Config"]["Labels"]
        links = generate_links.extract_links_from_labels(
            labels, "container", "001122334455", "caddy"
        )
        self.assertEqual(len(links), 0)


class TestDeduplicateLinks(unittest.TestCase):
    """Test deduplication logic."""

    def test_no_duplicates(self):
        links = [
            {"href": "https://a.home.lan", "name": "A"},
            {"href": "https://b.home.lan", "name": "B"},
        ]
        result = generate_links.deduplicate_links(links)
        self.assertEqual(len(result), 2)

    def test_with_duplicates(self):
        links = [
            {"href": "https://a.home.lan", "name": "A"},
            {"href": "https://a.home.lan", "name": "A duplicate"},
            {"href": "https://b.home.lan", "name": "B"},
        ]
        result = generate_links.deduplicate_links(links)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "A")

    def test_empty_list(self):
        self.assertEqual(generate_links.deduplicate_links([]), [])


class TestGroupItems(unittest.TestCase):
    """Test the grouping helper used by the HTML template (tested via generate_links)."""

    def test_groups_from_dummy_sites(self):
        """Verify dummy sites group correctly after extraction."""
        all_links = []
        for container in DUMMY_CONTAINERS:
            cid = container["Id"][:12]
            cname = container["Name"].lstrip("/")
            labels = container["Config"]["Labels"]
            all_links.extend(
                generate_links.extract_links_from_labels(labels, "container", cid, cname)
            )

        groups = {}
        for link in all_links:
            g = link.get("group", "Ungrouped")
            groups.setdefault(g, []).append(link)

        self.assertIn("Media", groups)
        self.assertIn("System", groups)
        self.assertIn("Network", groups)
        self.assertIn("Services", groups)
        self.assertEqual(len(groups["Media"]), 2)
        self.assertEqual(len(groups["System"]), 1)
        self.assertEqual(len(groups["Network"]), 1)
        self.assertEqual(len(groups["Services"]), 1)


class TestGenerateLinksJson(unittest.TestCase):
    """Test full JSON output generation with dummy sites."""

    @patch("generate_links.run_docker_command")
    def test_output_with_dummy_sites(self, mock_run):
        """Generate links file using mocked Docker output with dummy sites."""
        container_ids = [c["Id"][:12] for c in DUMMY_CONTAINERS]

        def side_effect(args):
            if args == ["ps", "-q"]:
                return (0, "\n".join(container_ids), "")
            if args[0] == "inspect":
                return (0, json.dumps(DUMMY_CONTAINERS), "")
            if args == ["info", "--format", "{{.Swarm.LocalNodeState}}"]:
                return (0, "inactive", "")
            return (1, "", "unknown command")

        mock_run.side_effect = side_effect

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            outpath = f.name

        try:
            generate_links.generate_links_json(outpath)

            with open(outpath, "r") as f:
                data = json.load(f)

            self.assertIn("generated_at", data)
            self.assertIn("items", data)
            self.assertEqual(len(data["items"]), 5)

            names = {item["name"] for item in data["items"]}
            self.assertIn("Jellyfin", names)
            self.assertIn("Portainer", names)
            self.assertIn("Pi-hole", names)
            self.assertIn("Navidrome", names)
            self.assertIn("gitea", names)

            hrefs = {item["href"] for item in data["items"]}
            self.assertIn("https://jellyfin.home.lan", hrefs)
            self.assertIn("https://portainer.home.lan", hrefs)
            self.assertIn("https://pihole.home.lan", hrefs)
            self.assertIn("https://navidrome.home.lan", hrefs)
            self.assertIn("https://git.home.lan", hrefs)

            # Verify sorted by group then name
            items = data["items"]
            sort_keys = [(i["group"], i["name"]) for i in items]
            self.assertEqual(sort_keys, sorted(sort_keys))
        finally:
            os.unlink(outpath)

    @patch("generate_links.run_docker_command")
    def test_output_no_containers(self, mock_run):
        """Empty container list should produce valid JSON with no items."""
        def side_effect(args):
            if args == ["ps", "-q"]:
                return (0, "", "")
            if args == ["info", "--format", "{{.Swarm.LocalNodeState}}"]:
                return (0, "inactive", "")
            return (1, "", "unknown command")

        mock_run.side_effect = side_effect

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            outpath = f.name

        try:
            generate_links.generate_links_json(outpath)

            with open(outpath, "r") as f:
                data = json.load(f)

            self.assertEqual(len(data["items"]), 0)
            self.assertIn("generated_at", data)
        finally:
            os.unlink(outpath)


class TestCaddyKeyPattern(unittest.TestCase):
    """Test the CADDY_KEY_PATTERN regex."""

    def test_matches(self):
        self.assertIsNotNone(generate_links.CADDY_KEY_PATTERN.match("caddy"))
        self.assertIsNotNone(generate_links.CADDY_KEY_PATTERN.match("caddy_0"))
        self.assertIsNotNone(generate_links.CADDY_KEY_PATTERN.match("caddy_1"))
        self.assertIsNotNone(generate_links.CADDY_KEY_PATTERN.match("caddy_99"))

    def test_non_matches(self):
        self.assertIsNone(generate_links.CADDY_KEY_PATTERN.match("caddy.reverse_proxy"))
        self.assertIsNone(generate_links.CADDY_KEY_PATTERN.match("startpage.name"))
        self.assertIsNone(generate_links.CADDY_KEY_PATTERN.match("com.docker"))
        self.assertIsNone(generate_links.CADDY_KEY_PATTERN.match("caddy_"))


if __name__ == "__main__":
    unittest.main()
