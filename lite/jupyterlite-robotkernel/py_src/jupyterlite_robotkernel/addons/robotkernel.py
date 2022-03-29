"""Install RobotKernel wheels."""
from importlib import resources
from jupyterlite.addons.base import BaseAddon
from pathlib import Path

import json
import traitlets

DEFAULT_WHEELS = json.loads(
    resources.read_text("jupyterlite_robotkernel.addons", "wheels.json")
)


class RobotKernelAddon(BaseAddon):
    """Ensures the unique dependencies of robotkernel are available."""

    __all__ = ["pre_build"]

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
                targets=[dest]
            )
