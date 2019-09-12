# -*- coding: utf-8 -*-
from io import BytesIO
from robot import run_cli
from robot.errors import DataError
from robot.libdoc import libdoc_cli
from robot.libdocpkg.builder import RESOURCE_EXTENSIONS
from robot.parsing import populators
from robot.parsing import TEST_EXTENSIONS
from robot.parsing.robotreader import RobotReader
import re
import sys
import types


try:
    import nbimporter

    nbimporter
except ImportError:
    pass


def exec_code_into_module(code, module):
    if module not in sys.modules:
        sys.modules[module] = types.ModuleType(module)
    exec(code, sys.modules[module].__dict__)


def NotebookReader():  # noqa: N802
    try:
        import nbformat
    except ImportError:
        raise DataError(
            "Using Notebook test data requires having "
            '"nbformat" module version 4.4.0 or newer installed.'
        )

    class NotebookReader(object):
        def read(self, ipynbfile, rawdata):
            notebook = nbformat.read(ipynbfile, 4)
            data = []

            for cell in notebook.cells:
                # Skip non-code cells
                if not cell.cell_type == "code":
                    continue

                # Execute %%python module magics
                match = re.match("^%%python module ([a-zA-Z_]+)", cell.source)
                if match is not None:
                    module = match.groups()[0]
                    cursor = len("%%python module {0:s}".format(module))
                    exec_code_into_module(cell.source[cursor:], module)
                    continue

                # Add the rest into robot test suite
                data.append(cell.source)

            data = "\n\n".join(data)
            robotfile = BytesIO(data.encode("UTF-8"))
            return RobotReader().read(robotfile, rawdata, ipynbfile.name)

    return NotebookReader()


def robot():
    # Enable nbreader
    if "ipynb" not in populators.READERS:
        populators.READERS["ipynb"] = NotebookReader
        TEST_EXTENSIONS.add("ipynb")
        RESOURCE_EXTENSIONS.add("ipynb")
    return run_cli(sys.argv[1:])


def libdoc():
    # Enable nbreader
    if "ipynb" not in populators.READERS:
        populators.READERS["ipynb"] = NotebookReader
        TEST_EXTENSIONS.add("ipynb")
        RESOURCE_EXTENSIONS.add("ipynb")
    return libdoc_cli(sys.argv[1:])
