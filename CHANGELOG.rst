Changelog
=========

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

New features:

- Add pregenerated kernel.json in data_files to auto-install robotkernel,
  but requiring
  [datakurre]

0.9.0 (2019-01-04)
------------------

New featurs:

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
