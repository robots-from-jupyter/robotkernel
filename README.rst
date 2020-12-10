Robotkernel
===========

|Smoketest Badge|

RobotKernel is a `Robot Framework`_ IPython_ kernel for `Jupyter Notebook`_ and JupyterLab_. It powers RobotLab_ – the Robot Framework JupyterLab distribution. Check a `video to see it in action`_ and `read the documentation`_.

RobotKernel requires Python 3.6 or later with setuptools 40.5.0 later and Robot Framework Robot Framework 3.1 or later.

.. |Smoketest Badge| image:: https://github.com/robots-from-jupyter/robotkernel/workflows/smoketest/badge.svg
.. _video to see it in action: https://youtu.be/uYGh9_c3b7s
.. _read the documentation: https://robots-from-jupyter.github.io/robotkernel/
.. _Robot Framework: http://robotframework.org/
.. _IPython: https://ipython.org/
.. _Jupyter Notebook: https://jupyter.readthedocs.io/en/latest/
.. _JupyterLab: https://jupyterlab.readthedocs.io/en/stable/
.. _RobotLab: https://github.com/robots-from-jupyter/robotlab/releases

For alternative Robot Framework IPython kernel, check out `ipythonrobotframework`_.

.. _ipythonrobotframework: https://github.com/gtri/irobotframework


Try RobotKernel
---------------

You can try RobotKernel instantly without installing it at MyBinder_ cloud:

* Launch JupyterLab with RobotKernel: https://mybinder.org/v2/gh/robots-from-jupyter/robotkernel/master?urlpath=lab/tree/starter/robotkernel-quickstart

* Launch Jupyter Notebook with RobotKernel: https://mybinder.org/v2/gh/robots-from-jupyter/robotkernel/master?urlpath=tree/example.ipynb

Note: Log | Report -links on saved notebooks may not be clickable `until notebook is "trusted"`__ ("Trust Notebook" in JupyterLab Commands) the related cells have been executed again.

.. _MyBinder: https://mybinder.org/
__ https://jupyter-notebook.readthedocs.io/en/latest/security.html#updating-trust


Install RobotKernel
-------------------

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


Export to .robot
----------------

It is possible to export Robot Framework Jupyter notebooks to regular plain text ``.robot`` files for usage without Jupyter:

.. code:: bash

   $ jupyter nbconvert --to script example.ipynb

.. _nbconvert: https://nbconvert.readthedocs.io/


Execute notebooks
-----------------

RobotKernel installs a script named ``nbrobot``. It can be used instead of Robot Framework's ``robot`` test runner to execute Robot Framework with ``.ipynb``-extension support:

.. code:: bash

   $ nbrobot example.ipynb


Hacking RobotKernel
-------------------

Create and activate a new Python virtual environment:

.. code:: bash

    $ venv myenv
    $ source myenv/bin/activate

Install Jupyter:

.. code:: bash

    $ pip install --upgrade pip setuptools
    $ pip install jupyter

Clone this kernel:

.. code:: bash

    $ git clone https://github.com/robots-from-jupyter/robotkernel.git
    $ cd robotkernel

Install the kernel into the virtualenv in develop mode:

.. code:: bash

    $ python setup.py develop
    $ python -m robotkernel.install

Launch the jupyter:

.. code:: bash

    $ jupyter notebook

Reloading the kernel reloads the code.

`Learn more about Jupyter kernel development.`__

__ http://jupyter.readthedocs.io/en/latest/install.html


Nix-shell
---------

This repository includes an opinionated environment for running and developing RobotKernel with Nix_ with `Cachix-powered binary cache`__.

__ https://robots-from-jupyter.cachix.org/

Launch Jupyter Notebook with RobotKernel:

.. code:: bash

   $ nix-shell -E 'import (fetchTarball https://github.com/robots-from-jupyter/robotkernel/archive/master.tar.gz + "/shell.nix")' --run "jupyter notebook"

.. _Nix: https://nixos.org/nix/

Launch JupyterLab with RobotKernel:

.. code:: bash

   $ nix-shell -E 'import (fetchTarball https://github.com/robots-from-jupyter/robotkernel/archive/master.tar.gz + "/shell.nix")'
   $ jupyter labextension install jupyterlab_robotmode --app-dir=.jupyterlab
   $ jupyter lab --app-dir=.jupyterlab
   $ exit

Add ``--arg vim true`` to enable `vim bindings`_.

.. _vim bindings: https://github.com/lambdalisue/jupyter-vim-binding

Open development environment with Nix:

.. code:: bash

    $ git clone https://github.com/robots-from-jupyter/robotkernel.git
    $ cd robotkernel
    $ nix-build setup.nix -A env  # to generate ./result/bin/python for IDE
    $ nix-shell setup.nix -A develop
