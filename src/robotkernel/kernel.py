# -*- coding: utf-8 -*-
from collections import OrderedDict  # noqa
from IPython.utils.tokenutil import line_at_cursor
from robot.libdocpkg.builder import RESOURCE_EXTENSIONS
from robot.parsing import populators
from robot.parsing import TEST_EXTENSIONS
from robotkernel import __version__
from robotkernel.constants import CONTEXT_LIBRARIES
from robotkernel.constants import VARIABLE_REGEXP
from robotkernel.display import DisplayKernel
from robotkernel.executors import execute_python
from robotkernel.executors import execute_robot
from robotkernel.executors import parse_robot
from robotkernel.listeners import AppiumConnectionsListener
from robotkernel.listeners import RobotKeywordsIndexerListener
from robotkernel.listeners import RobotVariablesListener
from robotkernel.listeners import SeleniumConnectionsListener
from robotkernel.listeners import WhiteLibraryListener
from robotkernel.nbreader import NotebookReader
from robotkernel.selectors import clear_selector_highlights
from robotkernel.selectors import get_autoit_selector_completions
from robotkernel.selectors import get_selector_completions
from robotkernel.selectors import get_white_selector_completions
from robotkernel.selectors import is_autoit_selector
from robotkernel.selectors import is_selector
from robotkernel.selectors import is_white_selector
from robotkernel.utils import detect_robot_context
from robotkernel.utils import get_keyword_doc
from robotkernel.utils import get_lunr_completions
from robotkernel.utils import lunr_builder
from robotkernel.utils import lunr_query
from robotkernel.utils import scored_results
from robotkernel.utils import yield_current_connection
from traceback import format_exc
import re
import robot
import sys
import uuid


try:
    import nbimporter  # noqa

    HAS_NBIMPORTER = True
except ImportError:
    HAS_NBIMPORTER = False


