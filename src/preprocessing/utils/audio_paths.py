import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Pup identity normalization (ported from segmentation-app)
#
# These helpers recognize colour words, genotype suffixes, supplement markers
# and parenthetical notes inside pup labels so Excel rows like
# ``24277J-2A (J)`` and disk folders like ``24277J-2A (BLUE) WT-WT-WT`` map
# to the same identity key, supporting fuzzy joins between Excel metadata
# and the recording filesystem.
# ---------------------------------------------------------------------------

# Suffix after the last "_" treated as a genotype label
# (Excel often shows "17450L", folder "17450L_WT").
_GENOTYPE_SUFFIX_RE = re.compile(
    r"^(WT|HT|HOM|HET|KO|KI|\+\/\+|\+\/-|-\/-|\+/-|-/\+)$",
    re.I,
)

# A token that is ONLY one or more colour words, e.g. "GREEN-RED" or "RED".
# We need to match the compound form first so naive `\bRED\b` stripping does
# not leave dangling "GREEN-".
_COLOR_COMPOUND_SEGMENT_RE = re.compile(
    r"^(?:RED|BLUE|GREEN|YELLOW|BLACK|WHITE|PURPLE|PINK|ORANGE|VIOLET|CYAN|MAGENTA)"
    r"(?:[-_]?(?:RED|BLUE|GREEN|YELLOW|BLACK|WHITE|PURPLE|PINK|ORANGE|VIOLET|CYAN|MAGENTA))*$",
    re.I,
)

# Folder shorthand for colours (e.g. ``BLU`` instead of ``BLUE``).
_COLOR_NAME_SHORTHAND: Set[str] = frozenset(
    {
        "blu",
        "grn",
        "org",
        "orn",
        "pnk",
        "ylw",
        "blk",
        "wht",
        "gry",
        "brn",
        "pur",
        "vio",
        "cya",
        "mag",
        "tan",
        "lav",
    }
)


def _strip_pup_parenthetical_notes(s: str) -> str:
    """Drop any ``(...)`` notes from a pup label."""
    return re.sub(r"\s*\([^)]*\)", "", str(s))


def _normalize_pup_label_separators(s: str) -> str:
    """Map ASCII / Unicode hyphens to ``-`` so tokenization stays consistent."""
    t = unicodedata.normalize("NFKC", str(s))
    for ch in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        t = t.replace(ch, "-")
    return t


def _pup_label_tokens(label: str) -> List[str]:
    """Underscore-separated tokens after removing parenthetical notes and SUPP markers."""
    s = _normalize_pup_label_separators(_strip_pup_parenthetical_notes(str(label).strip()))
    s = re.sub(r"\bSUPP?\b", "", s, flags=re.I)
    s = re.sub(r"\s+", "_", s)
    # Unify hyphen only when it precedes a digit (14164P-1C ↔ 14164P_1C); keep
    # G-R / GREEN-RED as single tokens.
    s = re.sub(r"-(?=\d)", "_", s)
    s = s.strip("_-")
    return [p for p in s.split("_") if p]


def _is_trailing_color_or_compound_token(tok: str) -> bool:
    return bool(_COLOR_COMPOUND_SEGMENT_RE.match(tok.strip()))


def _is_trailing_color_shorthand_token(tok: str) -> bool:
    t = str(tok).strip().lower()
    return bool(t) and t in _COLOR_NAME_SHORTHAND


def _is_trailing_genotype_token(tok: str) -> bool:
    return bool(_GENOTYPE_SUFFIX_RE.match(tok.strip()))


def _is_trailing_color_abbrev_token(tok: str) -> bool:
    """
    Lab shorthand for compound colours like ``G-R`` ≈ ``GREEN-RED``.

    Limited to single-letter tokens separated by ``-`` or ``/`` so we do not
    accidentally strip real ids that happen to contain digits.
    """
    t = tok.strip()
    if len(t) < 3 or len(t) > 16:
        return False
    parts = re.split(r"[-/]", t)
    if len(parts) < 2:
        return False
    return all(len(p) == 1 and p.isalpha() for p in parts)


