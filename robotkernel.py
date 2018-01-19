# -*- coding: utf-8 -*-
import os
from io import BytesIO

from ipykernel.kernelbase import Kernel

from robot.errors import DataError
from robot.output import LOGGER
from robot.parsing import TestCaseFile
from robot.parsing.populators import FromFilePopulator
from robot.parsing.tablepopulators import NullPopulator
from robot.parsing.txtreader import TxtReader
from robot.running import TestSuiteBuilder
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
        'codemirror_mode': 'robotframework',
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
        for source in self._history[:-1]:
            data.populate(source)
        data.testcase_table.tests.clear()
        data.populate(self._history[-1])

        builder = TestSuiteBuilder()
        suite = builder._build_suite(data)

        if suite.tests:
            if not silent:
                self.send_response(self.iopub_socket, 'stream', {
                    'name': 'stdout',
                    'text': 'Running...\n'
                })
            results = suite.run()
            if not silent:
                stats = results.statistics
                self.send_response(self.iopub_socket, 'stream', {
                    'name': 'stdout',
                    'text': 'Critical failed: {}\n'.format(
                        stats.total.critical.failed)
                })
                self.send_response(self.iopub_socket, 'stream', {
                    'name': 'stdout',
                    'text': 'Critical passed: {}\n'.format(
                        stats.total.critical.passed)
                })
        else:
            self.send_response(self.iopub_socket, 'stream', {
                'name': 'stdout',
                'text': 'No test cases'
            })

        return {
            'status': 'ok',
            # The base class increments the execution count
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

    def do_shutdown(self, restart):
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
