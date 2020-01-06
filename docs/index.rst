RobotKernel
===========

RobotKernel is a `Robot Framework`_ IPython_ kernel for `Jupyter Notebook`_ and JupyterLab_. It powers RobotLab_ – the Robot Framework JupyterLab distribution.

RobotKernel requires Python 3.6 or later and Robot Framework 3.1 or later.

.. _Robot Framework: http://robotframework.org/
.. _IPython: https://ipython.org/
.. _Jupyter Notebook: https://jupyter.readthedocs.io/en/latest/
.. _JupyterLab: https://jupyterlab.readthedocs.io/en/stable/

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

The easiest way to install RobotKernel is RobotLab_, the Robot Framework JupyterLab distribution, but `it can also be installed manually`__.

.. _RobotLab: https://github.com/robots-from-jupyter/robotlab/releases
__ install.rst


Learn RobotKernel
-----------------

Learn how to use author Robot Framework test suites or resource files with a RobotKernel powered JupyterLab or Jupyter Notebook by following these introductory tutorials:

.. toctree::
   :maxdepth: 2

   notebooks/01 Running Code.ipynb
   notebooks/02 Python XKCD.ipynb
   notebooks/03 Running Robot.ipynb
   notebooks/04 Robot XKCD.ipynb
   notebooks/05 Interactive Selenium.ipynb
   notebooks/06 Importing Notebooks.ipynb
   notebooks/07 Prototyping Keywords.ipynb
   notebooks/08 Interactive WhiteLibrary.ipynb
   notebooks/09 Prototyping Libraries.ipynb


Export to .robot
----------------

It is possible to export Robot Framework Jupyter notebooks to regular plain text ``.robot`` files for usage without Jupyter tools:

From JupyterLab, export a notebook into  ``.robot`` file by choosing from the menu

1. File
2. Export Notebook As...
3. Export Notebook to Executable Script.

From Jupyter Notebook, export a notebook into ``.robot`` file by choosing from the menu

1. File
2. Download as
3. Robot Framework (.robot).

From command-line with nbconvert_:

.. code:: bash

   $ jupyter nbconvert --to script example.ipynb

.. _nbconvert: https://nbconvert.readthedocs.io/

Robot Framework is also supported by Jupytext_, which support exporting ``.robot`` from a notebook and keep them synchronized with as long as JupyterLab or Jupyter Notebooks is running on the background. This allows editing the notebook alternatively with Jupyter tools or the IDE of choice.

.. _Jupytext: https://jupytext.readthedocs.io/

Note: Exporting notebooks with inline python modules defined using ``%%python module`` magics may result in broken ``.robot`` files requiring manual clean up of the exported inline python code.

Execute notebooks
-----------------

RobotKernel installs a script named ``nbrobot``. It can be used instead of Robot Framework's ``robot`` test runner to execute Robot Framework with ``.ipynb``-extension support:

.. code:: bash

   $ nbrobot example.ipynb

In addition, it is also possible to execute notebooks with nbconvert_ to result a new notebook with embedded execution logs and reports:

.. code:: bash

   $ jupyter nbconvert --to notebook --execute example.ipynb

On execution error, the partially executed notebook may not be saved until an extra argument ``--ExecutePreprocessor.allow_errors=True`` is given:

.. code:: bash

   $ jupyter nbconvert --ExecutePreprocessor.allow_errors=True --to notebook --execute example.ipynb

This `may change`__ in future versions of nbconvert.

__ https://github.com/jupyter/nbconvert/issues/626

Note: When executing a notebook with nbconvert, each cell with tests cases or tasks will be executed as its own suite. This may cause differences in execution when compared to executing exported ``.robot`` files with ``robot`` or ``nbrobot``.
