"""Robust shim for `import cge_scraper` used by tests.

This shim first tries to import the package `cge_scraper` (i.e. the folder
`cge_scraper/__init__.py`). If that fails (for example if tests are run from a
different working directory), it falls back to loading `main.py` from the repo
root and re-exports the expected symbols.
"""
import importlib
import importlib.util
import os
import sys


def _load_from_main():
	"""Load main.py from the project root and return the module."""
	this_dir = os.path.dirname(os.path.abspath(__file__))
	script_path = os.path.join(this_dir, "main.py")
	if not os.path.exists(script_path):
		# as a last resort, try parent directory
		script_path = os.path.join(this_dir, "..", "main.py")
		script_path = os.path.normpath(script_path)
	spec = importlib.util.spec_from_file_location("cge_scraper_main", script_path)
	module = importlib.util.module_from_spec(spec)
	sys.modules["cge_scraper_main"] = module
	spec.loader.exec_module(module)
	return module


# Try import package first
try:
	pkg = importlib.import_module("cge_scraper")
	# if package has been imported from the directory, re-export from it
	sanitize_param = getattr(pkg, "sanitize_param")
	main = getattr(pkg, "main")
	send_message = getattr(pkg, "send_message")
	URL = getattr(pkg, "URL")
	module = getattr(pkg, "_loaded_module", pkg)
except Exception:
	# fallback: load main.py directly
	module = _load_from_main()
	sanitize_param = getattr(module, "sanitize_param")
	main = getattr(module, "main")
	send_message = getattr(module, "send_message")
	URL = getattr(module, "URL")

