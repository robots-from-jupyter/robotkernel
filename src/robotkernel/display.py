# -*- coding: utf-8 -*-
from io import StringIO
from ipykernel.comm import CommManager
from ipykernel.kernelbase import Kernel
from ipykernel.zmqshell import ZMQInteractiveShell
from robotkernel.constants import THROBBER
from traitlets import Any
from traitlets import Instance
from traitlets import Type
import re


class DisplayKernel(Kernel):
    """BaseKernel with interactive shell for display hooks."""

    shell = Instance(
        "IPython.core.interactiveshell.InteractiveShellABC", allow_none=True
    )
    shell_class = Type(ZMQInteractiveShell)

    def __init__(self, **kwargs):
        super(DisplayKernel, self).__init__(**kwargs)

        # Configure IPython shell
        self.shell = self.shell_class.instance(
            parent=self,
            profile_dir=self.profile_dir,
            user_module=self.user_module,
            user_ns=self.user_ns,
            kernel=self,
        )
        self.shell.displayhook.session = self.session
        self.shell.displayhook.pub_socket = self.iopub_socket
        self.shell.displayhook.topic = self._topic("execute_result")
        self.shell.display_pub.session = self.session
        self.shell.display_pub.pub_socket = self.iopub_socket
        self.comm_manager = CommManager(parent=self, kernel=self)
        self.shell.configurables.append(self.comm_manager)

        for type_ in ["comm_open", "comm_msg", "comm_close"]:
            self.shell_handlers[type_] = getattr(self.comm_manager, type_)

    user_module = Any()

    def _user_module_changed(self, name, old, new):
        if self.shell is not None:
            self.shell.user_module = new

    user_ns = Instance(dict, args=(), allow_none=True)

    def _user_ns_changed(self, name, old, new):
        if self.shell is not None:
            self.shell.user_ns = new
            self.shell.init_user_ns()

    def start(self):
        self.shell.exit_now = False
        super(DisplayKernel, self).start()

    def set_parent(self, ident, parent):
        """Overridden from parent to tell the display hook and output streams about the parent message.
        """
        super(DisplayKernel, self).set_parent(ident, parent)
        self.shell.set_parent(parent)

    def do_shutdown(self, restart):
        self.shell.exit_now = True

    def send_error(self, content=None):
        self.send_response(self.iopub_socket, "error", content)

    def send_display_data(self, data=None, metadata=None, display_id=None):
        if isinstance(data, str):
            self.send_response(
                self.iopub_socket, "display_data", {"data": {"text/plain": data}}
            )
        else:
            self.send_response(
                self.iopub_socket,
                "display_data",
                {
                    "data": data or {},
                    "metadata": metadata or {},
                    "transient": {"display_id": display_id},
                },
            )

    def send_update_display_data(self, data=None, metadata=None, display_id=None):
        self.send_response(
            self.iopub_socket,
            "update_display_data",
            {
                "data": data or {},
                "metadata": metadata or {},
                "transient": {"display_id": display_id},
            },
        )

    def send_execute_result(self, data=None, metadata=None, display_id=None):
        self.send_response(
            self.iopub_socket,
            "execute_result",
            {
                "data": data or {},
                "metadata": metadata or {},
                "transient": {"display_id": display_id},
                "execution_count": self.execution_count,
            },
        )


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
        super(ProgressUpdater, self).__init__()

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
        return super(ProgressUpdater, self).write(s)