# noinspection PyAbstractClass
class RobotKernel(DisplayKernel):
    implementation = "IRobot"
    implementation_version = __version__
    language = "robotframework"
    language_version = robot.__version__
    language_info = {
        "mimetype": "text/plain",
        "name": "robotframework",
        "file_extension": ".robot",
        "codemirror_mode": "robotframework",
        "pygments_lexer": "robotframework",
    }
    banner = "Robot Framework kernel"

    def __init__(self, **kwargs):
        super(RobotKernel, self).__init__(**kwargs)
        # Enable nbreader
        if "ipynb" not in populators.READERS:
            populators.READERS["ipynb"] = NotebookReader
            TEST_EXTENSIONS.add("ipynb")
            RESOURCE_EXTENSIONS.add("ipynb")

        # History to repeat after kernel restart
        self.robot_history = OrderedDict()
        self.robot_cell_id = None  # current cell id from init_metadata
        self.robot_inspect_data = {}
        self.robot_variables = []
        self.robot_suite_variables = {}

        # Sticky connection cache (e.g. for webdrivers)
        self.robot_connections = []

        # Searchable index for keyword autocomplete documentation
        builder = lunr_builder("dottedname", ["dottedname", "name"])
        self.robot_catalog = {
            "builder": builder,
            "index": None,
            "libraries": [],
            "keywords": {},
        }
        populator = RobotKeywordsIndexerListener(self.robot_catalog)
        populator.library_import("BuiltIn", {})
        for name, keywords in CONTEXT_LIBRARIES.items():
            # noinspection PyProtectedMember
            populator._library_import(keywords, name)

    def do_shutdown(self, restart):
        super(RobotKernel, self).do_shutdown(restart)
        self.robot_history = OrderedDict()
        self.robot_variables = []
        self.robot_suite_variables = {}
        for driver in self.robot_connections:
            if hasattr(driver["instance"], "quit"):
                driver["instance"].quit()
        self.robot_connections = []

    def do_complete(self, code, cursor_pos):
        cursor_pos = cursor_pos is None and len(code) or cursor_pos
        line, offset = line_at_cursor(code, cursor_pos)
        line_cursor = cursor_pos - offset
        needle = re.split(r"\s{2,}|\t| \| ", line[:line_cursor])[-1].lstrip()

        if needle and needle[0] in "$@&%":  # is variable completion
            matches = [
                m["ref"]
                for m in scored_results(
                    needle,
                    [
                        dict(ref=v)
                        for v in (self.robot_variables + VARIABLE_REGEXP.findall(code))
                    ],
                )
                if needle.lower() in m["ref"].lower()
            ]
            if len(line) > line_cursor and line[line_cursor] == "}":
                cursor_pos += 1
                needle += "}"
        elif is_selector(needle):
            matches = []
            for driver in yield_current_connection(
                self.robot_connections, ["selenium", "appium"]
            ):
                matches = get_selector_completions(needle.rstrip(), driver)
        elif is_autoit_selector(needle):
            matches = get_autoit_selector_completions(needle)
        elif is_white_selector(needle):
            matches = get_white_selector_completions(needle)
        else:
            # Clear selector completion highlights
            for driver in yield_current_connection(
                self.robot_connections, ["selenium"]
            ):
                clear_selector_highlights(driver)
            context = detect_robot_context(code, cursor_pos)
            matches = get_lunr_completions(
                needle,
                self.robot_catalog["index"],
                self.robot_catalog["keywords"],
                context,
            )

        return {
            "matches": matches,
            "cursor_end": cursor_pos,
            "cursor_start": cursor_pos - len(needle),
            "metadata": {},
            "status": "ok",
        }

    def do_inspect(self, code, cursor_pos, detail_level=0):
        cursor_pos = cursor_pos is None and len(code) or cursor_pos
        line, offset = line_at_cursor(code, cursor_pos)
        line_cursor = cursor_pos - offset
        needle = re.split(r"\s{2,}|\t| \| ", line[:line_cursor])[-1].lstrip()
        needle = needle.strip().lower()

        reply_content = {
            "status": "ok",
            "data": self.robot_inspect_data,
            "metadata": {},
            "found": bool(self.robot_inspect_data),
        }

        results = []
        if needle and lunr_query(needle):
            query = lunr_query(needle)
            results = self.robot_catalog["index"].search(query)
            results += self.robot_catalog["index"].search(query.strip("*"))
        for result in results:
            keyword = self.robot_catalog["keywords"][result["ref"]]
            if needle not in [keyword.name.lower(), result["ref"].lower()]:
                continue
            self.robot_inspect_data.update(get_keyword_doc(keyword))
            reply_content["found"] = True
            break

        return reply_content

    def init_metadata(self, parent):
        # Jupyter Lab sends deleted cells and the currently updated cell
        # id as message metadata, that allows to keep robot history in
        # sync with the displayed notebook:
        deleted_cells = (parent.get("metadata") or {}).get("deletedCells") or []
        for cell_id in deleted_cells:
            if cell_id in self.robot_history:
                del self.robot_history[cell_id]
        self.robot_cell_id = (parent.get("metadata") or {}).get("cellId") or None
        return super(RobotKernel, self).init_metadata(parent)

    def do_execute(
        self, code, silent, store_history=True, user_expressions=None, allow_stdin=False
    ):
        # Reload ipynb modules
        if HAS_NBIMPORTER:
            for name, module in tuple(sys.modules.items()):
                if "nbimporter.NotebookLoader" in repr(module):
                    del sys.modules[name]

        # Clear selector completion highlights
        for driver in yield_current_connection(self.robot_connections, ["selenium"]):
            clear_selector_highlights(driver)

        # Support %%python module ModuleName cell magic
        match = re.match("^%%python module ([a-zA-Z_]+)", code)
        if match is not None:
            module = match.groups()[0]
            return execute_python(
                self,
                code[len("%%python module {0:s}".format(module)) :],
                module,
                silent,
            )
        else:
            # Update variables
            self.robot_variables = []
            for historical in self.robot_history.values():
                self.robot_variables.extend(
                    VARIABLE_REGEXP.findall(historical, re.U & re.M)
                )
            self.robot_variables.extend(VARIABLE_REGEXP.findall(code, re.U & re.M))

            # Populate
            try:
                data = parse_robot(code, self.robot_history)
            except Exception as e:
                if not silent:
                    self.send_error(
                        {
                            "ename": e.__class__.__name__,
                            "evalue": str(e),
                            "traceback": list(format_exc().splitlines()),
                        }
                    )
                return {
                    "status": "error",
                    "ename": e.__class__.__name__,
                    "evalue": str(e),
                    "traceback": list(format_exc().splitlines()),
                }

            # Update catalog
            keywords_indexer = RobotKeywordsIndexerListener(self.robot_catalog)
            # noinspection PyProtectedMember
            keywords_indexer._import_from_suite_data(data)

            listeners = [
                SeleniumConnectionsListener(self.robot_connections),
                AppiumConnectionsListener(self.robot_connections),
                WhiteLibraryListener(self.robot_connections),
                RobotKeywordsIndexerListener(self.robot_catalog),
                RobotVariablesListener(self.robot_suite_variables),
            ]

            # Execute test case
            result = execute_robot(
                self,
                code,
                data,  # passing history would be proper, but waste parsing
                listeners,
                silent,
            )

            # Save history
            if result["status"] == "ok":
                self.robot_history[self.robot_cell_id or str(uuid.uuid4())] = code

            return result


if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=RobotKernel)
