# -*- coding: utf-8 -*-
# Derived from bash_kernel
# https://github.com/takluyver/bash_kernel/blob/master/bash_kernel/install.py
# Contributed by https://github.com/bollwyvl
from glob import glob
from IPython.utils.tempdir import TemporaryDirectory
from jupyter_client.kernelspec import KernelSpecManager

import argparse
import json
import os
import shutil
import sys


HERE = os.path.dirname(__file__)

kernel_json = {
    'argv': [
        # this is that complex to support Nix Python environments better
        list(
            filter(
                os.path.exists, [
                    os.path.
                    join(sys.prefix, 'bin', os.path.basename(sys.executable)),
                    os.path.join(sys.prefix, os.path.basename(sys.executable)),
                    os.path.join(sys.executable),
                ]
            )
        )[0],
        '-m',
        'robotkernel.kernel',
        '-f',
        '{connection_file}',
    ],
    'codemirror_mode': 'robotframework',
    'display_name': 'Robot Framework',
    'language': 'robotframework',
}


def install_my_kernel_spec(user=False, prefix=None):
    with TemporaryDirectory() as td:
        os.chmod(td, 0o755)  # Starts off as 700, not user readable

        with open(os.path.join(td, 'kernel.json'), 'w') as f:
            json.dump(kernel_json, f, indent=2, sort_keys=True)

        for res in glob(os.path.join(HERE, 'resources', '*')):
            shutil.copy2(res, td)

        print('Installing kernelspec for robotkernel')
        KernelSpecManager().install_kernel_spec(
            td,
            'robotkernel',
            user=user,
            prefix=prefix,
        )


def _is_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False  # assume not an admin on non-Unix platforms


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Install kernelspec for Robot Kernel',
    )
    prefix_locations = parser.add_mutually_exclusive_group()

    prefix_locations.add_argument(
        '--user',
        help='Install KernelSpec in user home directory',
        action='store_true',
    )
    prefix_locations.add_argument(
        '--sys-prefix',
        help='Install KernelSpec in sys.prefix. Useful in conda / virtualenv',
        action='store_true',
        dest='sys_prefix',
    )
    prefix_locations.add_argument(
        '--prefix',
        help='Install KernelSpec in this prefix',
        default=None,
    )

    args = parser.parse_args(argv)
    user = False
    prefix = None

    if args.sys_prefix:
        prefix = sys.prefix
    elif args.prefix:
        prefix = args.prefix
    elif args.user or not _is_root():
        user = True

    install_my_kernel_spec(user=user, prefix=prefix)


if __name__ == '__main__':
    main()
