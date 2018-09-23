# -*- coding: utf-8 -*-
from io import BytesIO
from io import StringIO
from ipykernel.kernelbase import Kernel
from IPython.utils.tempdir import TemporaryDirectory
from PIL import Image
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from robot.errors import DataError
from robot.output import LOGGER
from robot.parsing import TestCaseFile
from robot.parsing.model import _TestData
from robot.parsing.model import KeywordTable
from robot.parsing.model import TestCaseFileSettingTable
from robot.parsing.populators import FromFilePopulator
from robot.parsing.settings import Fixture
from robot.parsing.tablepopulators import NullPopulator
from robot.parsing.txtreader import TxtReader
from robot.reporting import ResultWriter
from robot.running import TestSuiteBuilder
from robot.utils import get_error_message
from robotkernel import __version__
from traceback import format_exc

import base64
import inspect
import json
import os
import pygments
import re
import robot
import sys
import types
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
        mimetype,
        base64.b64encode(data).decode('utf-8'),
    )


def highlight(language, data):
    lexer = get_lexer_by_name(language)
    formatter = HtmlFormatter(noclasses=True, nowrap=True)
    return pygments.highlight(data, lexer, formatter)


class StatusEventListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, callback):
        self.callback = callback

    # noinspection PyUnusedLocal
    def end_keyword(self, name, attributes):
        self.callback(attributes['status'])


class ReturnValueListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, callback):
        self.callback = callback
        self.return_value = None

    # noinspection PyUnusedLocal
    def end_keyword(self, name, attributes):
        frame = inspect.currentframe()
        while frame is not None:
            if 'return_value' in frame.f_locals:
                self.return_value = frame.f_locals.get('return_value')
                break
            frame = frame.f_back

    # noinspection PyUnusedLocal
    def start_test(self, name, attributes):
        self.return_value = None

    # noinspection PyUnusedLocal
    def end_test(self, name, attributes):
        self.callback(self.return_value)


