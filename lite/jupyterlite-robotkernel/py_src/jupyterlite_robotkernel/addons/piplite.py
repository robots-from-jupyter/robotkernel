"""a JupyterLite addon for supporting piplite wheels"""

# Overridden to patch_jupyterlite_json to support robolite-kernel

from jupyterlite.addons.piplite import PipliteAddon as BasePipliteAddon
from jupyterlite.addons.piplite import PIPLITE_URLS
from jupyterlite.addons.piplite import write_wheel_index
from jupyterlite.constants import JUPYTER_CONFIG_DATA
from jupyterlite.constants import JSON_FMT
from jupyterlite.constants import LITE_PLUGIN_SETTINGS
from jupyterlite.constants import UTF8
from jupyterlite.constants import ALL_JSON

from pathlib import Path

import json
import sys


ROBOLITE_PLUGIN_ID = "@jupyterlite/robolite-kernel-extension:kernel"
PY = Path(sys.executable)
PYPI_WHEELS = "pypi"


class PipliteAddon(BasePipliteAddon):

    def patch_jupyterlite_json(self, jupyterlite_json, whl_index, whl_metas, pkg_jsons):
        """add the piplite wheels to jupyter-lite.json"""
        super().patch_jupyterlite_json(
            jupyterlite_json, whl_index, whl_metas, pkg_jsons
        )
        config = json.loads(jupyterlite_json.read_text(**UTF8))
        old_urls = (
            config.setdefault(JUPYTER_CONFIG_DATA, {})
            .setdefault(LITE_PLUGIN_SETTINGS, {})
            .setdefault(ROBOLITE_PLUGIN_ID, {})
            .get(PIPLITE_URLS, [])
        )

        new_urls = []

        # first add user-specified wheels
        if whl_metas:
            metadata = {}
            for whl_meta in whl_metas:
                meta = json.loads(whl_meta.read_text(**UTF8))
                whl = self.output_wheels / whl_meta.name.replace(".json", "")
                metadata[whl] = meta["name"], meta["version"], meta["release"]

            whl_index = write_wheel_index(self.output_wheels, metadata)
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
        else:
            new_urls = old_urls

        # ...then add wheels from federated extensions...
        if pkg_jsons:
            for pkg_json in pkg_jsons:
                pkg_data = json.loads(pkg_json.read_text(**UTF8))
                wheel_dir = pkg_data.get("piplite", {}).get("wheelDir")
                if wheel_dir:
                    pkg_whl_index = pkg_json.parent / wheel_dir / ALL_JSON
                    if pkg_whl_index.exists():
                        pkg_whl_index_url_with_sha = self.get(pkg_whl_index)[1]
                        new_urls += [pkg_whl_index_url_with_sha]

        # ... and only update if actually changed
        if new_urls:

            config[JUPYTER_CONFIG_DATA][LITE_PLUGIN_SETTINGS][ROBOLITE_PLUGIN_ID][
                PIPLITE_URLS
            ] = new_urls

            jupyterlite_json.write_text(json.dumps(config, **JSON_FMT), **UTF8)

            self.maybe_timestamp(jupyterlite_json)
