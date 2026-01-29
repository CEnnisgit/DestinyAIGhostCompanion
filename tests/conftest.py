import sys
from pathlib import Path

# Ensure project root is on the import path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Always provide test-only stubs for external HTTP libraries
from tests.stubs import requests as _requests  # type: ignore
from tests.stubs import responses as _responses  # type: ignore

sys.modules["requests"] = _requests
sys.modules["responses"] = _responses
