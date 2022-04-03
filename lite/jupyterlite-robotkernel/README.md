# jupyterlite_robotkernel

[![Github Actions Status](https://github.com/deathbeds/robotkernel/workflows/Build/badge.svg)](https://github.com/deathbeds/robotkernel/actions/workflows/build.yml)

A RobotFramework kernel for JupyterLite

## Requirements

* JupyterLite >= 0.1.0b2

## Install

To install the extension, execute:

```bash
pip install jupyterlite_robotkernel
```

Then build your JupyterLite site:

```bash
jupyter lite build
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall jupyterlite_robotkernel
```

## Contributing

### Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Change directory to the jupyterlite_robotkernel directory
# Install package in development mode
python -m pip install -e .

# Link your development version of the extension with JupyterLab
jupyter labextension develop . --overwrite

# Rebuild extension Typescript source after making changes
jlpm run build
```

You can watch the source directory and run JupyterLab at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm run watch
# Run JupyterLab in another terminal
jupyter lab
```

With the watch command running, every saved change will immediately be built locally and available in your running JupyterLab. Refresh JupyterLab to load the change in your browser (you may need to wait several seconds for the extension to be rebuilt).


### Development uninstall

```bash
pip uninstall jupyterlite_robotkernel
```

In development mode, you will also need to remove the symlink created by `jupyter labextension develop`
command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions`
folder is located. Then you can remove the symlink named `robotkernel` within that folder.
