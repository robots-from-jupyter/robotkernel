# -*- coding: utf-8 -*-
from robot.libdocpkg.model import KeywordDoc

import re


VARIABLE_REGEXP = re.compile(r'[$@&%]\{[\w\s]+\}')

CONTEXT_LIBRARIES = {
    '__root__': list(
        map(
            lambda item: KeywordDoc(name=item[0], doc=item[1]),
            {
                '*** Settings ***': """\
The Setting table is used to import test libraries, resource files and variable
files and to define metadata for test suites and test cases. It can be included
in test case files and resource files. Note that in a resource file, a Setting
table can only include settings for importing libraries, resources, and
variables.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#appendices
""",  # noqa: FE501
                '*** Variables ***': """\
The most common source for variables are Variable tables in test case files and
resource files. Variable tables are convenient, because they allow creating
variables in the same place as the rest of the test data, and the needed syntax
is very simple. Their main disadvantages are that values are always strings and
they cannot be created dynamically. If either of these is a problem, variable
files can be used instead.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#creating-variables
""",  # noqa: FE501
                '*** Test Cases ***': """\
Test cases are constructed in test case tables from the available keywords.
Keywords can be imported from test libraries or resource files, or created in
the keyword table of the test case file itself.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-syntax
""",  # noqa: FE501
                '*** Tasks ***': """\
Tasks are constructed in tasks tables from the available keywords. Keywords can
be imported from test libraries or resource files, or created in the keyword
table of the tasks file itself.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-syntax
""",  # noqa: FE501
                '*** Keywords ***': """\
User keyword names are in the first column similarly as test cases names. Also
user keywords are created from keywords, either from keywords in test libraries
or other user keywords. Keyword names are normally in the second column, but
when setting variables from keyword return values, they are in the subsequent
columns.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-syntax
""",  # noqa: FE501
            }.items(),
        ),
    ),
    '__settings__': list(
        map(
            lambda item: KeywordDoc(name=item[0], doc=item[1]),
            {
                'Library': """\
Test libraries are typically imported using the Library setting.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#importing-libraries 
""",  # noqa: FE501
                'Resource': """\
Resource files are imported using the Resource setting in the Settings table.
The path to the resource file is given in the cell after the setting name.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#taking-resource-files-into-use
""",  # noqa: FE501
                'Variables': """\
All test data files can import variables using the Variables setting in the
Setting table, in the same way as resource files are imported using the
Resource setting.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#taking-variable-files-into-use
""",  # noqa: FE501
                'Documentation': """\
Used for specifying a test suite or resource file documentation.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-suite-name-and-documentation
""",  # noqa: FE501
                'Metadata': """\
Used for setting free test suite metadata.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#free-test-suite-metadata
""",  # noqa: FE501
                'Suite Setup': """\
Used for specifying the suite setup.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#suite-setup-and-teardown
""",  # noqa: FE501
                'Suite Teardown': """\
Used for specifying the suite teardown.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#suite-setup-and-teardown
""",  # noqa: FE501
                'Test Setup': """\
Used for specifying a default test setup.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: FE501
                'Test Teardown': """\
Used for specifying a default test teardown.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: FE501
                'Test Template': """\
Used for specifying a default template keyword for test cases.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-templates
""",  # noqa: FE501
                'Test Timeout': """\
Used for specifying a default test case timeout.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-timeout
""",  # noqa: FE501
                'Task Setup': """\
Used for specifying a default task setup.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: FE501
                'Task Teardown': """\
Used for specifying a default task teardown.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: FE501
                'Task Template': """\
Used for specifying a default template keyword for tasks.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-templates
""",  # noqa: FE501
                'Task Timeout': """\
Used for specifying a default task timeout.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-timeout
""",  # noqa: FE501
                'Force Tags': """\
Used for specifying forced values for tags when tagging test cases.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tagging-test-cases
""",  # noqa: FE501
                'Default Tags': """\
Used for specifying default values for tags when tagging test cases.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tagging-test-cases
""",  # noqa: FE501
            }.items(),
        ),
    ),
    '__tasks__': list(
        map(
            lambda item: KeywordDoc(name=item[0], doc=item[1]),
            {
                '[Documentation]': """\
Used for specifying test case documentation.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-name-and-documentation
""",  # noqa: FE501
                '[Tags]': """\
Used for tagging test cases.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tagging-test-cases
""",  # noqa: FE501
                '[Setup]': """\
Used for specifying a test setup.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: FE501
                '[Teardown]': """\
Used for specifying a test teardown.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: FE501
                '[Template]': """\
Used for specifying a template keyword.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-templates
""",  # noqa: FE501
                '[Timeout]': """\
Used for specifying a test case timeout.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-timeout
""",  # noqa: FE501
            }.items(),
        ),
    ),
    '__keywords__': list(
        map(
            lambda item: KeywordDoc(name=item[0], doc=item[1]),
            {
                '[Documentation]': """\
Used for specifying a user keyword documentation.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-documentation
""",  # noqa: FE501
                '[Tags]': """\
Used for specifying user keyword tags.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-tags
""",  # noqa: FE501
                '[Arguments]': """\
Used for specifying user keyword arguments.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-arguments
""",  # noqa: FE501
                '[Return]': """\
Used for specifying user keyword return values.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-return-values
""",  # noqa: FE501
                '[Teardown]': """\
Used for specifying user keyword teardown.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-teardown
""",  # noqa: FE501
                '[Timeout]': """\
Used for specifying a user keyword timeout.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-timeout
""",  # noqa: FE501
            }.items(),
        ),
    ),
}
CONTEXT_LIBRARIES['__settings__'].extend(CONTEXT_LIBRARIES['__root__'])
