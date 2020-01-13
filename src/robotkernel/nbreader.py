# -*- coding: utf-8 -*-
from robot import run_cli
from robot.libdoc import libdoc_cli
from robotkernel.constants import HAS_NBIMPORTER
from robotkernel.monkeypatches import inject_libdoc_ipynb_support
from robotkernel.monkeypatches import inject_robot_ipynb_support
import sys


if HAS_NBIMPORTER:
    import nbimporter  # noqa


def robot():
    inject_robot_ipynb_support()
    inject_libdoc_ipynb_support()
    return run_cli(sys.argv[1:])


def libdoc():
    inject_robot_ipynb_support()
    inject_libdoc_ipynb_support()
    return libdoc_cli(sys.argv[1:])


if __name__ == "__main__":
    robot()
