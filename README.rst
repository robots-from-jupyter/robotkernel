Robot Framework kernel for Jupyter notebooks
============================================

Robot Framework language support for Jupyter notebooks.

Requires Python 3.6 or later.


Try it at binder
----------------

Jupyter Notebook: https://mybinder.org/v2/gh/datakurre/robotkernel/master?urlpath=tree/example.ipynb

Jupyter Lab: https://mybinder.org/v2/gh/datakurre/robotkernel/master?urlpath=lab/tree/example.ipynb


Kernel installation
-------------------

.. code:: bash

   $ pip install robotkernel
   $ python -m robotkernel.install


Local install and development
-----------------------------

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
