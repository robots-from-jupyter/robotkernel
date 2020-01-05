# -*- coding: utf-8 -*-
from robot.libdocpkg.model import KeywordDoc
import pkg_resources
import re


try:
    pkg_resources.get_distribution("robotframework>=3.2a1")
    HAS_RF32_PARSER = True
except pkg_resources.VersionConflict:
    HAS_RF32_PARSER = False

try:
    pkg_resources.get_distribution("nbimporter")
    HAS_NBIMPORTER = True
except pkg_resources.DistributionNotFound:
    HAS_NBIMPORTER = False


VARIABLE_REGEXP = re.compile(r"[$@&%]\{[\w\s]+\}")

CONTEXT_LIBRARIES = {
    "__root__": list(
        map(
            lambda item: KeywordDoc(name=item[0], doc=item[1]),
            {
                "*** Settings ***": """\
The Setting table is used to import test libraries, resource files and variable
files and to define metadata for test suites and test cases. It can be included
in test case files and resource files. Note that in a resource file, a Setting
table can only include settings for importing libraries, resources, and
variables.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#appendices
""",  # noqa: E501
                "*** Variables ***": """\
The most common source for variables are Variable tables in test case files and
resource files. Variable tables are convenient, because they allow creating
variables in the same place as the rest of the test data, and the needed syntax
is very simple. Their main disadvantages are that values are always strings and
they cannot be created dynamically. If either of these is a problem, variable
files can be used instead.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#creating-variables
""",  # noqa: E501
                "*** Test Cases ***": """\
Test cases are constructed in test case tables from the available keywords.
Keywords can be imported from test libraries or resource files, or created in
the keyword table of the test case file itself.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-syntax
""",  # noqa: E501
                "*** Tasks ***": """\
Tasks are constructed in tasks tables from the available keywords. Keywords can
be imported from test libraries or resource files, or created in the keyword
table of the tasks file itself.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-syntax
""",  # noqa: E501
                "*** Keywords ***": """\
User keyword names are in the first column similarly as test cases names. Also
user keywords are created from keywords, either from keywords in test libraries
or other user keywords. Keyword names are normally in the second column, but
when setting variables from keyword return values, they are in the subsequent
columns.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-syntax
""",  # noqa: E501
            }.items(),
        )
    ),
    "__settings__": list(
        map(
            lambda item: KeywordDoc(name=item[0], doc=item[1]),
            {
                "Library": """\
Test libraries are typically imported using the Library setting.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#importing-libraries
""",  # noqa: E501
                "Resource": """\
Resource files are imported using the Resource setting in the Settings table.
The path to the resource file is given in the cell after the setting name.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#taking-resource-files-into-use
""",  # noqa: E501
                "Variables": """\
All test data files can import variables using the Variables setting in the
Setting table, in the same way as resource files are imported using the
Resource setting.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#taking-variable-files-into-use
""",  # noqa: E501
                "Documentation": """\
Used for specifying a test suite or resource file documentation.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-suite-name-and-documentation
""",  # noqa: E501
                "Metadata": """\
Used for setting free test suite metadata.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#free-test-suite-metadata
""",  # noqa: E501
                "Suite Setup": """\
Used for specifying the suite setup.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#suite-setup-and-teardown
""",  # noqa: E501
                "Suite Teardown": """\
Used for specifying the suite teardown.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#suite-setup-and-teardown
""",  # noqa: E501
                "Test Setup": """\
Used for specifying a default test setup.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: E501
                "Test Teardown": """\
Used for specifying a default test teardown.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: E501
                "Test Template": """\
Used for specifying a default template keyword for test cases.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-templates
""",  # noqa: E501
                "Test Timeout": """\
Used for specifying a default test case timeout.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-timeout
""",  # noqa: E501
                "Task Setup": """\
Used for specifying a default task setup.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: E501
                "Task Teardown": """\
Used for specifying a default task teardown.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: E501
                "Task Template": """\
Used for specifying a default template keyword for tasks.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-templates
""",  # noqa: E501
                "Task Timeout": """\
Used for specifying a default task timeout.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-timeout
""",  # noqa: E501
                "Force Tags": """\
Used for specifying forced values for tags when tagging test cases.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tagging-test-cases
""",  # noqa: E501
                "Default Tags": """\
Used for specifying default values for tags when tagging test cases.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tagging-test-cases
""",  # noqa: E501
            }.items(),
        )
    ),
    "__tasks__": list(
        map(
            lambda item: KeywordDoc(name=item[0], doc=item[1]),
            {
                "[Documentation]": """\
Used for specifying test case documentation.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-name-and-documentation
""",  # noqa: E501
                "[Tags]": """\
Used for tagging test cases.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tagging-test-cases
""",  # noqa: E501
                "[Setup]": """\
Used for specifying a test setup.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: E501
                "[Teardown]": """\
Used for specifying a test teardown.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-setup-and-teardown
""",  # noqa: E501
                "[Template]": """\
Used for specifying a template keyword.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-templates
""",  # noqa: E501
                "[Timeout]": """\
Used for specifying a test case timeout.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-case-timeout
""",  # noqa: E501
            }.items(),
        )
    ),
    "__keywords__": list(
        map(
            lambda item: KeywordDoc(name=item[0], doc=item[1]),
            {
                "[Documentation]": """\
Used for specifying a user keyword documentation.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-documentation
""",  # noqa: E501
                "[Tags]": """\
Used for specifying user keyword tags.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-tags
""",  # noqa: E501
                "[Arguments]": """\
Used for specifying user keyword arguments.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-arguments
""",  # noqa: E501
                "[Return]": """\
Used for specifying user keyword return values.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-return-values
""",  # noqa: E501
                "[Teardown]": """\
Used for specifying user keyword teardown.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-teardown
""",  # noqa: E501
                "[Timeout]": """\
Used for specifying a user keyword timeout.

`Robot Framework User Guide`__

__ http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#user-keyword-timeout
""",  # noqa: E501
            }.items(),
        )
    ),
}
CONTEXT_LIBRARIES["__settings__"].extend(CONTEXT_LIBRARIES["__root__"])

THROBBER = "data:image/gif;base64,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"  # noqa: E501