def strip_trailing_pup_decorator_tokens(parts: List[str]) -> List[str]:
    """Drop trailing colour / compound-colour / genotype-only segments (right to left)."""
    out = list(parts)
    while out:
        last = out[-1].strip()
        if (
            _is_trailing_color_or_compound_token(last)
            or _is_trailing_color_abbrev_token(last)
            or _is_trailing_color_shorthand_token(last)
        ):
            out.pop()
            continue
        if _is_trailing_genotype_token(last):
            out.pop()
            continue
        low = last.lower()
        if low in {"sup", "supp", "i"}:
            out.pop()
            continue
        break
    return out


# Pup/cage slot after the mouse-line id, e.g. ``1A`` in ``13131J Het SUP 1A red`` → ``13131J-1A``.
_PUP_SLOT_TOKEN_RE = re.compile(r"^\d+[A-Za-z]+$")


def _collapse_mouse_line_and_slot_tokens(parts: List[str]) -> List[str]:
    """
    Collapse mouse-line + slot tokens when decorators left genotype/markers between them.

    If the last token looks like a numeric+letter cage id (``1A``, ``4A``, ``12B``)
    and the first token is a normal mouse-line id, drop everything in between
    (e.g. ``Het``, ``SUP``).
    """
    if len(parts) < 3:
        return parts
    first = parts[0].strip()
    last = parts[-1].strip()
    if not first or not last:
        return parts
    if not _PUP_SLOT_TOKEN_RE.fullmatch(last):
        return parts
    if not (re.search(r"\d", first) and re.search(r"[A-Za-z]", first)):
        return parts
    if _GENOTYPE_SUFFIX_RE.match(first):
        return parts
    return [first, last]


def canonical_pup_display_name(label: str) -> str:
    """
    Short pup id for display / output: strip colours (incl. GREEN-RED), genotypes, notes.

    Examples:
      - ``22731O_1A_BLUE`` → ``22731O_1A``
      - ``22731O_4A_GREEN-RED`` → ``22731O_4A``
      - ``22742K_4A_G-R`` (Excel) aligns with folder ``…_GREEN-RED`` → ``22742K_4A``
      - ``14164P-1C (RED)`` → ``14164P_1C`` (underscore — same identity key as the hyphen form)
      - ``13131J Het SUP 1A red`` → ``13131J_1A`` (matches Excel ``13131J-1A`` via :func:`pup_identity_key`)
      - ``13131J Het SUP 2A BLU`` → ``13131J_2A`` (shorthand ``BLU`` stripped like ``BLUE``)
    """
    parts = strip_trailing_pup_decorator_tokens(_pup_label_tokens(label))
    parts = _collapse_mouse_line_and_slot_tokens(parts)
    if not parts:
        t = _strip_pup_parenthetical_notes(str(label).strip())
        t = re.sub(r"\s+", " ", t).strip(" -_")
        return t
    base = "_".join(parts)
    base = re.sub(r"[-_]+$", "", base)
    return base.strip(" -_") or str(label).strip()


def _pup_identity_key_core(base: str) -> str:
    """Normalize an already-canonical pup base (no extra :func:`canonical_pup_display_name`)."""
    s = _normalize_pup_label_separators(str(base).strip())
    if not s:
        return ""
    s = s.replace("-", "_")
    t = s.replace("_", " ")
    m = re.fullmatch(r"([A-Za-z0-9]+)\s+([0-9]+[A-Za-z]?)", t.strip())
    if m:
        return f"{m.group(1)}-{m.group(2)}".upper()
    if "_" in s:
        left, right = s.rsplit("_", 1)
        if _GENOTYPE_SUFFIX_RE.match(right.strip()):
            s = left.strip()
    # Identity keys are used for case-insensitive joins between folder
    # names and Excel labels (13128k ↔ 13128K, 3a ↔ 3A).
    return s.replace(" ", "_").upper()


def pup_identity_key(label: str) -> str:
    """
    Normalize a pup label from Excel ``Name`` or a folder name so they can match.

    Examples:
      - ``17450L`` and folder ``17450L_WT`` → ``17450L``
      - ``24277J-2A (J)`` and ``24277J-2A (BLUE) WT-WT-WT`` → ``24277J-2A``
      - ``14164P-1C`` and ``14164P_1C`` → same key
      - ``22742K_4A_G-R`` and path ``…22742K_4A_GREEN-RED…`` → same key (via canonical)
    """
    return _pup_identity_key_core(canonical_pup_display_name(label))


