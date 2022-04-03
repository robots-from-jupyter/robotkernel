"""jupyterlite-robotkernel setup"""
import json
from pathlib import Path

HERE = Path(__file__).parent.resolve()
EXT = HERE / "py_src/jupyterlite_robotkernel/labextension"
PKG = EXT / "package.json"

__js__ = json.loads(
    PKG.read_text()
    # Allow installation without labextensions for piplite entrypoint only:
    if PKG.exists()
    else '{"version": "0.0.0"}'
)
SHARE = (
    f"""share/jupyter/labextensions/{__js__["name"]}"""
    if "name" in __js__
    else None
)

setup_args = dict(
    version=__js__["version"],
    data_files=[
        (SHARE, ["install.json"])
    ] + [
        (f"""{SHARE}/{p.parent.relative_to(EXT).as_posix()}""", [
            str(p.relative_to(HERE).as_posix())
        ])
        for p in EXT.rglob("*") if not p.is_dir()
    ] if SHARE else []
)

if __name__ == "__main__":
    import setuptools
    setuptools.setup(**setup_args)
