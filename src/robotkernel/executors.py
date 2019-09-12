# -*- coding: utf-8 -*-
from collections import OrderedDict
from io import StringIO
from IPython.core.display import clear_output
from IPython.core.display import display
from PIL import Image
from robot.model import TestSuite
from robot.reporting import ResultWriter
from robot.running import TestSuiteBuilder
from robotkernel.display import DisplayKernel
from robotkernel.display import ProgressUpdater
from robotkernel.listeners import ReturnValueListener
from robotkernel.listeners import StatusEventListener
from robotkernel.model import TestCaseString
from robotkernel.utils import data_uri
from robotkernel.utils import javascript_uri
from robotkernel.utils import to_mime_and_metadata
from tempfile import TemporaryDirectory
from traceback import format_exc
from typing import Dict
from typing import List
from typing import Tuple
import base64
import ipywidgets
import os
import re
import sys
import types
import uuid


def execute_python(kernel: DisplayKernel, code: str, module: str, silent: bool):
    """"Execute Python code str in the context of named module.
    If the named module is not found, a new module is introduced.
    """
    if module not in sys.modules:
        sys.modules[module] = types.ModuleType(module)
    try:
        exec(code, sys.modules[module].__dict__)
        return {"status": "ok", "execution_count": kernel.execution_count}
    except Exception as e:
        if not silent:
            kernel.send_error(
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


def parse_robot(code: str, cell_history: Dict[str, str]):
    data = TestCaseString()
    for historical in cell_history.values():
        data.populate(historical)
    data.testcase_table.tests.clear()
    data.populate(code)
    return data


def normalize_argument(name):
    return re.sub(r"\W", "_", re.sub(r"^[^\w]*|[^\w]*$", "", name, re.U), re.U)


def execute_ipywidget(
    kernel: DisplayKernel,
    data: TestCaseString,
    listeners: list,
    silent: bool,
    display_id: str,
    name,
    arguments,
    values,
):
    header = getattr(data.testcase_table, "name", "Tasks") or "Tasks"
    table = f"""\
*** {header} ***

{name}
    {name}  {'  '.join([values[a[1]] for a in arguments])}
"""
    data.testcase_table.tests.clear()
    data.populate(table)

    # Build
    builder = TestSuiteBuilder()
    data.source = os.getcwd()  # allow Library and Resource from CWD work
    suite = builder._build_suite(data)
    suite._name = "Jupyter"

    with TemporaryDirectory() as path:
        run_robot_suite(kernel, suite, listeners, silent, display_id, path, widget=True)


def inject_ipywidget(
    kernel: DisplayKernel,
    data: TestCaseString,
    listeners: list,
    silent: bool,
    display_id: str,
    name: str,
    arguments: List[Tuple[str, str, str]],
):
    def execute(**values):
        execute_ipywidget(
            kernel, data, listeners, silent, display_id, name, arguments, values
        )

    widgets = []
    controls = OrderedDict()
    out = ipywidgets.widgets.Output()

    def update(*args):
        values = {key: control.value for key, control in controls.items()}
        with out:
            description = widgets[0].description
            widgets[0].description = "Executing..."
            for widget in widgets:
                widget.disabled = True
            clear_output(wait=True)
            try:
                execute(**values)
            finally:
                widgets[0].description = description
                for widget in widgets:
                    widget.disabled = False

    for arg in arguments:
        widgets.append(ipywidgets.widgets.Label(value=arg[1] + "="))
        widgets.append(ipywidgets.widgets.Text(value=arg[2]))
        controls[arg[1]] = widgets[-1]

    button = ipywidgets.widgets.Button(description=name)
    button.on_click(update)
    widgets.insert(0, button)

    # noinspection PyTypeChecker
    layout = ipywidgets.widgets.Layout(
        display="flex", flex_flow="row", flex_wrap="wrap", justify_content="flex-start"
    )

    ui = ipywidgets.widgets.Box(widgets, layout=layout)
    # noinspection PyTypeChecker
    display(ui, out, display_id=display_id)


def inject_ipywidgets(
    kernel: DisplayKernel,
    code: str,
    data: TestCaseString,
    listeners: list,
    silent: bool,
    display_id: str,
):
    code_data = parse_robot(code, {})
    for keyword in code_data.keywords:
        name = keyword.name
        arguments = []
        for arg in keyword.args:
            if "=" in arg:
                arg, default = arg.split("=", 1)
            else:
                arg, default = arg, None
            arguments.append((arg, normalize_argument(arg), default))
        inject_ipywidget(kernel, data, listeners, silent, display_id, name, arguments)


def execute_robot(
    kernel: DisplayKernel,
    code: str,
    data: TestCaseString,
    listeners: list,
    silent: bool,
):
    # Build
    builder = TestSuiteBuilder()
    data.source = os.getcwd()  # allow Library and Resource from CWD work
    suite = builder._build_suite(data)
    suite._name = "Jupyter"

    # Run
    display_id = str(uuid.uuid4())
    if suite.tests:
        with TemporaryDirectory() as path:
            reply = run_robot_suite(kernel, suite, listeners, silent, display_id, path)
    else:
        last_code = getattr(kernel, "_last_code", "")
        if code == last_code:
            setattr(kernel, "_last_code", "")
        else:
            inject_ipywidgets(kernel, code, data, listeners, silent, display_id)
            setattr(kernel, "_last_code", code)
        reply = {"status": "ok", "execution_count": kernel.execution_count}

    return reply


def run_robot_suite(
    kernel: DisplayKernel,
    suite: TestSuite,
    listeners: list,
    silent: bool,
    display_id: str,
    path: str,
    widget: bool = False,
):
    return_values = []
    if not (silent or widget):
        progress = ProgressUpdater(kernel, display_id, sys.__stdout__)
    else:
        progress = None

    # Init status
    listeners = listeners[:]
    if not (silent or widget):
        listeners.append(StatusEventListener(lambda data: progress.update(data)))
    if not silent:
        listeners.append(ReturnValueListener(lambda v: return_values.append(v)))

    stdout = StringIO()
    if progress is not None:
        sys.__stdout__ = progress
    try:
        results = suite.run(outputdir=path, stdout=stdout, listener=listeners)
    finally:
        if progress is not None:
            sys.__stdout__ = progress.stdout

    stats = results.statistics

    # Reply error on error
    if stats.total.critical.failed:
        if not silent:
            kernel.send_error(
                {"ename": "", "evalue": "", "traceback": stdout.getvalue().splitlines()}
            )

    # Display result of the last keyword
    elif (
        len(return_values)
        and return_values[-1] is not None
        and return_values[-1] != ""
        and return_values[-1] != b""
        and not silent
    ):  # this comparison is "numpy compatible"
        bundle, metadata = to_mime_and_metadata(return_values[-1])
        if bundle:
            kernel.send_execute_result(bundle, metadata)

    # Process screenshots
    process_screenshots(kernel, path, silent)

    # Generate report
    writer = ResultWriter(os.path.join(path, "output.xml"))
    writer.write_results(
        log=os.path.join(path, "log.html"),
        report=os.path.join(path, "report.html"),
        rpa=getattr(suite, "rpa", False),
    )

    with open(os.path.join(path, "log.html"), "rb") as fp:
        log = fp.read()
        log = log.replace(b'"reportURL":"report.html"', b'"reportURL":null')

    with open(os.path.join(path, "report.html"), "rb") as fp:
        report = fp.read()
        report = report.replace(b'"logURL":"log.html"', b'"logURL":null')

    # Clear status and display results
    if not silent:
        (widget and kernel.send_display_data or kernel.send_update_display_data)(
            {
                "text/html": ""
                '<p><a href="about:" onClick="{}">Log</a> | <a href="about:" onClick="{}">Report</a></p>'.format(
                    javascript_uri(log, "log.html"),
                    javascript_uri(report, "report.html"),
                )
            },
            display_id=display_id,
        )

    # Reply ok on pass
    if stats.total.critical.failed:
        return {
            "status": "error",
            "ename": "",
            "evalue": "",
            "traceback": stdout.getvalue().splitlines(),
        }
    else:
        return {"status": "ok", "execution_count": kernel.execution_count}


def process_screenshots(kernel: DisplayKernel, path: str, silent: bool):
    cwd = os.getcwd()
    with open(os.path.join(path, "output.xml")) as fp:
        xml = fp.read()
    for src in re.findall('img src="([^"]+)', xml):
        if os.path.exists(src):
            filename = src
        elif os.path.exists(os.path.join(path, src)):
            filename = os.path.join(path, src)
        elif os.path.exists(os.path.join(cwd, src)):
            filename = os.path.join(cwd, src)
        else:
            continue
        im = Image.open(filename)
        mimetype = Image.MIME[im.format]
        # Fix issue where Pillow on Windows returns APNG for PNG
        if mimetype == "image/apng":
            mimetype = "image/png"
        with open(filename, "rb") as fp:
            data = fp.read()
        uri = data_uri(mimetype, data)
        xml = xml.replace('a href="{}"'.format(src), "a")
        xml = xml.replace(
            'img src="{}" width="800px"'.format(src),
            'img src="{}" style="max-width:800px;"'.format(uri),
        )  # noqa: E501
        xml = xml.replace('img src="{}"'.format(src), 'img src="{}"'.format(uri))
        if not silent:
            kernel.send_display_data(
                {mimetype: base64.b64encode(data).decode("utf-8")},
                {mimetype: {"height": im.height, "width": im.width}},
            )
    with open(os.path.join(path, "output.xml"), "w") as fp:
        fp.write(xml)
