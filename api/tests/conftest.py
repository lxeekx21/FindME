# Ensure 'app' package imports resolve when running tests from the api/ directory
import sys
from pathlib import Path

api_root = Path(__file__).resolve().parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))
