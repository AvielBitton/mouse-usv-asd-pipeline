from pathlib import Path

from typing import Optional


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

    This project stores recordings in a structured folder layout:
      <recordings_root>/<year>/<mother>_<matgen>/<name>_<pupgen>/day_<day>/session<session>/<rec_num>.(wav|WAV)

    Example (base path, no extension):
      USV_Recordings/2015/08001P_HT/08132N_WT/day_10/session2/T0000001

    Returning a Path (instead of a string) makes it easier and safer to add extensions,
    check file existence, and avoid string formatting duplication.
    """
    return (
        Path(recordings_root)
        / str(year)
        / f"{mother}_{matgen}"
        / f"{name}_{pupgen}"
        / f"day_{int(day)}"
        / f"session{int(session)}"
        / str(rec_num)
    )


def resolve_wav_path(base_path: Path) -> Optional[Path]:
    """
    Resolve the actual WAV file path from a base path (no extension).

    Some datasets use '.wav' and others use '.WAV'. This helper:
      1) checks '<base>.wav'
      2) if not found, checks '<base>.WAV'
      3) returns None if neither exists

    This keeps the main loop clean and avoids duplicating the full path formatting twice.
    """
    wav_lower = base_path.with_suffix(".wav")
    if wav_lower.exists():
        return wav_lower

    wav_upper = base_path.with_suffix(".WAV")
    if wav_upper.exists():
        return wav_upper

    return None

