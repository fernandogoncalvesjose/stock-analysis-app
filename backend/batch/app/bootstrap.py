from pathlib import Path
import sys


def configure_batch_pythonpath() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    api_root = backend_root / "api"
    core_root = backend_root

    for path in (api_root, core_root):
        value = str(path)
        if value not in sys.path:
            sys.path.append(value)
