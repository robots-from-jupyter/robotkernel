Robot Framework kernel for Jupyter notebooks
============================================

Work in progress.

Proof of concept.

Experimental.


Hacking
-------

See also: http://jupyter.readthedocs.io/en/latest/install.html

Create and activate clean Python virtual environment::

    $ venv jupyter
    $ source venv/bin/activate

Install Jupyter::

    $ pip install --upgrade pip setuptools
    $ pip install jupyter

Clone this kernel::

    $ clone https://github.com/datakurre/robotkernel
    $ cd robotkernel

Install the kernel into virtualenv in develop mode::

    $ python setup.py develop

Install the kernel into jupyter::

    $ jupyter kernelspec install $PWD/kernelspec --user

Launch the jupyter::

    $ jupyter notebook

Reloading the kernel reloads the code.
