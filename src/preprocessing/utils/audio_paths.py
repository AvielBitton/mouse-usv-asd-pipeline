from pathlib import Path
from functools import lru_cache
from typing import List, Optional


@lru_cache(maxsize=64)
def _list_subdirs(parent: Path):
    """Return a dict of {dir_name: Path} for all subdirectories of *parent*.

    Cached so repeated lookups across thousands of recordings are cheap.
    """
    if not parent.is_dir():
        return {}
    return {d.name: d for d in parent.iterdir() if d.is_dir()}


def _normalize_for_match(s: str) -> str:
    """Normalize a string for fuzzy directory matching.

    Replaces dashes with spaces and collapses whitespace so that
    ``13128K-1A`` matches ``13128K 1A WT-WT-WT RED``.
    """
    return s.lower().replace('-', ' ')


def _find_all_dirs(parent: Path, prefix: str) -> List[Path]:
    """Find all subdirectories of *parent* whose names match *prefix*.

    Uses normalized matching (case-insensitive, dash == space) so that
    e.g. prefix ``13128K-1A`` matches folder ``13128K 1A WT-WT-WT RED``.

    Also handles folders where extra words appear between the ID and
    the pup number (e.g. ``13131J Het SUP 1A red`` for prefix ``13131J-1A``).

    Returns all matches (may be empty). Needed when a mother has multiple
    litters in separate directories (e.g. ``24277J WT`` and
    ``24277J WT - litter 2 (2.7.24)``).
    """
    subdirs = _list_subdirs(parent)
    norm_prefix = _normalize_for_match(prefix)
    results = []
    seen = set()

    # Pass 1: exact prefix match
    for dir_name, dir_path in subdirs.items():
        if _normalize_for_match(dir_name).startswith(norm_prefix):
            results.append(dir_path)
            seen.add(dir_name)

    # Pass 2: id + pup-number tokens anywhere in the folder name.
    # Handles "13131J Het SUP 1A red" when prefix is "13131J-1A".
    tokens = norm_prefix.split()
    if len(tokens) >= 2:
        id_part, num_part = tokens[0], tokens[-1]
        for dir_name, dir_path in subdirs.items():
            if dir_name in seen:
                continue
            norm_dir = _normalize_for_match(dir_name)
            if norm_dir.startswith(id_part) and f' {num_part}' in f' {norm_dir}':
                results.append(dir_path)

    return results


def build_recording_base_path(
    recordings_root: str,
    year: str,
    mother: str,
    matgen: str,
    name: str,
    pupgen: str,
    day: int,
    session: int,
    rec_num: str,
) -> Path:
    """
    Build the expected recording path WITHOUT the file extension.

    First tries the canonical underscore-separated layout:
      <root>/<year>/<mother>_<matgen>/<name>_<pupgen>/day_<day>/session<session>/<rec_num>

    If the mother or pup directory does not exist, falls back to searching
    for a directory whose name starts with the mother/name identifier
    (handles space-separated folders like ``13128K WT`` or ``13128K-1A RED``).

    When a mother has multiple litters in separate directories (e.g.
    ``24277J WT`` and ``24277J WT - litter 2``), all matching mother
    directories are searched until the pup is found.
    """
    year_dir = Path(recordings_root) / str(year)
    suffix = Path(f"day_{int(day)}") / f"session{int(session)}" / str(rec_num)

    # --- canonical underscore-separated path ---
    canonical_mother = year_dir / f"{mother}_{matgen}"
    canonical_pup = canonical_mother / f"{name}_{pupgen}"
    if canonical_pup.is_dir():
        return canonical_pup / suffix

    # --- collect candidate mother directories ---
    if canonical_mother.is_dir():
        mother_candidates = [canonical_mother]
    else:
        mother_candidates = _find_all_dirs(year_dir, mother)

    if not mother_candidates:
        return canonical_mother / f"{name}_{pupgen}" / suffix

    # --- search for pup inside each mother directory ---
    for mother_dir in mother_candidates:
        pup_dir = mother_dir / f"{name}_{pupgen}"
        if pup_dir.is_dir():
            return pup_dir / suffix

        found = _find_all_dirs(mother_dir, name)
        if found:
            return found[0] / suffix

    # Nothing found — return a plausible path (will fail on WAV lookup)
    return mother_candidates[0] / f"{name}_{pupgen}" / suffix


def resolve_wav_path(base_path: Path) -> Optional[Path]:
    """
    Resolve the actual WAV file path from a base path (no extension).

    Some datasets use '.wav' and others use '.WAV'. This helper:
      1) checks '<base>.wav'
      2) if not found, checks '<base>.WAV'
      3) returns None if neither exists
    """
    wav_lower = base_path.with_suffix(".wav")
    if wav_lower.exists():
        return wav_lower

    wav_upper = base_path.with_suffix(".WAV")
    if wav_upper.exists():
        return wav_upper

    return None
