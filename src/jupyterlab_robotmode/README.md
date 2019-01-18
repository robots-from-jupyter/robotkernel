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

### 2.0.0 (xxxx-xx-xx)

- Rebase the implementation on top of jupyterlab-robotframework from
  https://github.com/gtri/irobotframework

### 1.1.1 (2018-01-11)

- Fix ssue where only the first variable in cell was highlighted

### 1.1.0 (2018-01-04)

- Add to highlight variables
- Add to highlight ELSE
- Add to highlight keywords after variable assignments
- Add to highlight = operator
