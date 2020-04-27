# -*- coding: utf-8 -*-
from io import StringIO
from robot.api import get_model
from robot.errors import DataError
from robot.running.builder.parsers import ErrorReporter
from robot.running.builder.testsettings import TestDefaults
from robot.running.builder.transformers import SettingsBuilder
from robot.running.builder.transformers import SuiteBuilder
from robot.running.model import TestSuite
from typing import Dict
import os


def _get_rpa_mode(data):
    if not data:
        return None
    tasks = [s.tasks for s in data.sections if hasattr(s, "tasks")]
    if all(tasks) or not any(tasks):
        return tasks[0] if tasks else None
    raise DataError("One file cannot have both tests and tasks.")


# TODO: Refactor to use public API only
# https://github.com/robotframework/robotframework/commit/fa024345cb58d154e1d8384552b62788d3ed6258


def build_suite(code: str, cell_history: Dict[str, str], data_only: bool = False):
    # Init
    suite = TestSuite(name="Jupyter", source=os.getcwd())
    defaults = TestDefaults(None)

    # Populate history
    for historical in cell_history.values():
        ast = get_model(
            StringIO(historical),
            data_only=data_only,
            curdir=os.getcwd().replace("\\", "\\\\"),
        )
        ErrorReporter(historical).visit(ast)
        SettingsBuilder(suite, defaults).visit(ast)
        SuiteBuilder(suite, defaults).visit(ast)

    # Clear historical tests
    suite.tests._items = []

    # Populate current
    ast = get_model(
        StringIO(code), data_only=data_only, curdir=os.getcwd().replace("\\", "\\\\")
    )
    ErrorReporter(code).visit(ast)
    SettingsBuilder(suite, defaults).visit(ast)
    SuiteBuilder(suite, defaults).visit(ast)

    # Strip duplicate keywords
    keywords = {}
    for keyword in suite.resource.keywords:
        keywords[keyword.name] = keyword
    suite.resource.keywords._items = list(keywords.values())

    # Strip duplicate variables
    variables = {}
    for variable in suite.resource.variables:
        variables[variable.name] = variable
    suite.resource.variables._items = list(variables.values())

    # Detect RPA
    suite.rpa = _get_rpa_mode(ast)

    return suite
