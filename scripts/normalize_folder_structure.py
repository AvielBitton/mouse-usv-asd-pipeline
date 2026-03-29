"""
Normalize the USV_Recordings folder structure to the canonical layout expected
by generate_metadata.py and the preprocessing pipeline.

Some data batches (e.g. 2023, 2024) arrive with non-standard folder naming:
  - Day folders:     "DAY 6", "day 6", "Day 4"   instead of "day_6", "day_4"
  - Session folders: "SESSION 1", "Session 1"     instead of "session1"
  - Channel dirs:    files inside an extra "ch1/"  sub-directory

This script renames everything to the canonical format:
  <year>/<mother>/<pup>/day_<n>/session<n>/<recording>.wav

It is idempotent: running it multiple times is safe (already-correct names
are skipped).

Usage:
    python normalize_folder_structure.py [--recordings-root USV_Recordings] [--dry-run]
"""

import argparse
import os
import re
import shutil
from pathlib import Path


# Matches "DAY 6", "day 6", "Day  4", etc. (case-insensitive, one or more spaces)
DAY_PATTERN = re.compile(r'^day\s+(\d+)$', re.IGNORECASE)

# Matches "SESSION 1", "Session  2", etc. (case-insensitive, one or more spaces)
SESSION_PATTERN = re.compile(r'^session\s+(\d+)$', re.IGNORECASE)

# Matches "ch1", "Ch1", "CH1", etc.
CHANNEL_PATTERN = re.compile(r'^ch\d+$', re.IGNORECASE)


def normalize_channel_dirs(root: Path, dry_run: bool = False) -> int:
    """Move files out of ch<N> directories into the parent, then remove ch<N>."""
    count = 0
    for dirpath, dirnames, _ in os.walk(str(root), topdown=False):
        for d in dirnames:
            if CHANNEL_PATTERN.match(d):
                ch_dir = Path(dirpath) / d
                parent = Path(dirpath)
                files = list(ch_dir.iterdir())
                if files:
                    print(f"  {'[DRY] ' if dry_run else ''}Move {len(files)} items: {ch_dir} -> {parent}")
                    if not dry_run:
                        for item in files:
                            dest = parent / item.name
                            shutil.move(str(item), str(dest))
                if not dry_run:
                    try:
                        ch_dir.rmdir()
                    except OSError:
                        pass
                count += 1
    return count


def normalize_session_dirs(root: Path, dry_run: bool = False) -> int:
    """Rename 'SESSION 1' -> 'session1', etc."""
    count = 0
    for dirpath, dirnames, _ in os.walk(str(root), topdown=False):
        for d in dirnames:
            m = SESSION_PATTERN.match(d)
            if m:
                new_name = f"session{m.group(1)}"
                if d != new_name:
                    old = Path(dirpath) / d
                    new = Path(dirpath) / new_name
                    print(f"  {'[DRY] ' if dry_run else ''}Rename: {old} -> {new}")
                    if not dry_run:
                        old.rename(new)
                    count += 1
    return count


def normalize_day_dirs(root: Path, dry_run: bool = False) -> int:
    """Rename 'DAY 6' -> 'day_6', etc."""
    count = 0
    for dirpath, dirnames, _ in os.walk(str(root), topdown=False):
        for d in dirnames:
            m = DAY_PATTERN.match(d)
            if m:
                new_name = f"day_{m.group(1)}"
                if d != new_name:
                    old = Path(dirpath) / d
                    new = Path(dirpath) / new_name
                    print(f"  {'[DRY] ' if dry_run else ''}Rename: {old} -> {new}")
                    if not dry_run:
                        old.rename(new)
                    count += 1
    return count


def normalize_year(year_dir: Path, dry_run: bool = False):
    """Apply all normalizations to a single year directory.

    Relevant for 2023+ data which arrives with non-standard naming.
    Pre-2023 data already uses the canonical layout and needs no changes.

    Idempotent: if everything is already normalized, nothing is modified
    and no output is produced.
    """
    ch = normalize_channel_dirs(year_dir, dry_run)
    sess = normalize_session_dirs(year_dir, dry_run)
    days = normalize_day_dirs(year_dir, dry_run)

    total = ch + sess + days
    if total > 0:
        print(f"Normalized {year_dir}: "
              f"ch dirs removed={ch}, sessions renamed={sess}, days renamed={days}")
    else:
        print(f"Already normalized: {year_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Normalize USV_Recordings folder structure to canonical format."
    )
    parser.add_argument(
        "--recordings-root", type=str, default="USV_Recordings",
        help="Root directory containing year folders (default: USV_Recordings)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without making changes",
    )
    args = parser.parse_args()

    root = Path(args.recordings_root)
    if not root.exists():
        print(f"Error: {root} does not exist")
        return

    for year_dir in sorted(root.iterdir()):
        if year_dir.is_dir() and year_dir.name.isdigit() and len(year_dir.name) == 4:
            normalize_year(year_dir, args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
