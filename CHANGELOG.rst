Changelog
=========

1.5.0 (2021-04-22)
------------------

- Add support for robotframework 4.0
  [datakurre]

1.4.0 (2020-04-27)
------------------

- Add support for robotframework 3.2
  [datakurre]
- Change kernel mimetype to "text/x-robotframework"
  [datakurre]

1.3.0 (2020-01-09)
------------------

- Add jupyterlab-starters' based quick start and tutorial
  [datakurre]
- Fix issue where Selenium test or task execution resulted in breaking
  exception, because temporary execution directory could not be cleared due to
  open geckodriver.log
  [datakurre]

1.2.2 (2020-01-05)
------------------

- Fix regression where wrong nbimporter was not automatically imported
  [datakurre]

1.2.1 (2019-12-30)
------------------

- Fix issue where data uri images were not displayed on notebook
  [datakurre]
- Fix issue where list type suite variables were not correctly restored
  [datakurre]

1.2 (2019-12-06)
----------------

- Add support for Robot Framework 3.2a1
  [datakurre]
- Add support for displaying multiline text return values
  [datakurre]
- Add support for sticky JupyterLibrary webdriver connections
  [datakurre]
- Fix issue where updated global variables were overridden from saved
  variables from the previous execution
  [datakurre]

1.1.1 (2019-12-05)
------------------

- Fix issue where library autocompletion override settings keywords
  autocompletion
  [datakurre]

1.1.0 (2019-12-05)
------------------

- Add Library autocompletion after Library keyword within Settings
  [datakurre]

1.0.2 (2019-12-04)
------------------

- Fix issue where text strings feed to JSON displayed a warning
  [datakurre]
- Fix JupyterLab context help support to work when clicked in the middlle of a keyword
  [datakurre]
- Fix to close dangling Selenium connections
  [datakurre]

1.0.1 (2019-09-19)
------------------

- Fix issue where ${CURDIR} was broken on Windows, because it contained path without
  escaped path separators required by Robot Framework
  [datakurre]
- Fix issue where suite variable listener reported errors when running robot suites,
  because it tried to restore dictionary variables with empty value
  [datakurre]

1.0 (2019-09-12)
----------------

- Fix issue where log and report links did not open on JupyterLab 1.0
  [datakurre]

1.0rc1 (2019-04-01)
-------------------

- Move tutorials notebooks into notebooks folder
  [datakurre]
- Fix WhiteLibrary autocompletion to suggest selectors with :-separator
  instead of =-separator
  [datakurre]

0.12.2 (2019-03-30)
-------------------

- Fix remaining where keeping state of suite level variables between cell
  executions since 0.12.0 caused regression by fixing the listener to ignore
  all known built-in variables
  [datakurre]

0.12.1 (2019-03-27)
-------------------

- Fix issue where keeping state of suite level variables between cell
  executions resulted in errors caused by outdated output directory
  from the old variables
  [datakurre]

0.12.0 (2019-03-26)
-------------------

New features:

- Add keyword execution widgets below executed keyword cells; Add to toggle
  widgets on consecutive executions without code changes
  [datakurre]

- Add listener to keep state of suite level variables between robot executions
  [datakurre]

- Add IPython display hooks
  [datakurre]

New features:

- Add updates to highlighting from ipythonrobotframework
  [datakurre]

0.11.0 (2019-01-29)
-------------------

- Add WhiteLibrary state support and interactive element picker
  [datakurre]

- Add WhiteLibraryCompanion keyword library to interactively
  select elements and click elements with OpenCV templates
  [datakurre]

0.10.2 (2019-01-11)
-------------------

- Fix syntax highlighting issue where only the first variable of many was
  highlighted
  [datakurre]

0.10.1 (2019-01-10)
-------------------

- Update package trove classifiers
  [datakurre]

0.10.0 (2019-01-08)
-------------------

Breaking:

- Setuptools 40.5.0 later and Robot Framework 3.1 or later.
  [datakurre]

new features:

- Add pregenerated kernel.json in data_files to auto-install robotkernel,
  but requiring
  [datakurre]

0.9.0 (2019-01-04)
------------------

