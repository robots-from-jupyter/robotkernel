# -*- coding: utf-8 -*-
from robotkernel.builders import build_suite


TEST_SUITE = """\
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
    Should be equal  ${head}  1
"""


def test_string():
    suite = build_suite(TEST_SUITE, {})
    assert len(suite.resource.keywords) == 1
    assert len(suite.tests) == 1
