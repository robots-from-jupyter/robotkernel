import json
from pathlib import Path

__all__ = ["__version__", "__js__"]
__js__ = json.loads(
    (Path(__file__).parent.resolve() / "labextension/package.json").read_text()
    # Allow installation without labextensions for piplite entrypoint only:
    if (Path(__file__).parent.resolve() / "labextension/package.json").exists()
    else '{"version": "0.0.0"}'
)
__version__ = __js__["version"]
