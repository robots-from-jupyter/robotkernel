# jupyterlab_robotmode

A JupyterLab extensions, which adds CodeMirror mode for Robot Framework syntax


## Prerequisites

* JupyterLab

## Installation

To install using pip:

```bash
jupyter labextension install jupyterlab_robotmode
```

## Development

For a development install (requires npm version 4 or later), do the following in the repository directory:

```bash
npm install
jupyter labextension link .
```

## Changelog

### 3.0.2 (2020-04-17)

- Loosen dependencies for Jupyterlab to better support Binder

### 3.0.0 (2020-04-17)

- Package for Jupyterlab 2.x

### 2.4.0 (2019-09-12)

- Fix compatibility with JupyterLab 1.0

### 2.3.1 (2019-03-06)

- Fix highlighting mode label to match robotkernel's

### 2.3.0 (2019-03-05)

- Update fixes from
  https://github.com/gtri/irobotframework/pull/1

### 2.2.0 (2019-01-29)

- Add to highlight : as operator in keyword arguments to better
  highligh SeleniumLibrary locators

### 2.1.1 (2019-01-29)

- Fix packaging issue in 2.1.0

### 2.1.0 (2019-01-29)

- Add support for highlighting loops and other fixes from
  https://github.com/gtri/irobotframework/pull/1

### 2.0.3 (2019-01-20)

- Loosen jupyterlab version requirements

### 2.0.0 (2019-01-20)

- Rebase the implementation on top of jupyterlab-robotframework from
  https://github.com/gtri/irobotframework

### 1.1.1 (2019-01-11)

- Fix ssue where only the first variable in cell was highlighted

### 1.1.0 (2018-01-04)

- Add to highlight variables
- Add to highlight ELSE
- Add to highlight keywords after variable assignments
- Add to highlight = operator