# noinspection PyAbstractClass
class RobotKernel(Kernel):
    implementation = 'IRobot'
    implementation_version = __version__
    language = 'robotframework'
    language_version = robot.__version__
    language_info = {
        'mimetype': 'text/plain',
        'name': 'robotframework',
        'file_extension': '.robot',
        'codemirror_mode': 'robotframework',
        'pygments_lexer': 'robotframework',
    }
    banner = 'Robot Framework kernel'

    def __init__(self, **kwargs):
        super(RobotKernel, self).__init__(**kwargs)
        self.robot_history = []

    def do_shutdown(self, restart):
        self.robot_history = []

    def do_execute(
            self,
            code,
            silent,
            store_history=True,
            user_expressions=None,
            allow_stdin=False,
    ):
        # Support %%python module ModuleName cell magic
        match = re.match('^%%python module ([a-zA-Z_]+)', code)
        if match is not None:
            module = match.groups()[0]
            return self.do_execute_python(
                code[len('%%python module {0:s}'.format(module)):],
                module,
                silent,
                store_history,
                user_expressions,
                allow_stdin,
            )
        # Populate
        data = TestCaseString()
        try:
            for historical in self.robot_history:
                data.populate(historical)
            data.testcase_table.tests.clear()
            data.populate(code)
        except Exception as e:
            if not silent:
                self.send_error({
                    'ename': e.__class__.__name__,
                    'evalue': str(e),
                    'traceback': list(format_exc().splitlines()),
                })
            return {
                'status': 'error',
                'ename': e.__class__.__name__,
                'evalue': str(e),
                'traceback': list(format_exc().splitlines()),
            }

        # Build
        builder = TestSuiteBuilder()
        suite = builder._build_suite(data)
        suite._name = 'Jupyter'

        # Run
        if suite.tests:
            reply = self.run_robot_suite(suite, silent)
        else:
            reply = {
                'status': 'ok',
                'execution_count': self.execution_count,
            }

        # Save history
        if reply['status'] == 'ok':
            self.robot_history.append(code)

        return reply

    def do_execute_python(
            self,
            code,
            module,
            silent,
            store_history=True,
            user_expressions=None,
            allow_stdin=False,
    ):
        if module not in sys.modules:
            sys.modules[module] = types.ModuleType(module)
        try:
            exec(code, sys.modules[module].__dict__)
            return {'status': 'ok', 'execution_count': self.execution_count}
        except Exception as e:
            if not silent:
                self.send_error({
                    'ename': e.__class__.__name__,
                    'evalue': str(e),
                    'traceback': list(format_exc().splitlines()),
                })
            return {
                'status': 'error',
                'ename': e.__class__.__name__,
                'evalue': str(e),
                'traceback': list(format_exc().splitlines()),
            }

    def run_robot_suite(self, suite, silent):
        with TemporaryDirectory() as path:
            return self._run_robot_suite(suite, silent, path)

    def _run_robot_suite(self, suite, silent, path):
        listener = []
        display_id = str(uuid.uuid4())
        return_values = []

        def update_progress(progress_, status):
            progress_.append({'PASS': '.'}.get(status, 'F'))
            return progress_

        # Init status
        if not silent:
            self.send_display_data({'text/plain': '.'}, display_id=display_id)
            listener.append(
                StatusEventListener(
                    lambda s: self.send_update_display_data(
                        {
                            'text/plain': ''.
                            join(update_progress(progress, s)),
                        },
                        display_id=display_id,
                    ),
                ),
            )
            listener.append(
                ReturnValueListener(lambda v: return_values.append(v)),
            )

        # Run suite
        stdout = StringIO()
        progress = []
        results = suite.run(outputdir=path, stdout=stdout, listener=listener)
        stats = results.statistics

        # Reply error on error
        if stats.total.critical.failed:
            if not silent:
                self.send_error({
                    'ename': '',
                    'evalue': '',
                    'traceback': stdout.getvalue().splitlines(),
                })

        # Display result of the last keyword, if it was JSON
        elif return_values and return_values[-1] and not silent:
            try:
                result = json.dumps(
                    json.loads(return_values[-1].strip()),
                    sort_keys=False,
                    indent=4,
                )
                self.send_execute_result({
                    'text/html': '<pre>{}</pre>'.format(
                        highlight('json', result),
                    ),
                })
            except (AttributeError, ValueError):
                pass

        # Process screenshots
        self.process_screenshots(path, silent)

        # Generate report
        writer = ResultWriter(os.path.join(path, 'output.xml'))
        writer.write_results(
            log=os.path.join(path, 'log.html'),
            report=os.path.join(path, 'report.html'),
        )

        with open(os.path.join(path, 'log.html'), 'rb') as fp:
            log = fp.read()
            log = log.replace(
                b'"reportURL":"report.html"',
                b'"reportURL":null',
            )

        with open(os.path.join(path, 'report.html'), 'rb') as fp:
            report = fp.read()
            report = report.replace(b'"logURL":"log.html"', b'"logURL":null')

        # Clear status and display results
        if not silent:
            self.send_update_display_data(
                {
                    'text/html': ''
                    '<a href="{}">Log</a> | <a href="{}">Report</a>'.
                    format(javascript_uri(log), javascript_uri(report)),
                },
                display_id=display_id,
            )

        # Reply ok on pass
        if stats.total.critical.failed:
            return {
                'status': 'error',
                'ename': '',
                'evalue': '',
                'traceback': stdout.getvalue().splitlines(),
            }
        else:
            return {
                'status': 'ok',
                'execution_count': self.execution_count,
            }

    def process_screenshots(self, path, silent):
        with open(os.path.join(path, 'output.xml')) as fp:
            xml = fp.read()
        for src in [name for name in re.findall('img src="([^"]+)', xml)
                    if os.path.exists(os.path.join(path, name))]:
            im = Image.open(os.path.join(path, src))
            mimetype = Image.MIME[im.format]
            with open(os.path.join(path, src), 'rb') as fp:
                data = fp.read()
            uri = data_uri(mimetype, data)
            xml = xml.replace('a href="{}"'.format(src), 'a')
            xml = xml.replace(
                'img src="{}" width="800px"'.format(src),
                'img src="{}" style="max-width:800px;"'.format(uri),
            )  # noqa: E501
            xml = xml.replace(
                'img src="{}"'.format(src),
                'img src="{}"'.format(uri),
            )
            if not silent:
                self.send_display_data({
                    mimetype: base64.b64encode(data).decode('utf-8'),
                }, {mimetype: {
                    'height': im.height,
                    'width': im.width,
                }})
        with open(os.path.join(path, 'output.xml'), 'w') as fp:
            fp.write(xml)

    def send_error(self, content=None):
        self.send_response(self.iopub_socket, 'error', content)

    def send_display_data(self, data=None, metadata=None, display_id=None):
        if isinstance(data, str):
            self.send_response(
                self.iopub_socket,
                'display_data',
                {'data': {
                    'text/plain': data,
                }},
            )
        else:
            self.send_response(
                self.iopub_socket,
                'display_data',
                {
                    'data': data or {},
                    'metadata': metadata or {},
                    'transient': {
                        'display_id': display_id,
                    },
                },
            )

    def send_update_display_data(
            self,
            data=None,
            metadata=None,
            display_id=None,
    ):
        self.send_response(
            self.iopub_socket,
            'update_display_data',
            {
                'data': data or {},
                'metadata': metadata or {},
                'transient': {
                    'display_id': display_id,
                },
            },
        )

    def send_execute_result(self, data=None, metadata=None, display_id=None):
        self.send_response(
            self.iopub_socket,
            'execute_result',
            {
                'data': data or {},
                'metadata': metadata or {},
                'transient': {
                    'display_id': display_id,
                },
                'execution_count': self.execution_count,
            },
        )


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
