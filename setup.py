import os
import setuptools

name = 'robotkernel'

__version__ = None

with open(os.path.join(name, '_version.py')) as fp:
    exec(fp.read())

with open('README.rst') as fp:
    README = fp.read()

setup_args = dict(
    name=name,
    version=__version__,
    description='A Jupyter kernel for interactive acceptance-test-driven'
                ' development with the Robot Framework',
    long_description=README,
    url='https://github.com/datakurre/robotkernel',
    author='Asko Soukka',
    packages=setuptools.find_packages(),
    # TODO: Pick a license, add here and below, add text to repo, etc.
    # license="BSD-3-Clause",
    install_requires=[
        'ipykernel',
        'IPython',
        'pillow',
        'pygments',
        'robotframework-seleniumlibrary',
        'robotframework',
    ],
    keywords=[
        'Interactive',
        'Interpreter',
        'Shell',
        'Testing',
        'Web',
    ],
    classifiers=[
        'Framework :: Jupyter',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        # 'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Quality Assurance'
        'Topic :: Software Development :: Testing',
    ],
    zip_safe=False,
)

if __name__ == '__main__':
    setuptools.setup(**setup_args)
