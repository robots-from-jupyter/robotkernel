# -*- coding: utf-8 -*-
from pyolite import ipython_shell
from traitlets import Any
from traitlets import Instance


class DisplayKernel:
    """BaseKernel with interactive shell for display hooks."""

    def __init__(self, *args, **kwargs):
        self.display_pub = ipython_shell.display_pub
        self.displayhook = ipython_shell.displayhook
        self.displayhook.publish_execution_error = None
        self.shell = ipython_shell
        self.interpreter = ipython_shell.kernel.interpreter
        self.comm_manager = ipython_shell.kernel.comm_manager
        self.execution_count = 0

    def _get_parent_header(self):
        return self.shell.kernel._parent_header

    def _set_parent_header(self, header):
        self.shell.kernel._parent_header = header

    _parent_header = property(_get_parent_header, _set_parent_header)

    def get_parent(self):
        # TODO mimick ipykernel's get_parent signature
        # (take a channel parameter)
        return self._parent_header

    user_module = Any()

    def _user_module_changed(self, name, old, new):
        pass
        # if self.shell is not None:
        #     self.shell.user_module = new

    user_ns = Instance(dict, args=(), allow_none=True)

    def _user_ns_changed(self, name, old, new):
        pass
        # if self.shell is not None:
        #     self.shell.user_ns = new
        #     self.shell.init_user_ns()

    def start(self):
        pass
        # self.shell.exit_now = False
        # super(DisplayKernel, self).start()

    def set_parent(self, ident, parent):
        """Overridden from parent to tell the display hook and output streams about the parent message.
        """
        pass
        # super(DisplayKernel, self).set_parent(ident, parent)
        # self.shell.set_parent(parent)

    def do_shutdown(self, restart):
        pass
        # self.shell.exit_now = True

    def send_display_data(self, data=None, metadata=None, display_id=None):
        if isinstance(data, str):
            self.display_pub.publish(**{"data": {"text/plain": data}})
        else:
            self.display_pub.publish(
                **{
                    "data": data or {},
                    "metadata": metadata or {},
                    "transient": {"display_id": display_id},
                },
            )

    def send_update_display_data(self, data=None, metadata=None, display_id=None):
        self.display_pub.publish(
            **{
                "data": data or {},
                "metadata": metadata or {},
                "transient": {"display_id": display_id},
                "update": True,
            },
        )

    def send_execute_result(self, data=None, metadata=None, display_id=None):
        self.displayhook.publish_execution_result(
            self.execution_count, data or {}, metadata or {},
        )

    def send_error(self, content=None):
        self.displayhook.publish_execution_error(
            f"{content['ename']}", f"{content['evalue']}", f"{content['traceback']}",
        )

    def run(self, code):
        return self.do_execute(code, silent=False)

    def complete(self, code, cursor_pos):
        return self.do_complete(code, cursor_pos)
