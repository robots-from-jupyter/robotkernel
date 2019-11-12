# -*- coding: utf-8 -*-
from io import BytesIO
from robot.errors import DataError
from robot.output import LOGGER
from robot.parsing import TestCaseFile
from robot.parsing.model import _TestData
from robot.parsing.model import KeywordTable
from robot.parsing.model import TestCaseFileSettingTable
from robot.parsing.populators import FromFilePopulator
from robot.parsing.robotreader import RobotReader
from robot.parsing.settings import Fixture
from robot.parsing.tablepopulators import NullPopulator
from robot.running import TestSuiteBuilder
from robot.utils import get_error_message
from typing import Dict
import os
import platform


def build_suite(code: str, cell_history: Dict[str, str]):
    # Init
    data = TestCaseString()
    data.source = os.getcwd()  # allow Library and Resource from CWD work

    # Populate history, but ignore tests
    for historical in cell_history.values():
        data.populate(historical)
        data.testcase_table.tests.clear()

    # Populate current
    data.populate(code)

    # Wrap up
    builder = TestSuiteBuilder()
    suite = builder._build_suite(data)
    suite._name = "Jupyter"

    return suite


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
        self.suite_setup = OverridingFixture("Suite Setup", self)
        self.suite_teardown = OverridingFixture("Suite Teardown", self)
        self.test_setup = OverridingFixture("Test Setup", self)
        self.test_teardown = OverridingFixture("Test Teardown", self)


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
        # Jupyter running directory for convenience
        if platform.system() == "Windows" and os.path.sep == "\\":
            # Because Robot Framework uses the backslash (\) as an escape character in
            # the test data, using a literal backslash requires duplicating it.
            self._curdir = os.getcwd().replace(os.path.sep, os.path.sep * 2)
        else:
            self._curdir = os.getcwd()

    def populate(self, source):
        LOGGER.info("Parsing string '%s'." % source)
        try:
            RobotReader().read(BytesIO(source.encode("utf-8")), self)
        except Exception:
            raise DataError(get_error_message())
