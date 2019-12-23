Install RobotKernel
===================

Installing RobotKernel requires Python 3.6 or later with setuptools 40.5.0 later and Robot Framework Robot Framework 3.1 or later.


Virtualenv installation
-----------------------

RobotKernel can be installed using the usual Python package manager tools, like pip:

.. code:: bash

   $ pip install robotkernel

For JupyterLab it is recommended to also install the Robot Framework syntax highlighting and Jupyter widgets support:

.. code:: bash

   $ jupyter labextension install jupyterlab_robotmode
   $ jupyter labextension install @jupyter-widgets/jupyterlab-manager

For some environments it might be required to run the following command to manually register robotkernel as an available Jupyter kernel:

.. code:: bash

   $ python -m robotkernel.install


Install Robotkernel from Python 3 notebook
------------------------------------------

.. code:: bash

   !pip install robotkernel

After refreshing the notebook, it is possible change the kernel to Robot Framework kernel or create a new notebook with Robot Framework kernel.

For JupyterLab it is recommended to also install the Robot Framework syntax highlighting and Jupyter widgets support:

.. code:: bash

   !jupyter labextension install jupyterlab_robotmode
   !jupyter labextension install @jupyter-widgets/jupyterlab-manager


Local installation and development
----------------------------------

See also: http://jupyter.readthedocs.io/en/latest/install.html

Create and activate clean Python virtual environment::

    $ venv myenv
    $ source myenv/bin/activate

Install Jupyter::

    $ pip install --upgrade pip setuptools
    $ pip install jupyter

Clone this kernel::

    $ git clone https://github.com/robots-from-jupyter/robotkernel.git
    $ cd robotkernel

Install the kernel into virtualenv in develop mode::

    $ python setup.py develop

Launch the jupyter::

    $ jupyter notebook

Reloading the kernel reloads the code.


Nix-shell (https://nixos.org/nix/)
----------------------------------

This repository includes opinionated instructions for running and developing Robotkernel with Nix for Jupyter Notebook:

.. code:: bash

   $ nix-shell -E 'import (fetchTarball https://github.com/robots-from-jupyter/robotkernel/archive/master.tar.gz + "/shell.nix")' --run "jupyter notebook"

And for Jupyter Lab:

.. code:: bash

   $ nix-shell -E 'import (fetchTarball https://github.com/robots-from-jupyter/robotkernel/archive/master.tar.gz + "/shell.nix")'
   $ jupyter labextension install jupyterlab_robotmode --app-dir=.jupyterlab
   $ jupyter lab --app-dir=.jupyterlab
   $ exit

Add ``--arg vim true`` to enable `vim bindings`_ for Jupyter Notebook.

.. _vim bindings: https://github.com/lambdalisue/jupyter-vim-binding

Development environment with Nix:

.. code:: bash

    $ git clone https://github.com/robots-from-jupyter/robotkernel.git
    $ cd robotkernel
    $ nix-build setup.nix -A env  # to generate ./result/bin/python for IDE
    $ nix-shell setup.nix -A develop
