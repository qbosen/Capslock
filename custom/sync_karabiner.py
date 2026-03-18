#!/usr/bin/env python3
"""Sync capslock.json rules into ~/.config/karabiner/karabiner.json.

Replaces rules with matching descriptions and appends new ones,
while preserving rules that only exist in karabiner.json.

Usage:
    python3 sync_karabiner.py [--dry-run]
"""

import json
import sys
from pathlib import Path

CAPSLOCK_JSON = Path(__file__).parent / "capslock.json"
KARABINER_JSON = Path.home() / ".config/karabiner/karabiner.json"


def sync(dry_run=False):
    with open(CAPSLOCK_JSON) as f:
        capslock_rules = json.load(f)["rules"]

    with open(KARABINER_JSON) as f:
        karabiner = json.load(f)

    profile = next(p for p in karabiner["profiles"] if p.get("selected"))
    existing_rules = profile["complex_modifications"].get("rules", [])

    # Index capslock rules by description
    capslock_by_desc = {r["description"]: r for r in capslock_rules}

    # Build merged list: update existing in-place, preserve order
    merged = []
    seen_capslock_descs = set()

    for rule in existing_rules:
        desc = rule["description"]
        if desc in capslock_by_desc:
            merged.append(capslock_by_desc[desc])
            seen_capslock_descs.add(desc)
        else:
            merged.append(rule)

    # Append new capslock rules not yet in karabiner.json
    for rule in capslock_rules:
        if rule["description"] not in seen_capslock_descs:
            merged.append(rule)

    profile["complex_modifications"]["rules"] = merged

    if dry_run:
        print("=== Dry run: merged rules ===")
        for i, r in enumerate(merged):
            src = "capslock" if r["description"] in capslock_by_desc else "karabiner"
            print(f"  [{i}] ({src}) {r['description']}")
        return

    with open(KARABINER_JSON, "w") as f:
        json.dump(karabiner, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"Synced {len(capslock_rules)} capslock rules into {KARABINER_JSON}")
    print(f"Total rules: {len(merged)}")


if __name__ == "__main__":
    sync(dry_run="--dry-run" in sys.argv)
