#!/usr/bin/env python
"""Build GitHub-ready release bundles without polluting the dev setup.

This script produces zip archives in release/artifacts/<version>/ that can be
uploaded directly to a GitHub release. It keeps packaging outputs away from
your development folders (dist/, frontend/build/, etc.).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
DIST_DIR = REPO_ROOT / "dist"
RELEASE_ROOT = REPO_ROOT / "release" / "artifacts"

# Map target names to their PyInstaller spec files and expected dist folders.
TARGETS = {
    "launcher": {"spec": "ghost_companion.spec", "dist": "GhostCompanionLauncher"},
    "desktop": {"spec": "ghost_desktop.spec", "dist": "GhostCompanion"},
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create clean release bundles for GitHub downloads."
    )
    parser.add_argument(
        "--version",
        help="Version label for the artifacts (defaults to frontend/package.json).",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Reuse existing dist/ outputs instead of rebuilding.",
    )
    parser.add_argument(
        "--launcher-only",
        action="store_true",
        help="Only package the launcher (backend + web UI).",
    )
    parser.add_argument(
        "--desktop-only",
        action="store_true",
        help="Only package the desktop app (no browser UI).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing release/artifacts/<version>/ directory.",
    )
    args = parser.parse_args()

    targets = resolve_targets(args.launcher_only, args.desktop_only)
    version = resolve_version(args.version)
    release_dir = RELEASE_ROOT / f"v{version}"

    if release_dir.exists():
        if not args.overwrite:
            sys.exit(
                f"{release_dir} already exists; pass --overwrite to recreate it."
            )
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True)

    if not args.skip_build:
        build_frontend()
        build_pyinstaller(targets)

    archives = []
    staged_dirs = []
    for target in targets:
        dist_name = TARGETS[target]["dist"]
        source_dir = DIST_DIR / dist_name
        staged_dir, archive = stage_artifact(
            source_dir, release_dir, dist_name, version
        )
        staged_dirs.append(staged_dir)
        archives.append(archive)

    checksum_file = write_checksums(archives, release_dir)
    release_notes = write_release_notes(release_dir, version, staged_dirs, archives)

    print()
    print(f"[release] Done. Artifacts staged under: {release_dir}")
    print(f"[release] Checksums: {checksum_file.name}")
    print(f"[release] Notes:     {release_notes.name}")
    for archive in archives:
        print(f"[release] -> {archive.name}")


def resolve_targets(
    launcher_only: bool, desktop_only: bool
) -> list[str]:
    if launcher_only and desktop_only:
        sys.exit("Use only one of --launcher-only or --desktop-only.")
    if launcher_only:
        return ["launcher"]
    if desktop_only:
        return ["desktop"]
    return list(TARGETS.keys())


def resolve_version(explicit: str | None) -> str:
    if explicit:
        return explicit
    pkg_path = FRONTEND_DIR / "package.json"
    try:
        with pkg_path.open("r", encoding="utf-8") as handle:
            package_json = json.load(handle)
        return str(package_json["version"])
    except Exception:
        today = _dt.date.today()
        return f"{today.year}.{today.month:02d}.{today.day:02d}"


def resolve_cmd(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        sys.exit(f"Required tool not found on PATH: {name}")
    return path


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print(f"[release] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def build_frontend() -> None:
    npm_cmd = resolve_cmd("npm")
    if not (FRONTEND_DIR / "node_modules").exists():
        run([npm_cmd, "install"], cwd=FRONTEND_DIR)
    run([npm_cmd, "run", "build"], cwd=FRONTEND_DIR)


def build_pyinstaller(targets: Iterable[str]) -> None:
    pyinstaller_cmd = resolve_cmd("pyinstaller")
    for target in targets:
        spec_file = TARGETS[target]["spec"]
        run([pyinstaller_cmd, "--clean", "--noconfirm", spec_file], cwd=REPO_ROOT)


def stage_artifact(
    source_dir: Path, release_dir: Path, label: str, version: str
) -> tuple[Path, Path]:
    if not source_dir.exists():
        raise FileNotFoundError(
            f"Expected build output missing: {source_dir}. "
            "Run without --skip-build or build manually first."
        )
    staged_dir = release_dir / f"{label}-v{version}"
    shutil.copytree(long_path(source_dir), long_path(staged_dir))
    archive_path = shutil.make_archive(
        long_path(staged_dir), "zip", root_dir=long_path(release_dir), base_dir=staged_dir.name
    )
    return staged_dir, Path(archive_path)


def write_checksums(archives: list[Path], release_dir: Path) -> Path:
    checksum_file = release_dir / "SHA256SUMS.txt"
    with checksum_file.open("w", encoding="utf-8") as handle:
        for archive in archives:
            digest = sha256_file(archive)
            handle.write(f"{digest}  {archive.name}\n")
    return checksum_file


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_release_notes(
    release_dir: Path, version: str, staged_dirs: list[Path], archives: list[Path]
) -> Path:
    notes = release_dir / "RELEASE-NOTES.txt"
    lines = [
        f"Ghost Companion release v{version}",
        "",
        "Contents:",
    ]
    for staged, archive in zip(staged_dirs, archives):
        lines.append(f"- {archive.name}: packaged from {staged.name}/")
    lines += [
        "",
        "Upload the zip files above to a GitHub Release.",
        "The staged folders are left intact for code signing or final manual checks.",
        "",
        "To verify integrity after download:",
        "  certutil -hashfile <zip> SHA256",
        "  (compare with SHA256SUMS.txt)",
        "",
        "Environment: .env is not bundled. The app prompts for missing values",
        "on first launch and writes them next to the executable.",
    ]
    notes.write_text("\n".join(lines), encoding="utf-8")
    return notes


def long_path(path: Path) -> str:
    """Return a path string with Windows long-path prefix to avoid MAX_PATH issues."""

    resolved = path.resolve()
    if os.name == "nt":
        raw = str(resolved)
        if not raw.startswith("\\\\?\\"):
            return "\\\\?\\" + raw
        return raw
    return str(resolved)


if __name__ == "__main__":
    main()