New features:

- Rewrite status updater to the status of currently run test as
  ``trobber | test name | keyword name | robot.api.logger.console message``
  [datakurre]

- Add embedded log and report to include Download-links at top right corner
  [datakurre]

- Add to display the results of the last executed keyword as the notebook
  result for the executed code cell
  [datakurre]

- Add syntax highlighting for variables and assignment operators
  [datakurre]

Bug fixes:

- Fix issue where setup.cfg contained OS specific path separators preventing
  build on Windows
  [datakurre]

- Fix issue where PNGs were interpreted as APNG on Windows preventing
  them from being rendered on Windows
  [datakurre]

- Update example notebook to use SeleniumLibrary and SeleniumScreenshots
  instead of SeleniumLibrary and Selenium2Screenshots
  [datakurre]

- Add to always reload libraries imported from other notebooks
  [datakurre]

0.8.0 (2018-12-14)
------------------

- Add to auto-import nbimporter when available to make it possible to
  import eg. keyword libraries from Python notebooks
  [datakurre]
- Fix issue where nbrobot did support %%python module magic
  [datakurre]

0.7.1 (2018-11-20)
------------------

- Add to require robotframework >= 3.1b1 in requires

0.7.0 (2018-10-31)
------------------

Breaking:

- Requires robotframework >= 3.1b1

Other:

- Add to create nbreader and nblibdoc cli to run robot with notebook reader
  support
  [datakurre]
- Add Selenium completions to sometimes include raw Simmer results with
  simplfied id completion results
  [datakurre]
- Add proof-of-concept selector completion for Appium and AutoIT libraries
  [datakurre]
- Fix screenshot processor to also discover images with absolute path or within
  the current working directory
  [datakurre]

0.6.3 (2018-10-19)
------------------

This is the last release compatible with robotframework < 3.1

- Remove deprecated replace-flag from kernel installer
  [datakurre]

0.6.2 (2018-10-19)
------------------

- Fix compatibility issue with robotframework < 3.1
  [datakurre]

0.6.1 (2018-10-19)
------------------

- Fix issue where kernel installation produced broken kernel.json on Windows
  [datakurre]

0.6.0 (2018-10-18)
------------------

- Revert data source path from temporary directory into current working
  directory to allow local libraries and resources work in the usual use cases
  [datakurre]
- Add experimental Simmerjs based CSS-selector builder and element picker with
  when auto-completion is called with empty "css:"-selector
  [datakurre]
- Add experimental Selenium selector auto-completion
  [datakurre]
- Add dummy variable completion with only variables from current suite without
  context knowledge
  [datakurre]
- Add inline documentation links to Robot Framework User Guide for structural
  keywords
  [datakurre]

0.5.4 (2018-10-09)
------------------

- Fix issue where single term keywords got no completions
  [datakurre]

0.5.3 (2018-10-09)
------------------

- Update README
  [datakurre]

0.5.1 (2018-10-08)
------------------

- Auto completion and keyword doc inspection enhancements
  [datakurre]

0.5.0 (2018-10-08)
------------------

- Add auto-completion, keyword doc inspection and support for
  replacing and deleting cell history on Jupyter lab
  [datakurre]

0.4.0 (2018-09-26)
------------------

- Add support for robotframework 3.1a2
  [datakurre]

- Add support for reporting RPA suites with "Tasks" instead of "Tests"
  [datakurre]

0.3.5 (2018-09-25)
------------------

- Update README with notebook execution instructions
  [datakurre]

0.3.4 (2018-09-25)
------------------

- Update README
  [datakurre]

0.3.3 (2018-09-25)
------------------

- Note on README that Log | Report -links require trusting the notebook
  [datakurre]

- Fix to wrap test execution updates with '<pre>' for better readability
  [datakurre]

0.3.2 (2018-09-25)
------------------

- Change to always send display data updates in text/html to workaround a bug
  that caused 'undefined' to be rendered in JupyterLab
  [datakurre]

0.3.1 (2018-09-24)
------------------

- Update README
  [datakurre]

0.3.0 (2018-09-23)
------------------

- First release.
  [datakurre]
