RobotKernel
===========

RobotKernel is a `Robot Framework`_ IPython_ kernel for `Jupyter Notebook`_ and JupyterLab_.

Requires Python 3.6 or later and Robot Framework 3.1 or later.

.. _Robot Framework: http://robotframework.org/
.. _IPython: https://ipython.org/
.. _Jupyter Notebook: https://jupyter.readthedocs.io/en/latest/
.. _JupyterLab: https://jupyterlab.readthedocs.io/en/stable/

Check also `ipythonrobotframework`_ for alternative Robot Framework IPython kernel.

.. _ipythonrobotframework: https://github.com/gtri/irobotframework


Try RobotKernel
---------------

You can try RobotKernel without installing it at MyBinder_ cloud:

Jupyter Notebook: https://mybinder.org/v2/gh/robots-from-jupyter/robotkernel/master?urlpath=tree/example.ipynb

JupyterLab: https://mybinder.org/v2/gh/robots-from-jupyter/robotkernel/master?urlpath=lab/tree/example.ipynb

Note: Log | Report -links on existing notebooks are only active on trusted notebooks.

.. _MyBinder: https://mybinder.org/


Install RobotKernel
-------------------

RobotKernel is included with RobotLab_ distribution, but there are also
plenty of other `installation options`_.

.. _RobotLab: https://github.com/robots-from-jupyter/robotlab/releases
.. _installation options: install.rst


Learn RobotKernel
-----------------

.. toctree::
   :maxdepth: 2

   notebooks/01 Running Code.ipynb
   notebooks/02 Python XKCD.ipynb
   notebooks/03 Running Robot.ipynb
   notebooks/04 Robot XKCD.ipynb
   notebooks/05 Interactive Selenium.ipynb
   notebooks/07 Executable Keywords.ipynb
   notebooks/08 Interactive WhiteLibrary.ipynb


Export robot files
------------------

It is possible to export test suites directly from Jupyter Notebook or JupyterLab user interface (into traditional ``.robot`` files), but also from command line:

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
