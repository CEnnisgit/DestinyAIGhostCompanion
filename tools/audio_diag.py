"""Standalone audio diagnostic helper.

Runs the same checks exposed via /diagnostics/audio so developers can collect
microphone/STT troubleshooting data without launching the full UI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ghost.voice import diagnose_audio, HAVE_SD  # type: ignore


def _query_devices() -> dict[str, object]:
    if not HAVE_SD:
        return {"available": False, "error": "sounddevice module missing"}
    try:
        import sounddevice as _sd  # type: ignore

        devices = _sd.query_devices()
        default_in = getattr(_sd.default, "device", [None, None])[0]
        return {
            "available": True,
            "default_input": default_in,
            "devices": devices,
        }
    except Exception as exc:  # pragma: no cover - best-effort helper
        return {"available": False, "error": str(exc)}


def main() -> None:
    payload = {
        "report": diagnose_audio().splitlines(),
        "devices": _query_devices(),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
