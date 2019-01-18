Robotkernel
===========

`Robot Framework`_ IPython_ kernel for `Jupyter Notebook`_ and JupyterLab_.

Requires Python 3.6 or later and Robot Framework 3.1b1 or later.

Log | Report -links on existing notebooks are only active on trusted notebooks.

.. _Robot Framework: http://robotframework.org/
.. _IPython: https://ipython.org/
.. _Jupyter Notebook: https://jupyter.readthedocs.io/en/latest/
.. _JupyterLab: https://jupyterlab.readthedocs.io/en/stable/


Try Robotkernel at Binder
-------------------------

Jupyter Notebook: https://mybinder.org/v2/gh/robots-from-jupyter/robotkernel/master?urlpath=tree/example.ipynb

JupyterLab: https://mybinder.org/v2/gh/robots-from-jupyter/robotkernel/master?urlpath=lab/tree/example.ipynb


Install Robotkernel
-------------------

.. code:: bash

   $ pip install robotkernel

For JupyterLab you should also install the companion syntax highlighting:

.. code:: bash

   $ jupyter labextension install jupyterlab_robotmode

For some environments it might be required to run the following command to
manually register robotkernel as Jupyter kernel:

.. code:: bash

   $ python -m robotkernel.install


Install Robotkernel from Python 3 notebook
------------------------------------------

.. code:: bash

   !pip install robotkernel

After refreshing the notebook, it is possible change the kernel to Robot Framework kernel or create a new notebook with Robot Framework kernel.

For JupyterLab you should also install the companion syntax highlighting:

.. code:: bash

   !jupyter labextension install jupyterlab_robotmode


Export robot files
------------------

It is possible to export test suites direclty from Jupyter Notebook or JupyterLab user interface (into traditional ``.robot`` files), but also from command line:

.. code:: bash

   $ jupyter nbconvert --to script example.ipynb


Execute notebooks
-----------------

Robotkernel installs script named ``nbrobot``, which the Robot Frameworks test runner ``robot`` with support for executing Jupyter notebooks created with Robotkernel:

.. code:: bash

   $ nbrobot example.ipynb

In addition, it is also possible to execute notebooks as such, resulting into a new notebook with embedded execution logs and reports:

.. code:: bash

   $ jupyter nbconvert --to notebook --execute example.ipynb

This will stop the execution at first failing test case.

When execution with errors, to also get a result notebook with execution logs saved, an extra flag ``--ExecutePreprocessor.allow_errors=True`` must be set:

.. code:: bash

   $ jupyter nbconvert --ExecutePreprocessor.allow_errors=True --to notebook --execute example.ipynb

This `may change`__ in future versions of nbconvert.

__ https://github.com/jupyter/nbconvert/issues/626

Note that when executing a notebook, each cell with tests cases or tasks will be executed as its own suite. It might be more efficient to export notebook into a robot script and execute that with the traditional robot runner.


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

Add ``--arg sikuli true`` to include SikuliLibrary_.

Add ``--arg vim true`` to enable `vim bindings`_.

.. _SikuliLibrary: https://github.com/rainmanwy/robotframework-SikuliLibrary
.. _vim bindings: https://github.com/lambdalisue/jupyter-vim-binding

Development environment with Nix:

.. code:: bash

    $ git clone https://github.com/robots-from-jupyter/robotkernel.git
    $ cd robotkernel
    $ nix-build setup.nix -A env  # to generate ./result/bin/python for IDE
    $ nix-shell setup.nix -A develop

.. toctree::
   :maxdepth: 2

   smoketest.ipynb
   tutorial/00 JupyterLab User Interface.ipynb
   tutorial/01 Running Code.ipynb
   tutorial/02 Python XKCD.ipynb
   tutorial/03 Running Robot.ipynb
   tutorial/04 Robot XKCD.ipynb
