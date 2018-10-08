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

.. toctree::
   :maxdepth: 2

   example.ipynb
