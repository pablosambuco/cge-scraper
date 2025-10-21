"""Package shim that loads the top-level main.py so tests can import cge_scraper.

This keeps the repository layout flexible (main.py at project root) while allowing
`import cge_scraper` in tests.
"""
import importlib.util
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = THIS_DIR
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "main.py")

spec = importlib.util.spec_from_file_location("cge_scraper.main", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules["cge_scraper.main"] = module
spec.loader.exec_module(module)

# Re-export commonly used symbols for tests
sanitize_param = getattr(module, "sanitize_param")
send_message = getattr(module, "send_message")
send_message = getattr(module, "read_config")
send_message = getattr(module, "get_config")
send_message = getattr(module, "tprint")
main = getattr(module, "main")
URL = getattr(module, "_CONFIG")

