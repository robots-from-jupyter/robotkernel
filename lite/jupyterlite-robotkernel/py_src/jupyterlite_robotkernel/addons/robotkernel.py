"""Install RobotKernel wheels."""
from importlib import resources
from jupyterlite.addons.base import BaseAddon
from jupyterlite.constants import JUPYTERLITE_JSON
from jupyterlite.constants import LITE_PLUGIN_SETTINGS
from jupyterlite.constants import JUPYTER_CONFIG_DATA
from jupyterlite.constants import UTF8
from jupyterlite.constants import ALL_JSON
from jupyterlite.constants import JSON_FMT
from jupyterlite.addons.piplite import PYPI_WHEELS
from jupyterlite.addons.piplite import PIPLITE_URLS
from pathlib import Path
from hashlib import sha256

import json
import traitlets

DEFAULT_WHEELS = json.loads(
    resources.read_text("jupyterlite_robotkernel.addons", "wheels.json")
)
ROBOLITE_PLUGIN_ID = "@jupyterlite/robolite-kernel-extension:kernel"


class RobotKernelAddon(BaseAddon):
    """Ensures the unique dependencies of robotkernel are available."""

    __all__ = ["pre_build", "post_build"]

    wheel_urls = traitlets.List(DEFAULT_WHEELS).tag(config=True)

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
