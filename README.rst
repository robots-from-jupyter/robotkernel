Robot Framework kernel for Jupyter notebooks
============================================

Proof-of-concept that adds Robot Framework language support for Jupyter
notebooks.

Currently for Python >= 3.6 only.


Try it out with Docker
----------------------

::

    $ docker run --rm -p 8888:8888 datakurre/robotkernel


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

    $ jupyter kernelspec install $PWD/kernelspec/robotkernel --user

Launch the jupyter::

    $ jupyter notebook

Reloading the kernel reloads the code.
