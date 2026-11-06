"""Write a release version in the integration's manifest."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
MANIFEST = ROOT / "custom_components" / "electricity_contracts" / "manifest.json"

manifest = json.loads(MANIFEST.read_text())
manifest["version"] = sys.argv[1]
MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
