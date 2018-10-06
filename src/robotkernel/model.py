# -*- coding: utf-8 -*-
from io import BytesIO
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
from robot.utils import get_error_message

import os


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
