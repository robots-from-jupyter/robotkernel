# -*- coding: utf-8 -*-
from collections import OrderedDict
from io import StringIO
from ipykernel.kernelbase import Kernel
from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.tokenutil import line_at_cursor
from PIL import Image
from robot.libdocpkg.model import KeywordDoc
from robot.reporting import ResultWriter
from robot.running import TestSuiteBuilder
from robotkernel import __version__
from robotkernel.listeners import ReturnValueListener
from robotkernel.listeners import RobotKeywordsIndexerListener
from robotkernel.listeners import StatusEventListener
from robotkernel.listeners import WebdriverConnectionsListener
from robotkernel.model import TestCaseString
from robotkernel.utils import data_uri
from robotkernel.utils import detect_robot_context
from robotkernel.utils import get_keyword_doc
from robotkernel.utils import highlight
from robotkernel.utils import javascript_uri
from robotkernel.utils import lunr_builder
from robotkernel.utils import readable_keyword
from robotkernel.utils import scored_results
from traceback import format_exc

import base64
import json
import os
import re
import robot
import sys
import types
import uuid


CONTEXT_LIBRARIES = {
    '__root__': list(
        map(
            KeywordDoc,
            [
                '*** Settings ***',
                '*** Variables ***',
                '*** Test Cases ***',
                '*** Tasks ***',
                '*** Keywords ***',
            ],
        ),
    ),
    '__settings__': list(
        map(
            KeywordDoc,
            [
                '*** Settings ***',
                '*** Variables ***',
                '*** Test Cases ***',
                '*** Tasks ***',
                '*** Keywords ***',
                'Library',
                'Resource',
                'Variables',
                'Documentation',
                'Metadata',
                'Suite Setup',
                'Suite Teardown',
                'Test Setup',
                'Test Teardown',
                'Test Template',
                'Test Timeout',
                'Task Setup',
                'Task Teardown',
                'Task Template',
                'Task Timeout',
                'Force Tags',
                'Default Tags',
            ],
        ),
    ),
    '__tasks__': list(
        map(
            KeywordDoc,
            [
                '[Documentation]',
                '[Tags]',
                '[Setup]',
                '[Teardown]',
                '[Template]',
                '[Timeout]',
            ],
        ),
    ),
    '__keywords__': list(
        map(
            KeywordDoc,
            [
                '[Documentation]',
                '[Tags]',
                '[Arguments]',
                '[Return]',
                '[Teardown]',
                '[Timeout]',
            ],
        ),
    ),
}


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

        # History to repeat after kernel restart
        self.robot_history = OrderedDict()
        self.robot_cell_id = None  # current cell id from init_metadata
        self.robot_inspect_data = {}

        # Persistent storage for selenium library webdrivers
        self.robot_webdrivers = []

        # Searchable index for keyword autocomplete documentation
        builder = lunr_builder('dottedname', ['dottedname', 'name'])
        self.robot_catalog = {
            'builder': builder,
            'index': None,
            'libraries': [],
            'keywords': {},
        }
        populator = RobotKeywordsIndexerListener(self.robot_catalog)
        populator.library_import('BuiltIn', {})
        for name, keywords in CONTEXT_LIBRARIES.items():
            populator._library_import(keywords, name)

    def do_shutdown(self, restart):
        self.robot_history = OrderedDict()
        for driver in self.robot_webdrivers:
            driver['instance'].quit()
        self.robot_webdrivers = []

    def do_complete(self, code, cursor_pos):
        cursor_pos = cursor_pos is None and len(code) or cursor_pos
        line, offset = line_at_cursor(code, cursor_pos)
        line_cursor = cursor_pos - offset
        needle = re.split(r'\s{2,}|\t| \| ', line[:line_cursor])[-1].lstrip()

        def normalize(s):
            return (re.sub(r'([:*])', r'\\\1', s, re.U) + '*').rstrip().lower()

        matches = []
        results = []
        context = detect_robot_context(code, cursor_pos)
        if needle.rstrip():
            results = self.robot_catalog['index'].search(normalize(needle))
        for result in scored_results(needle, results):
            ref = result['ref']
            if ref.startswith('__') and not ref.startswith(context):
                continue
            elif not ref.startswith(context) and context not in [
                    '__tasks__',
                    '__keywords__',
                    '__settings__',
            ]:
                continue
            elif not needle.count('.'):
                keyword = self.robot_catalog['keywords'][ref].name
                if keyword not in matches:
                    matches.append(readable_keyword(keyword))
            else:
                matches.append(readable_keyword(ref))

        return {
            'matches': matches,
            'cursor_end': cursor_pos,
            'cursor_start': cursor_pos - len(needle),
            'metadata': {},
            'status': 'ok',
        }

    def do_inspect(self, code, cursor_pos, detail_level=0):
        cursor_pos = cursor_pos is None and len(code) or cursor_pos
        line, offset = line_at_cursor(code, cursor_pos)
        line_cursor = cursor_pos - offset
        needle = re.split(r'\s{2,}|\t| \| ', line[:line_cursor])[-1].lstrip()
        needle = needle.strip().lower()

        def normalize(s):
            return re.sub(r'([:*])', r'\\\1', s, re.U)

        reply_content = {
            'status': 'ok',
            'data': self.robot_inspect_data,
            'metadata': {},
            'found': bool(self.robot_inspect_data),
        }

        results = []
        if needle:
            results = self.robot_catalog['index'].search(normalize(needle))
        for result in results:
            keyword = self.robot_catalog['keywords'][result['ref']]
            if needle not in [keyword.name.lower(), result['ref'].lower()]:
                continue
            self.robot_inspect_data.update(get_keyword_doc(keyword))
            reply_content['found'] = True
            break

        return reply_content

    def init_metadata(self, parent):
        # Jupyter Lab sends deleted cells and the currently updated cell
        # id as message metadata, that allows to keep robot history in
        # sync with the displayed notebook:
        deleted_cells = \
            (parent.get('metadata') or {}).get('deletedCells') or []
        for cell_id in deleted_cells:
            if cell_id in self.robot_history:
                del self.robot_history[cell_id]
        self.robot_cell_id = \
            (parent.get('metadata') or {}).get('cellId') or None
        return super(RobotKernel, self).init_metadata(parent)

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
            for historical in self.robot_history.values():
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

        # Update catalog
        keywords_indexer = RobotKeywordsIndexerListener(self.robot_catalog)
        keywords_indexer._import_from_suite_data(data)

        # Build
        builder = TestSuiteBuilder()
        with TemporaryDirectory() as path:
            data.source = path
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
            self.robot_history[self.robot_cell_id or str(uuid.uuid4())] = code

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
            self.send_display_data(
                {
                    'text/html': '<pre>.</pre>',
                },
                display_id=display_id,
            )
            listener.append(
                StatusEventListener(
                    lambda s: self.send_update_display_data(
                        {
                            'text/html': '<pre>' +
                            (''.join(update_progress(progress, s))) + '</pre>',
                        },
                        display_id=display_id,
                    ),
                ),
            )
            listener.append(
                ReturnValueListener(lambda v: return_values.append(v)),
            )
        listener.append(WebdriverConnectionsListener(self.robot_webdrivers))
        listener.append(RobotKeywordsIndexerListener(self.robot_catalog))

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
            rpa=suite.rpa,
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
                    '<p><a href="{}">Log</a> | <a href="{}">Report</a></p>'.
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


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=RobotKernel)
