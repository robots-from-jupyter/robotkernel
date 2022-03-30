"""Install RobotKernel wheels.

Update wheels.json for RobotKernelAddon:

    python -m jupyterlite_robotkernel.addons.robotkernel

"""
from typing import List

from jupyterlite.addons.base import BaseAddon
from jupyterlite.addons.piplite import PIPLITE_URLS
from jupyterlite.addons.piplite import PYPI_WHEELS
from jupyterlite.constants import ALL_JSON
from jupyterlite.constants import JSON_FMT
from jupyterlite.constants import JUPYTERLITE_JSON
from jupyterlite.constants import JUPYTER_CONFIG_DATA
from jupyterlite.constants import LITE_PLUGIN_SETTINGS
from jupyterlite.constants import UTF8

from contextlib import contextmanager
from hashlib import sha256
from importlib import resources
from pathlib import Path
from tempfile import mkdtemp

import argparse
import json
import os
import shutil
import subprocess
import sys
import traitlets

PY = Path(sys.executable)
DEFAULT_WHEELS = json.loads(
    resources.read_text("jupyterlite_robotkernel.addons", "wheels.json")
)
ROBOLITE_PLUGIN_ID = "@jupyterlite/robolite-kernel-extension:kernel"


class RobotKernelAddon(BaseAddon):
    """Ensures the unique dependencies of robotkernel are available."""

    __all__ = ["pre_build", "post_build"]

    wheel_urls = traitlets.List(DEFAULT_WHEELS).tag(config=True)

    def __init__(self, manager, *args, **kwargs):
        kwargs["parent"] = manager
        kwargs["manager"] = manager
        super().__init__(*args, **kwargs)

    def pre_build(self, manager):
        """Downloads wheels."""
        for wheel in self.wheel_urls:
            dest = manager.output_dir / "pypi" / Path(wheel).name
            if dest.exists():
                continue
            yield dict(
                name=f"""fetch:{wheel.rsplit("/", 1)[-1]}""",
                actions=[(self.fetch_one, [wheel, dest])],
                targets=[dest],
            )

    def post_build(self, manager):
        jupyterlite_json = manager.output_dir / JUPYTERLITE_JSON
        whl_index = manager.output_dir / PYPI_WHEELS / ALL_JSON
        yield dict(
            name="patch",
            doc=f"ensure {JUPYTERLITE_JSON} includes any piplite wheels",
            file_dep=[jupyterlite_json, whl_index],
            actions=[
                (
                    self.patch_jupyterlite_json,
                    [jupyterlite_json, whl_index],
                )
            ],
            targets=[f"{whl_index}#"],  # TODO: target
        )

    def patch_jupyterlite_json(self, jupyterlite_json, whl_index):
        """add the piplite wheels to jupyter-lite.json"""
        config = json.loads(jupyterlite_json.read_text(**UTF8))
        old_urls = (
            config.setdefault(JUPYTER_CONFIG_DATA, {})
            .setdefault(LITE_PLUGIN_SETTINGS, {})
            .setdefault(ROBOLITE_PLUGIN_ID, {})
            .get(PIPLITE_URLS, [])
        )

        new_urls = []
        whl_index_url, whl_index_url_with_sha = self.get_index_urls(whl_index)
        added_build = False
        for url in old_urls:
            if url.split("#")[0].split("?")[0] == whl_index_url:
                new_urls += [whl_index_url_with_sha]
                added_build = True
            else:
                new_urls += [url]
        if not added_build:
            new_urls = [whl_index_url_with_sha, *new_urls]

        # ... and only update if actually changed
        if len(new_urls) > len(old_urls) or added_build:

            config[JUPYTER_CONFIG_DATA][LITE_PLUGIN_SETTINGS][ROBOLITE_PLUGIN_ID][
                PIPLITE_URLS
            ] = new_urls

            jupyterlite_json.write_text(json.dumps(config, **JSON_FMT), **UTF8)

            self.maybe_timestamp(jupyterlite_json)

    def get_index_urls(self, whl_index):
        """get output dir relative URLs for all.json files"""
        whl_index_sha256 = sha256(whl_index.read_bytes()).hexdigest()
        whl_index_url = f"./{whl_index.relative_to(self.manager.output_dir).as_posix()}"
        whl_index_url_with_sha = f"{whl_index_url}?sha256={whl_index_sha256}"
        return whl_index_url, whl_index_url_with_sha


@contextmanager
def NamedTemporaryDirectory():
    tmpdir = mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


def resolve_wheel_urls(reqs: List[str]) -> List[str]:
    with NamedTemporaryDirectory() as tmpdir:
        return _resolve_wheel_urls(tmpdir, reqs)


def _resolve_wheel_urls(tmpdir: str, reqs: List[str]) -> List[str]:
    cwd = Path(tmpdir).resolve()
    cwd.mkdir(parents=True, exist_ok=True)
    # Install robotkernel
    subprocess.check_call([PY, "-m", "pip", "wheel", "--prefer-binary", *reqs], cwd=cwd)
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
    return [
        f"""https://files.pythonhosted.org/packages/py2.py3/{path.name[0]}/{path.name.split("-")[0]}/{path.name}"""
        for path in sorted(cwd.glob("*-none-any.whl"))
        if path.name.endswith("py2.py3-none-any.whl") or path.name in PY2_PY3_EXCEPTIONS
    ] + [
        f"""https://files.pythonhosted.org/packages/py3/{path.name[0]}/{path.name.split("-")[0]}/{path.name}"""
        for path in sorted(cwd.glob("*-none-any.whl"))
        if not path.name.endswith("py2.py3-none-any.whl")
        and path.name not in PY2_PY3_EXCEPTIONS
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Resolve RobotKernel wheel with dependencies."
    )
    parser.add_argument(
        "--inplace",
        action=argparse.BooleanOptionalAction,
        help="update RobotKernel wheel_urls `--inplace` or create/update `jupyter_lite_config.json` (default)",
    )
    args = parser.parse_args()
    wheel_urls = resolve_wheel_urls(["robotkernel >=1.6a1"])
    config = Path(os.getcwd()) / "jupyter_lite_config.json"
    if args.inplace:
        (Path(__file__).parent / "wheels.json").write_text(
            json.dumps(wheel_urls, indent=4)
        )
    else:
        config_json = json.loads(config.read_text()) if config.exists() else {}
        config_json.setdefault("LiteBuildConfig", {})
        config_json.setdefault("RobotKernelAddon", {}).setdefault("wheel_urls", [])
        config_json["RobotKernelAddon"]["wheel_urls"] = wheel_urls
        config.write_text(json.dumps(config_json, indent=4))