def iter_pup_table_lookup_keys(mother: str, *name_hints: str) -> List[Tuple[str, str]]:
    """
    Ordered ``(mother, name)`` keys to try against pup-summary / sex lookups.

    Includes raw hints plus :func:`pup_identity_key` variants so Excel rows
    with colour/genotype suffixes can still match folder-based keys.
    """
    m = str(mother).strip()
    mu = m.upper()
    seen: Set[Tuple[str, str]] = set()
    out: List[Tuple[str, str]] = []

    def add_pair(a: str, b: str) -> None:
        b2 = str(b).strip()
        if not b2:
            return
        key = (a, b2)
        if key not in seen:
            seen.add(key)
            out.append(key)

    variants: List[str] = []
    for h in name_hints:
        hs = str(h).strip() if h else ""
        if not hs:
            continue
        if hs not in variants:
            variants.append(hs)
        cd = canonical_pup_display_name(hs)
        if cd and cd not in variants:
            variants.append(cd)

    for nm in variants:
        pk = pup_identity_key(nm)
        for a in (mu, m):
            add_pair(a, nm)
            if pk != nm:
                add_pair(a, pk)
    return out


# ---------------------------------------------------------------------------
# Filesystem resolution helpers (mouse-usv project layout)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=64)
def _list_subdirs(parent: Path):
    """Cached ``{name: Path}`` of *parent*'s subdirectories.

    Repeated lookups across thousands of recordings would otherwise re-scan
    the same mother / pup folders many times.
    """
    if not parent.is_dir():
        return {}
    return {d.name: d for d in parent.iterdir() if d.is_dir()}


def _normalize_for_match(s: str) -> str:
    """Lowercase + dash→space: makes ``13128K-1A`` match ``13128K 1A WT-WT-WT RED``."""
    return s.lower().replace('-', ' ')


def _find_all_dirs(parent: Path, prefix: str) -> List[Path]:
    """Find all subdirectories of *parent* whose names match *prefix*.

    Uses normalized matching (case-insensitive, dash == space) so that
    e.g. prefix ``13128K-1A`` matches folder ``13128K 1A WT-WT-WT RED``.

    Also handles folders with extra words between the id and the pup
    number (e.g. ``13131J Het SUP 1A red`` for prefix ``13131J-1A``).

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

    First tries the canonical underscore-separated layout::

        <root>/<year>/<mother>_<matgen>/<name>_<pupgen>/day_<day>/session<session>/<rec_num>

    If the mother or pup directory does not exist, falls back to searching
    for a directory whose name starts with the mother / name identifier
    (handles space-separated folders like ``13128K WT`` or ``13128K-1A RED``).

    When a mother has multiple litters in separate directories (e.g.
    ``24277J WT`` and ``24277J WT - litter 2``), all matching mother
    directories are searched until the pup is found.

    Always returns a :class:`Path` — combine with :func:`resolve_wav_path`
    to get the actual ``.wav`` file (or ``None`` if it does not exist).
    """
    year_dir = Path(recordings_root) / str(year)
    suffix = Path(f"day_{int(day)}") / f"session{int(session)}" / str(rec_num)

    # Canonical underscore-separated path
    canonical_mother = year_dir / f"{mother}_{matgen}"
    canonical_pup = canonical_mother / f"{name}_{pupgen}"
    if canonical_pup.is_dir():
        return canonical_pup / suffix

    # Collect candidate mother directories
    if canonical_mother.is_dir():
        mother_candidates = [canonical_mother]
    else:
        mother_candidates = _find_all_dirs(year_dir, mother)

    if not mother_candidates:
        return canonical_mother / f"{name}_{pupgen}" / suffix

    # Pup identity key gives a stronger match than prefix alone for labels
    # carrying colour/genotype suffixes (24277J-2A (J) ↔ 24277J-2A (BLUE) WT-WT-WT).
    pup_key = pup_identity_key(name)

    for mother_dir in mother_candidates:
        pup_dir = mother_dir / f"{name}_{pupgen}"
        if pup_dir.is_dir():
            return pup_dir / suffix

        # First, try identity-key matching against any subdirectory.
        for child_name, child_path in _list_subdirs(mother_dir).items():
            if pup_identity_key(child_name) == pup_key:
                return child_path / suffix

        # Fall back to prefix / token matching (handles ``13128K 1A WT-WT-WT RED`` style).
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
