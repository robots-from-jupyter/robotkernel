# -*- coding: utf-8 -*-
from io import StringIO
from robotkernel.constants import THROBBER
import re


try:
    from robotkernel.display_ipykernel import DisplayKernel
except ImportError:
    from robotkernel.display_pyolite import DisplayKernel


class ProgressUpdater(StringIO):
    """Wrapper designed to capture robot.api.logger.console and display it."""

    colors = re.compile(r"\[[0-?]+[^m]+m")

    def __init__(self, kernel: DisplayKernel, display_id, stdout):
        self.kernel = kernel
        self.display_id = display_id
        self.stdout = stdout
        self.progress = {"dots": [], "test": "n/a", "keyword": "n/a", "message": None}
        self.kernel.send_display_data(
            {
                "text/html": f""
                f'<img src="{THROBBER}" '
                f'style="float:left; height:1em;margin-top:0.15em"/>'
                f'<pre style="'
                f"white-space:nowrap;overflow:hidden;padding-left:1ex;"
                f'"></pre>'
            },
            display_id=self.display_id,
        )
        super().__init__()

    def _update(self):
        status_line = " | ".join(
            str(s)
            for s in [
                self.progress["test"],
                self.progress["keyword"],
                self.progress["message"],
            ]
            if s
        )
        self.kernel.send_update_display_data(
            {
                "text/html": f""
                f'<img src="{THROBBER}" '
                f'style="float:left;height:1em;margin-top:0.15em"/>'
                f'<pre style="'
                f"white-space:nowrap;overflow:hidden;padding-left:1ex;"
                f'">{status_line}</pre>'
            },
            display_id=self.display_id,
        )

    def update(self, data):
        if "test" in data:
            self.progress["test"] = data["test"]
            self.progress["message"] = None
        elif "keyword" in data:
            self.progress["keyword"] = data["keyword"]
            self.progress["message"] = None
        self._update()

    def write(self, s):
        self.progress["message"] = s.strip()
        self._update()
        self.stdout.write(s)
        return super().write(s)
