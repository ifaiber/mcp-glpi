import os
import sys
from pathlib import Path


# Ensure local source tree is preferred over any installed copy
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

# Provide dummy tokens so config validation passes during tests
os.environ.setdefault("GLPI_APP_TOKEN", "test-token")
os.environ.setdefault("GLPI_USER_TOKEN", "test-token")

# Clear any previously imported installed version so we always use the local code
for module_name in list(sys.modules):
    if module_name == "mcp_glpi" or module_name.startswith("mcp_glpi."):
        sys.modules.pop(module_name, None)

import importlib

importlib.invalidate_caches()
importlib.import_module("mcp_glpi")
