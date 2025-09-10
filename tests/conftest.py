import sys
from pathlib import Path

# Ensure project root is on the import path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Provide test-only stubs for external HTTP libraries when they're not installed
try:  # pragma: no cover - imported for side effects
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - runtime fallback
    from tests.stubs import requests  # type: ignore
    sys.modules["requests"] = requests

try:  # pragma: no cover - imported for side effects
    import responses  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - runtime fallback
    from tests.stubs import responses  # type: ignore
    sys.modules["responses"] = responses
