# -*- coding: utf-8 -*-
from robot.parsing import LexerWrapper
from robot.parsing import RobotFrameworkParser
from robot.parsing import TestCaseFileLexer
from robot.parsing.vendor import yacc
from robot.running.builder.builders import _get_rpa_mode
from robot.running.builder.testsettings import TestDefaults
from robot.running.builder.transformers import SettingsBuilder
from robot.running.builder.transformers import SuiteBuilder
from robot.running.model import TestSuite
from typing import Dict
import os
import robot.parsing.parser


def build_suite(code: str, cell_history: Dict[str, str]):
    # Init
    suite = TestSuite(name="Jupyter", source=os.getcwd())
    defaults = TestDefaults(None)

    # Populate history
    for historical in cell_history.values():
        ast = StringRobotFrameworkParser(TestCaseFileLexer()).parse(historical)
        SettingsBuilder(suite, defaults).visit(ast)
        SuiteBuilder(suite, defaults).visit(ast)

    # Clear historical tests
    suite.tests._items = ()

    # Populate current
    ast = StringRobotFrameworkParser(TestCaseFileLexer()).parse(code)
    SettingsBuilder(suite, defaults).visit(ast)
    SuiteBuilder(suite, defaults).visit(ast)

    # Strip duplicate keywords
    keywords = {}
    for keyword in suite.resource.keywords:
        keywords[keyword.name] = keyword
    suite.resource.keywords._items = tuple(list(keywords.values()))

    # Strip duplicate variables
    variables = {}
    for variable in suite.resource.variables:
        variables[variable.name] = variable
    suite.resource.variables._items = tuple(list(variables.values()))

    # Detect RPA
    suite.rpa = _get_rpa_mode(ast)

    return suite


class StringLexerWrapper(LexerWrapper):

    # noinspection PyMissingConstructor
    def __init__(self, lexer, source):
        self.source = source
        self.curdir = os.getcwd().replace("\\", "\\\\")
        lexer.input(source)
        self.tokens = lexer.get_tokens()


class StringRobotFrameworkParser(RobotFrameworkParser):
    def parse(self, source):
        parser = yacc.yacc(module=robot.parsing.parser.RobotFrameworkParser(None))
        return parser.parse(lexer=StringLexerWrapper(self.lexer, source))
