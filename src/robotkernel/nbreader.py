# -*- coding: utf-8 -*-
from io import BytesIO
from robot import run_cli
from robot.errors import DataError
from robot.libdoc import libdoc_cli
from robot.libdocpkg.builder import RESOURCE_EXTENSIONS
from robot.parsing import populators
from robot.parsing import TEST_EXTENSIONS
from robot.parsing.robotreader import RobotReader

import sys


def NotebookReader():  # noqa: N802
    try:
        import nbformat
    except ImportError:
        raise DataError(
            'Using Notebook test data requires having '
            '"nbformat" module version 4.4.0 or newer installed.',
        )

    class NotebookReader(object):
        def read(self, ipynbfile, rawdata):
            notebook = nbformat.read(ipynbfile, 4)
            data = '\n\n'.join([
                cell.source
                for cell in notebook.cells
                if cell.cell_type == 'code'
            ])
            robotfile = BytesIO(data.encode('UTF-8'))
            return RobotReader().read(robotfile, rawdata, ipynbfile.name)

    return NotebookReader()


def robot():
    # Enable nbreader
    if 'ipynb' not in populators.READERS:
        populators.READERS['ipynb'] = NotebookReader
        TEST_EXTENSIONS.add('ipynb')
        RESOURCE_EXTENSIONS.add('ipynb')
    return run_cli(sys.argv[1:])


def libdoc():
    # Enable nbreader
    if 'ipynb' not in populators.READERS:
        populators.READERS['ipynb'] = NotebookReader
        TEST_EXTENSIONS.add('ipynb')
        RESOURCE_EXTENSIONS.add('ipynb')
    return libdoc_cli(sys.argv[1:])
