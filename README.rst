Robot Framework kernel for Jupyter notebooks
============================================

Robot Framework language support for Jupyter notebooks.

Requires Python 3.6 or later.

Log | Report -links on existing notebooks are only active on trusted notebooks.

Try Robot Framework kernel at Binder
------------------------------------

Jupyter Notebook: https://mybinder.org/v2/gh/datakurre/robotkernel/master?urlpath=tree/example.ipynb

Jupyter Lab: https://mybinder.org/v2/gh/datakurre/robotkernel/master?urlpath=lab/tree/example.ipynb


Install Robot Framework kernel
------------------------------

.. code:: bash

   $ pip install robotkernel
   $ python -m robotkernel.install


Install Robot Framework kernel from Python 3 notebook
-----------------------------------------------------

.. code:: bash

   !pip install robotkernel
   !python -m robotkernel.install

After refreshing the notebook, it is possible change the kernel to Robot
Framework kernel or create a new notebook with Robot Framework kernel.


Executing notebooks
-------------------

It is possible to export test suites from Jupyter Notebook or Lab user interface (into traditional ``.robot`` files), but it is also possible to execute saved Jupyter notebook as such:

.. code:: bash

   $ jupyter nbconvert --to notebook --execute example.ipynb

This will stop the execution at first failing test case.

After execution with errors, to get a notebook with execution logs saved, an extra flag ``--ExecutePreprocessor.allow_errors=True`` must be set:

.. code:: bash

   $ jupyter nbconvert --ExecutePreprocessor.allow_errors=True --to notebook --execute example.ipynb


Nix-shell (https://nixos.org/nix/)
----------------------------------

.. code:: bash

   $ nix-shell -E 'import (fetchTarball https://github.com/datakurre/robotkernel/archive/master.tar.gz + "/shell.nix")' --run "jupyter notebook"

.. code:: bash

   $ nix-shell -E 'import (fetchTarball https://github.com/datakurre/robotkernel/archive/master.tar.gz + "/shell.nix")' --run "jupyter lab"

Add ``--arg sikuli true`` to include SikuliLibrary_.

Add ``--arg vim true`` to enable `vim bindings`_.

.. _SikuliLibrary: https://github.com/rainmanwy/robotframework-SikuliLibrary
.. _vim bindings: https://github.com/lambdalisue/jupyter-vim-binding


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

    $ git clone https://github.com/datakurre/robotkernel.git
    $ cd robotkernel

Install the kernel into virtualenv in develop mode::

    $ python setup.py develop

Install the kernel into jupyter::

    $ python -m robotkernel.install

Launch the jupyter::

    $ jupyter notebook

Reloading the kernel reloads the code.
