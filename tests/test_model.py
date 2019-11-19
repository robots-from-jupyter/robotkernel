# -*- coding: utf-8 -*-
from robotkernel.model import TestCaseString


def test_string():
    case = TestCaseString()
    case.populate('''
*** Settings ***

Library  Collections

*** Settings ***

Library  Collections

*** Keywords ***

Head
    [Arguments]  ${list}
    ${value}=  Get from list  ${list}  0
    [Return]  ${value}

*** Tasks ***

Get head
    ${array}=  Create list  1  2  3  4  5
    ${head}=  Head  ${array}
    Should be equal  ${
''')
    assert len(case.keywords) == 1
    assert len(case.testcase_table.tests) == 1
