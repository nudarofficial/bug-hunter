#!/usr/bin/env python3
"""Build the installable skill ZIP and its SHA-256 checksum file.

The archive contains a single top-level `bug-hunter/` folder with SKILL.md,
the reference files, and the LICENSE, which is the layout expected when
uploading a custom skill ZIP to claude.ai or unzipping into ~/.claude/skills/.

The build is reproducible: entries are sorted and stored uncompressed,
timestamps and permissions are fixed, and text files are normalized to LF line
endings, so the same source produces the same checksum on Windows, macOS, and
Linux.

Usage:
    python scripts/build_release.py --version 1.0.0 [--out dist]
    python scripts/build_release.py --verify dist/bug-hunter-v1.0.0.zip
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_NAME = "bug-hunter"
# ZIP format cannot store dates before 1980; this is the conventional fixed value.
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
FILE_MODE = 0o644
TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".js", ".yml", ".yaml", ""}


def collect_files() -> list[tuple[str, pathlib.Path]]:
    skill_dir = ROOT / SKILL_NAME
    if not (skill_dir / "SKILL.md").is_file():
        raise SystemExit(f"error: {skill_dir / 'SKILL.md'} not found")
    entries = []
    for path in skill_dir.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            entries.append((f"{SKILL_NAME}/{path.relative_to(skill_dir).as_posix()}", path))
    license_file = ROOT / "LICENSE"
    if license_file.is_file():
        entries.append((f"{SKILL_NAME}/LICENSE", license_file))
    return sorted(entries)


def read_normalized(path: pathlib.Path) -> bytes:
    data = path.read_bytes()
    if path.suffix in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return data


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(version: str, out_dir: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SystemExit(f"error: version must look like 1.2.3, got {version!r}")
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{SKILL_NAME}-v{version}.zip"
    # ZIP_STORED (no compression) keeps the bytes independent of the zlib
    # version; the skill is small text, so the size cost is negligible.
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as zf:
        for arcname, path in collect_files():
            info = zipfile.ZipInfo(arcname, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = (0o100000 | FILE_MODE) << 16  # regular file, rw-r--r--
            info.create_system = 3  # Unix, so the mode bits are honored
            zf.writestr(info, read_normalized(path))
    checksum = out_dir / f"{archive.name}.sha256"
    checksum.write_text(f"{sha256_of(archive)}  {archive.name}\n", encoding="utf-8", newline="\n")
    return archive, checksum


def verify(archive: pathlib.Path) -> bool:
    checksum = archive.with_name(archive.name + ".sha256")
    if not archive.is_file() or not checksum.is_file():
        print(f"error: need both {archive} and {checksum}")
        return False
    expected, _, name = checksum.read_text(encoding="utf-8").strip().partition("  ")
    actual = sha256_of(archive)
    if name != archive.name:
        print(f"error: checksum file names {name!r}, expected {archive.name!r}")
        return False
    if actual != expected:
        print(f"MISMATCH: expected {expected}, got {actual}")
        return False
    with zipfile.ZipFile(archive) as zf:
        bad = zf.testzip()
        names = zf.namelist()
    if bad is not None:
        print(f"error: corrupt entry {bad}")
        return False
    if f"{SKILL_NAME}/SKILL.md" not in names:
        print(f"error: {SKILL_NAME}/SKILL.md missing from archive")
        return False
    print(f"OK: {archive.name} sha256={actual} ({len(names)} files)")
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build or verify the skill release ZIP.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--version", help="release version, e.g. 1.0.0")
    group.add_argument("--verify", type=pathlib.Path, help="verify an archive against its .sha256 file")
    parser.add_argument("--out", type=pathlib.Path, default=ROOT / "dist")
    args = parser.parse_args(argv)

    if args.verify:
        return 0 if verify(args.verify) else 1
    archive, checksum = build(args.version, args.out)
    print(f"Built {archive}")
    print(f"Wrote {checksum}: {checksum.read_text(encoding='utf-8').strip()}")
    return 0 if verify(archive) else 1


if __name__ == "__main__":
    sys.exit(main())
