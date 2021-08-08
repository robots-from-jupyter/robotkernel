# -*- coding: utf-8 -*-
from pyolite import ipython_shell
from traitlets import Any
from traitlets import Instance


class DisplayKernel:
    """BaseKernel with interactive shell for display hooks."""

    def __init__(self, *args, **kwargs):
        self.comm_info = ipython_shell.kernel.comm_info
        self.comm_manager = ipython_shell.kernel.comm_manager
        self.interpreter = ipython_shell.kernel.interpreter
        self.shell = ipython_shell
        self.shell.displayhook.publish_execution_error = None
        self.execution_count = 0

    def _get_parent_header(self):
        return self.shell.kernel._parent_header

    def _set_parent_header(self, header):
        self.shell.kernel._parent_header = header

    _parent_header = property(_get_parent_header, _set_parent_header)

    def get_parent(self):
        return self.shell.kernel.get_parent()

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
        self.execution_count = 0
        self.shell.exit_now = False

    def set_parent(self, ident, parent):
        """Overridden from parent to tell the display hook and output streams about the parent message."""
        self.shell.set_parent(parent)

    def do_shutdown(self, restart):
        self.execution_count = 0
        self.shell.exit_now = True

    def send_display_data(self, data=None, metadata=None, display_id=None):
        if isinstance(data, str):
            self.shell.display_pub.publish(**{"data": {"text/plain": data}})
        else:
            self.shell.display_pub.publish(
                **{
                    "data": data or {},
                    "metadata": metadata or {},
                    "transient": {"display_id": display_id},
                },
            )

    def send_update_display_data(self, data=None, metadata=None, display_id=None):
        self.shell.display_pub.publish(
            **{
                "data": data or {},
                "metadata": metadata or {},
                "transient": {"display_id": display_id},
                "update": True,
            },
        )

    def send_execute_result(self, data=None, metadata=None, display_id=None):
        self.shell.displayhook.publish_execution_result(
            self.execution_count,
            data or {},
            metadata or {},
            display_id and {"display_id": display_id} or {},
        )

    def send_error(self, content=None):
        self.shell.displayhook.publish_execution_error(
            f"{content['ename']}",
            f"{content['evalue']}",
            f"{content['traceback']}",
        )

    def inspect(self, code, cursor_pos, detail_level):
        return self.do_inspect(code, cursor_pos, detail_level)

    def is_complete(self, code, cursor_pos):
        result = self.do_complete(code, cursor_pos)
        if result["cursor_start"] != result["cursor_end"]:
            result["status"] = "incomplete"
            result["indent"] = " " * (
                len(code[: result["cursor_end"]])
                - len(code[: result["cursor_end"]].lstrip())
            )
        return result

    def complete(self, code, cursor_pos):
        return self.do_complete(code, cursor_pos)

    def run(self, code):
        self.execution_count += 1
        return self.do_execute(code, silent=False)
