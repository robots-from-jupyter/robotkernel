# -*- coding: utf-8 -*-
from io import BytesIO
from robot.errors import DataError
from robot.libdocpkg.builder import RESOURCE_EXTENSIONS
from robotkernel.constants import HAS_RF32_PARSER
import os
import re
import sys
import types


if HAS_RF32_PARSER:
    from robot.parsing.lexerwrapper import LexerWrapper
    from robot.running import importer
else:
    from robot.parsing import populators
    from robot.parsing import TEST_EXTENSIONS
    from robot.parsing.robotreader import RobotReader


def exec_code_into_module(code, module):
    if module not in sys.modules:
        sys.modules[module] = types.ModuleType(module)
    exec(code, sys.modules[module].__dict__)


def NotebookReader():  # noqa: N802
    try:
        import nbformat  # noqa
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

            if HAS_RF32_PARSER:
                return data
            else:
                robotfile = BytesIO(data.encode("UTF-8"))
                return RobotReader().read(robotfile, rawdata, ipynbfile.name)

    return NotebookReader()


def ipynb_read(old):
    def _read(self, path):
        if os.path.splitext(path)[1].lower() == ".ipynb":
            return NotebookReader().read(path, "")
        else:
            return old(self, path)

    return _read


def inject_libdoc_ipynb_support():
    RESOURCE_EXTENSIONS.add("ipynb")


def inject_robot_ipynb_support():
    # Enable nbreader
    if HAS_RF32_PARSER:
        # noinspection PyNoneFunctionAssignment,PyProtectedMember
        LexerWrapper._read = ipynb_read(LexerWrapper._read)
        importer.RESOURCE_EXTENSIONS += (".ipynb",)
    elif "ipynb" not in populators.READERS:
        populators.READERS["ipynb"] = NotebookReader
        TEST_EXTENSIONS.add("ipynb")
