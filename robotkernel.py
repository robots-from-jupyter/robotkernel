# -*- coding: utf-8 -*-
from io import BytesIO
from io import StringIO
from ipykernel.kernelbase import Kernel
from PIL import Image
from robot.errors import DataError
from robot.output import LOGGER
from robot.parsing import TestCaseFile
from robot.parsing.model import KeywordTable
from robot.parsing.model import TestCaseFileSettingTable
from robot.parsing.model import _TestData
from robot.parsing.populators import FromFilePopulator
from robot.parsing.settings import Fixture
from robot.parsing.tablepopulators import NullPopulator
from robot.parsing.txtreader import TxtReader
from robot.reporting import ResultWriter
from robot.running import TestSuiteBuilder
from robot.utils import get_error_message

import base64
import os
import re
import shutil
import tempfile
import uuid


def javascript_uri(html):
    """Because data-uri for text/html is not supported by IE"""
    if isinstance(html, str):
        html = html.encode('utf-8')
    return (
        'javascript:(function(){{'
        'var w=window.open();'
        'w.document.open();'
        'w.document.write(window.atob(\'{}\'));'
        'w.document.close();'
        '}})();" '.format(base64.b64encode(html).decode('utf-8'))
    )


def data_uri(mimetype, data):
    return 'data:{};base64,{}'.format(
        mimetype, base64.b64encode(data).decode('utf-8'))


class TemporaryDirectory(object):
    def __enter__(self):
        self.name = tempfile.mkdtemp()
        return self.name

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self.name)


class StatusEventListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, callback):
        self.callback = callback

    # noinspection PyUnusedLocal
    def end_keyword(self, name, attributes):
        self.callback(attributes['status'])


# noinspection PyAbstractClass
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

    def do_shutdown(self, restart):
        self.robot_history = []

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):

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

        # Run
        if suite.tests:
            status = self.run_robot_suite(suite, silent)
        else:
            status = 'ok'

        # Save history
        if status == 'ok':
            self.robot_history.append(code)
        return {
            'status': status,
            'execution_count': self.execution_count
        }

    def run_robot_suite(self, suite, silent):
        with TemporaryDirectory() as path:
            return self._run_robot_suite(suite, silent, path)

    def _run_robot_suite(self, suite, silent, path):
        listener = []
        status = 'ok'
        display_id = str(uuid.uuid4())

        def update_progress(progress_, status_):
            progress_.append({'PASS': '.'}.get(status_, 'F'))
            return progress_

        # Init status
        if not silent:
            self.send_display_data({'text/plain': '.'}, display_id=display_id)
            listener.append(StatusEventListener(
                lambda s: self.send_update_display_data({
                    'text/plain': ''.join(update_progress(progress, s))
                }, display_id=display_id))
            )

        # Run suite
        stdout = StringIO()
        progress = []
        results = suite.run(outputdir=path, stdout=stdout, listener=listener)
        stats = results.statistics

        # Toggle status on error
        if stats.total.critical.failed:
            status = 'error'

        # Display console log
        if stats.total.critical.failed and not silent:
            self.send_display_data({'text/plain': stdout.getvalue()})

        # Process screenshots
        self.process_screenshots(path, silent)

        # Generate report
        writer = ResultWriter(os.path.join(path, 'output.xml'))
        writer.write_results(log=os.path.join(path, 'log.html'),
                             report=os.path.join(path, 'report.html'))

        with open(os.path.join(path, 'log.html'), 'rb') as fp:
            log = fp.read()
            log = log.replace(b'"reportURL":"report.html"',
                              b'"reportURL":null')

        with open(os.path.join(path, 'report.html'), 'rb') as fp:
            report = fp.read()
            report = report.replace(b'"logURL":"log.html"',
                                    b'"logURL":null')

        # Clear status and send result
        if not silent:
            self.send_update_display_data({
                'text/html':
                    '<a href="{}">Log</a> | <a href="{}">Report</a>'
                    .format(javascript_uri(log), javascript_uri(report))
            }, display_id=display_id)

        return status

    def process_screenshots(self, path, silent):
        with open(os.path.join(path, 'output.xml')) as fp:
            xml = fp.read()
        for src in re.findall('img src="([^"]+)', xml):
            im = Image.open(os.path.join(path, src))
            mimetype = Image.MIME[im.format]
            with open(os.path.join(path, src), 'rb') as fp:
                data = fp.read()
            uri = data_uri(mimetype, data)
            xml = xml.replace('a href="{}"'.format(src), 'a')
            xml = xml.replace('img src="{}"'.format(src),
                              'img src="{}" style="width:100%;"'.format(uri))
            if not silent:
                self.send_display_data(
                    {mimetype: base64.b64encode(data).decode('utf-8')},
                    {mimetype: {'height': im.height, 'width': im.width}}
                )
        with open(os.path.join(path, 'output.xml'), 'w') as fp:
            fp.write(xml)

    def send_display_data(self, data=None, metadata=None, display_id=None):
        if isinstance(data, str):
            self.send_response(self.iopub_socket, 'display_data', {
                'data': {'text/plain': data}
            })
        else:
            self.send_response(self.iopub_socket, 'display_data', {
                'data': data or {},
                'metadata': metadata or {},
                'transient': {'display_id': display_id}
            })

    def send_update_display_data(self, data=None, metadata=None, display_id=None):  # noqa: E501
        self.send_response(self.iopub_socket, 'update_display_data', {
            'data': data or {},
            'metadata': metadata or {},
            'transient': {'display_id': display_id}
        })

    def send_execute_result(self, data=None, metadata=None, display_id=None):
        self.send_response(self.iopub_socket, 'execute_result', {
            'data': data or {},
            'metadata': metadata or {},
            'transient': {'display_id': display_id},
            'execution_count': self.execution_count
        })


class TestCaseString(TestCaseFile):
    # noinspection PyMissingConstructor
    def __init__(self, parent=None, source=None):
        super(TestCaseString, self).__init__(parent, source)
        self.setting_table = SafeSettingsTable(self)
        self.keyword_table = OverridingKeywordTable(self)
        _TestData.__init__(self, parent, source)

    # noinspection PyMethodOverriding
    def populate(self, source):
        FromStringPopulator(self).populate(source)
        return self


class SafeSettingsTable(TestCaseFileSettingTable):
    def __init__(self, parent):
        super(SafeSettingsTable, self).__init__(parent)
        self.suite_setup = OverridingFixture('Suite Setup', self)
        self.suite_teardown = OverridingFixture('Suite Teardown', self)
        self.test_setup = OverridingFixture('Test Setup', self)
        self.test_teardown = OverridingFixture('Test Teardown', self)


class OverridingFixture(Fixture):
    def populate(self, value, comment=None):
        # Always reset setting before populating it
        self.reset()
        super(OverridingFixture, self).populate(value, comment)


class OverridingKeywordTable(KeywordTable):
    def add(self, name):
        # Always clear previous definition
        for i in range(len(self.keywords)):
            if self.keywords[i].name == name:
                del self.keywords[i]
                break
        return super(OverridingKeywordTable, self).add(name)


class FromStringPopulator(FromFilePopulator):
    # noinspection PyMissingConstructor
    def __init__(self, datafile):
        self._datafile = datafile
        self._populator = NullPopulator()
        self._curdir = os.getcwd()  # Jupyter running directory for convenience

    def populate(self, source):
        LOGGER.info("Parsing string '%s'." % source)
        try:
            TxtReader().read(BytesIO(source.encode('utf-8')), self)
        except Exception:
            raise DataError(get_error_message())


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=RobotKernel)
