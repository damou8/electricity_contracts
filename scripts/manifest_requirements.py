"""Print the integration's requirements, one per line, for pip."""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
MANIFEST = ROOT / "custom_components" / "electricity_contracts" / "manifest.json"

print("\n".join(json.loads(MANIFEST.read_text())["requirements"]))  # noqa: T201
