# -*- coding: utf-8 -*-
from robotkernel.utils import detect_robot_context


def test_detect_robot_context_root():
    assert detect_robot_context("", -1) == "__root__"
    assert (
        detect_robot_context(
            """\
*** Variables ***
""",
            -1,
        )
        == "__root__"
    )
    assert (
        detect_robot_context(
            """\
*** Settings ***
*** Variables ***
""",
            -1,
        )
        == "__root__"
    )


def test_detect_robot_context_settings():
    assert (
        detect_robot_context(
            """\
    *** Settings ***
    """,
            -1,
        )
        == "__settings__"
    )
    assert (
        detect_robot_context(
            """\
*** Settings ***
*** Tasks ***
""",
            len("*** Settings ***"),
        )
        == "__settings__"
    )


def test_detect_robot_context_tasks():
    assert (
        detect_robot_context(
            """\
*** Test Cases ***

This is a test case
    With a keyword  and  param
""",
            -1,
        )
        == "__tasks__"
    )
    assert (
        detect_robot_context(
            """\
*** Settings ***
*** Test Cases ***

This is a test case
    With a keyword  and  param
""",
            -1,
        )
        == "__tasks__"
    )
    assert (
        detect_robot_context(
            """\
*** Settings ***
*** Tasks ***

This is a task
    With a keyword  and  param
""",
            -1,
        )
        == "__tasks__"
    )


#
# def test_detect_robot_context_keywords():
#     assert detect_robot_context(
#         """\
# *** Keywords ***
# """, -1
#     ) == '__keywords__'
