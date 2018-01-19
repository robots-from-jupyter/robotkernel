# -*- coding: utf-8 -*-
import os
import uuid
from io import BytesIO
from io import StringIO

from ipykernel.kernelbase import Kernel

from robot.errors import DataError
from robot.output import LOGGER
from robot.parsing import TestCaseFile
from robot.parsing.populators import FromFilePopulator
from robot.parsing.tablepopulators import NullPopulator
from robot.parsing.txtreader import TxtReader
from robot.reporting import ResultWriter
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
        self.robot_history = []
        self.display_id = None

    def send_display_data(self, data=None, silent=False):
        if not silent:
            self._send_display_data(data)

    def _send_display_data(self, data=None):
        if self.display_id:
            message = 'update_display_data'
        else:
            message = 'display_data'
        if not self.display_id:
            self.display_id = str(uuid.uuid4())
        self.send_response(self.iopub_socket, message, {
            'data': data or {},
            'metadata': {},
            'transient': {'display_id': self.display_id}
        })

    def send_execute_result(self, data=None, metadata=None):
        self.send_response(self.iopub_socket, 'execute_result', {
            'data': data or {},
            'metadata': metadata or {},
            'transient': {'display_id': self.display_id},
            'execution_count': self.execution_count
        })

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        self.display_id = None
        status = 'ok'

        # Populate
        data = TestCaseString()
        for historical in self.robot_history:
            data.populate(historical)
        data.testcase_table.tests.clear()
        data.populate(code)

        # Build
        builder = TestSuiteBuilder()
        suite = builder._build_suite(data)
        suite._name = 'Jupyter'

        if suite.tests:
            self.send_display_data({'text/plain': '...'})

            # Execute
            stdout = StringIO()
            results = suite.run(output='output.xml', stdout=stdout)
            writer = ResultWriter('output.xml')
            writer.write_results()
            stats = results.statistics

            # Toggle status on error
            if stats.total.critical.failed:
                status = 'error'
                self.send_display_data({'text/plain': stdout.getvalue()})
                self.display_id = False

            # Clear status and send result
            self.send_display_data({
                'text/html':
                '<a href="report.html" target="_blank">Test Report</a>'
            })

        # Save history
        if status == 'ok':
            self.robot_history.append(code)
        return {
            'status': status,
            'execution_count': self.execution_count
        }

    def do_shutdown(self, restart):
        self.robot_history = []
        self.display_id = None


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
