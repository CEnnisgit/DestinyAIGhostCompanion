from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
import os
import traceback
from datetime import datetime


LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "desktop_bootstrap.log"


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def _pip_install_requirements(req_path: Path) -> bool:
    try:
        _log(f"Installing requirements from {req_path}")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_path)], check=True)
        return True
    except Exception as e:
        _log(f"Failed to install requirements: {e}")
        return False


def _ensure_module(mod: str, pip_name: str | None = None) -> bool:
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        name = pip_name or mod
        try:
            _log(f"Installing missing dependency: {name}")
            subprocess.run([sys.executable, "-m", "pip", "install", name], check=True)
            importlib.invalidate_caches()
            importlib.import_module(mod)
            return True
        except Exception as e:
            _log(f"Failed to install {name}: {e}")
            return False


def _bootstrap() -> None:
    repo_root = Path(__file__).resolve().parent
    req = repo_root / "requirements.txt"

    # Ensure core GUI dependency first; if missing, install full requirements.
    try:
        importlib.import_module("PySide6")
    except Exception:
        if req.exists():
            if not _pip_install_requirements(req):
                _log("Continuing without full requirements; attempting minimal installs")
        else:
            _log("requirements.txt not found; attempting minimal installs")

    # Minimal guarantees for desktop run
    _ensure_module("PySide6")
    # Ensure WebEngine widgets module (lives in PySide6-Addons)
    _ensure_module("PySide6.QtWebEngineWidgets", pip_name="PySide6-Addons")
    _ensure_module("numpy")
    _ensure_module("sounddevice")
    _ensure_module("pyttsx3")
    _ensure_module("playsound")
    # Optional local STT (won't block startup if unavailable)
    _ensure_module("faster_whisper", pip_name="faster-whisper")
    _ensure_module("soundfile")
    _ensure_frontend_build_preflight()



def _ensure_frontend_build_preflight() -> None:
    # Skip if dev server mode requested
    if os.getenv("DESKTOP_WEB_DEV") == "1":
        return
    repo = Path(__file__).resolve().parent
    fe_dir = repo / "frontend"
    build_dir = fe_dir / "build"
    if not fe_dir.exists():
        return
    # Determine if build is missing or stale vs src
    def _latest_mtime(p: Path) -> float:
        latest = 0.0
        for ext in (".js", ".jsx", ".ts", ".tsx", ".css"):
            for fp in p.rglob(f"*{ext}"):
                try:
                    latest = max(latest, fp.stat().st_mtime)
                except Exception:
                    pass
        return latest

    need_build = False
    if not build_dir.exists():
        need_build = True
    else:
        try:
            src_mtime = _latest_mtime(fe_dir / "src")
            build_mtime = _latest_mtime(build_dir)
            need_build = src_mtime > (build_mtime + 2)
        except Exception:
            need_build = False

    if not need_build:
        return
    try:
        _log("Building frontend (npm install && npm run build)…")
        subprocess.run(["npm", "install"], cwd=str(fe_dir), check=True)
        subprocess.run(["npm", "run", "build"], cwd=str(fe_dir), check=True)
        _log("Frontend build complete.")
    except FileNotFoundError:
        _log("npm not found on PATH; skipping UI build. Dev mode may still work.")
    except subprocess.CalledProcessError as e:
        _log(f"Frontend build failed with exit code {e.returncode}.")

def main() -> None:
    try:
        _log("Desktop bootstrap start")
        _bootstrap()
        _log("Launching desktop UI…")
        from ghost.desktop import main as _main
        _main()
    except Exception:
        tb = traceback.format_exc()
        _log("Fatal error during startup:\n" + tb)
        # Try to show a message box even if Qt isn't available yet
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, tb, "Ghost Companion - Startup Error", 0)
        except Exception:
            pass


if __name__ == "__main__":
    main()

