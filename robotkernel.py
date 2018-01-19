# -*- coding: utf-8 -*-
import os
from io import StringIO
from io import BytesIO

from ipykernel.kernelbase import Kernel

from robot.errors import DataError
from robot.libraries.BuiltIn import BuiltIn
from robot.output import LOGGER
from robot.parsing import TestData, TestCaseFile
from robot.parsing.model import TestCaseTable
from robot.parsing.populators import FromFilePopulator
from robot.parsing.tablepopulators import NullPopulator
from robot.parsing.txtreader import TxtReader
from robot.running import TestCase, TestSuiteBuilder
from robot.utils import get_error_message


class RobotKernel(Kernel):
    implementation = 'IRobot'
    implementation_version = '1.0'
    language = 'robotframework'
    language_version = '1.0'
    language_info = {
        'mimetype': 'text/plain',
        'name': 'robotframework',
        'file_extension': '.robot',
        'pygments_lexer': 'robotframework'
    }
    banner = 'Robot Framework kernel'

    def __init__(self, **kwargs):
        super(RobotKernel, self).__init__(**kwargs)
        self._history = []

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):

        self._history.append(code)
        data = TestCaseString(code)
        for source in self._history:
            data.populate(source)
        builder = TestSuiteBuilder()
        suite = builder._build_suite(data)
        if suite.tests:
            suite.run()

        if not silent:
            stream_content = {'name': 'stdout', 'text': code}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        return {
            'status': 'ok',
            # The base class increments the execution count
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

    def do_shutdown(self, restart):
        #try:
        #    BuiltIn().get_library_instance('SeleniumLibrary').close_all_browsers()
        #except Exception:
        #    pass
        self._history = []


class TestCaseString(TestCaseFile):
    # noinspection PyMethodOverriding
    def populate(self, source):
        FromStringPopulator(self).populate(source)
        # self._validate()
        return self


class FromStringPopulator(FromFilePopulator):
    # noinspection PyMissingConstructor
    def __init__(self, datafile):
        self._datafile = datafile
        self._populator = NullPopulator()
        self._curdir = os.getcwd()  # should probably be tmp or jupyter rundir

    def populate(self, source):
        LOGGER.info("Parsing string '%s'." % source)
        try:
            TxtReader().read(BytesIO(source.encode('utf-8')), self)
        except Exception:
            raise DataError(get_error_message())


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=RobotKernel)
