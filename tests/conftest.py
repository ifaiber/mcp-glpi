import os
import sys
from pathlib import Path

# Ensure predictable configuration for tests
os.environ.setdefault('GLPI_URL', 'http://example.test')
os.environ.setdefault('GLPI_APP_TOKEN', 'dummy-app-token')
os.environ.setdefault('GLPI_USER_TOKEN', 'dummy-user-token')

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
