"""Generate wheels.json for RobotKernelAddon

Usage:

    python wheels.py

"""

from contextlib import contextmanager
from tempfile import mkdtemp
from pathlib import Path

import json
import os
import subprocess
import sys
import shutil

PY = Path(sys.executable)


@contextmanager
def NamedTemporaryDirectory():
    tmpdir = mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


def wheels_json(tmpdir: str):
    cwd = Path(tmpdir).resolve()
    cwd.mkdir(parents=True, exist_ok=True)
    # Install robotkernel
    subprocess.check_call(
        [PY, "-m", "pip", "wheel", "--prefer-binary", "robotkernel >=1.6a1"], cwd=cwd
    )
    # Remove wheels that conflict with pyolite shims
    for path in cwd.glob("ipykernel-*"):
        os.unlink(path)
    for path in cwd.glob("widgetsnbextension-*"):
        os.unlink(path)
    # Remove binary wheels
    for path in set(cwd.glob("*")) - (set(cwd.glob("*-none-any.whl"))):
        os.unlink(path)
    # Freeze
    PY2_PY3_EXCEPTIONS = ["testpath-0.6.0-py3-none-any.whl"]
    return json.dumps(
        [
            f"""https://files.pythonhosted.org/packages/py2.py3/{path.name[0]}/{path.name.split("-")[0]}/{path.name}"""
            for path in sorted(cwd.glob("*-none-any.whl"))
            if path.name.endswith("py2.py3-none-any.whl")
            or path.name in PY2_PY3_EXCEPTIONS
        ]
        + [
            f"""https://files.pythonhosted.org/packages/py3/{path.name[0]}/{path.name.split("-")[0]}/{path.name}"""
            for path in sorted(cwd.glob("*-none-any.whl"))
            if not path.name.endswith("py2.py3-none-any.whl")
            and path.name not in PY2_PY3_EXCEPTIONS
        ],
        indent=4,
    )


if __name__ == "__main__":
    with NamedTemporaryDirectory() as tmpdir:
        (Path(__file__).parent / "wheels.json").write_text(wheels_json(tmpdir))
