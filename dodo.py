"""dodo.py"""
from pathlib import Path
from re import sub
import shutil
from hashlib import sha256
import sys
import os
import subprocess
import json

import doit.tools

PY = Path(sys.executable)
DOIT_CONFIG = dict(verbosity=2)
DODO = Path(__file__)
HERE = DODO.parent
CONF = HERE / "conf.py"
DIST = HERE / "dist"
DOCS = HERE / "docs"
LITE = HERE / "lite"
LICENSE = HERE / "LICENSE"
EXT = LITE / "jupyterlite-robotkernel"
EXT_LICENSE = EXT / LICENSE.name
EXT_SRC_PKG = EXT / "package.json"
EXT_SRC_PKG_DATA = json.load(EXT_SRC_PKG.open())
EXT_DIST_PKG = EXT / "py_src/jupyterlite_robotkernel/labextension/package.json"
EXT_DIST = EXT / "dist"
EXT_WHL_NAME = f"""jupyterlite_robotkernel-{EXT_SRC_PKG_DATA["version"]}-py3-none-any.whl"""
EXT_WHL = EXT_DIST / EXT_WHL_NAME
EXT_ICON = EXT / "style/robotkernel.png"
SHA256SUMS = DIST / "SHA256SUMS"
KERNEL_DATA = HERE / "src/robotkernel/resources/kernel"
KERNEL_ICON = KERNEL_DATA / "logo-64x64.png"
WHL_PY = [
    p
    for p in [
        HERE / "setup.py",
        *Path("src").rglob("*.py"),
    ]
    if p.name != "_version.py"
]
WHL_MD = [HERE / "README.rst"]
WHL_DEPS = [
    HERE / "setup.cfg",
    *KERNEL_DATA.rglob("*"),
    *WHL_MD,
    *WHL_PY,
]
ALL_PY = [DODO, *WHL_PY]
ALL_MD = [*WHL_MD]
ALL_JSON = [
    *LITE.glob("*.json"),
    *LITE.glob("*/*.json"),
    *[p for p in WHL_DEPS if p.suffix == "json"],
]
SOURCE_DATE_EPOCH = (
    subprocess.check_output(["git", "log", "-1", "--format=%ct"])
    .decode("utf-8")
    .strip()
)
os.environ.update(SOURCE_DATE_EPOCH=SOURCE_DATE_EPOCH)


def task_dist():
    """build distributions"""

    def hashfile():
        lines = []

        for p in sorted([*DIST.glob("robotkernel*.whl"), *DIST.glob("robotkernel*.tar.gz")]):
            if p == SHA256SUMS:
                continue
            lines += ["  ".join([sha256(p.read_bytes()).hexdigest(), p.name])]

        output = "\n".join(lines)
        print(output)
        SHA256SUMS.write_text(output)

    yield dict(
        name="robotkernel",
        doc="build robotkernel distributions",
        file_dep=WHL_DEPS,
        actions=[
            lambda: [shutil.rmtree(DIST) if DIST.is_dir() else None, None][-1],
            [PY, "setup.py", "sdist"],
            [PY, "-m", "pip", "wheel", "-w", DIST, "--no-deps", "."],
            hashfile,
        ],
        targets=[SHA256SUMS],
    )


@doit.create_after("dist")
def task_labext():
    pkg = EXT / "package.json"
    lock = EXT / "yarn.lock"
    integrity = EXT / "node_modules" / ".yarn-integrity"
    packages = EXT / "packages"
    packages_pkg = [
        packages / "robolite-kernel" / "package.json",
        packages / "robolite-kernel-extension" / "package.json",
    ]
    packages_lock = [
        packages / "robolite-kernel" / "yarn.lock",
        packages / "robolite-kernel-extension" / "yarn.lock",
    ]
    packages_integrity= [
        packages / "robolite-kernel" / "node_modules" / ".yarn-integrity",
        packages / "robolite-kernel-extension" / "node_modules" / ".yarn-integrity",
    ]
    packages_ts_src = [
        *(packages / "robolite-kernel" / "src").rglob("*.ts"),
        *(packages / "robolite-kernel-extension" / "src").rglob("*.ts"),
    ]
    packages_ts_buildinfo = [
        *(packages / "robolite-kernel" / "src").rglob("tsconfig.buildinfo"),
        *(packages / "robolite-kernel-extension" / "src").rglob("tsconfig.buildinfo"),
    ]
    lerna = EXT / "node_modules" / ".bin" / "lerna"

    def _do(*args, **kwargs):
        cwd = str(kwargs.pop("cwd", EXT))
        return doit.tools.CmdAction([*args], **kwargs, cwd=cwd, shell=False)

    def _copy_static():
        copy_one(KERNEL_ICON, EXT_ICON)
        copy_one(LICENSE, EXT_LICENSE)

    yield dict(
        name="lerna install",
        file_dep=[pkg] + ([lock] if lock.exists() else []),
        targets=[integrity],
        actions=[_do("yarn", "--prefer-offline", "--ignore-optional")],
    )

    yield dict(
        name="lerna bootstrap",
        file_dep=[*packages_pkg] + ([lock for lock in packages_lock if lock.exists()]),
        targets=[*packages_integrity],
        actions=[_do(lerna, "bootstrap")],
    )

    yield dict(
        name="copy:static",
        file_dep=[*DIST.glob("*.any.whl"), KERNEL_ICON, LICENSE],
        targets=[EXT_ICON, EXT_LICENSE],
        actions=[_copy_static],
    )
    yield dict(
        name="build:ts",
        file_dep=[*packages_ts_src, *packages_pkg, *packages_integrity],
        targets=[*packages_ts_buildinfo],
        actions=[_do(lerna, "run", "build:lib")],
    )

    yield dict(
        name="build:ext",
        file_dep=[*packages_ts_buildinfo, *packages_integrity, *packages_pkg],
        targets=[EXT_DIST_PKG],
        actions=[_do(lerna, "run", "build:labextension")],
    )

    yield dict(
        name="wheel:ext",
        file_dep=[EXT_DIST_PKG, EXT_LICENSE],
        actions=[_do(PY, "-m", "pip", "wheel", "--no-deps", "-w", EXT_DIST, ".")],
        targets=[EXT_WHL],
    )


@doit.create_after("labext")
def task_lite():
    """build jupyterlite site and pre-requisites"""
    wheel = sorted(DIST.glob("robotkernel*.whl"))[-1]

    def _clean_wheels():
        # Remove wheels that conflict with pyolite shims
        for path in (LITE / "pypi").glob("ipykernel-*"):
            os.unlink(path)
        for path in (LITE / "pypi").glob("widgetsnbextension-*"):
            os.unlink(path)
        # Remove binary wheels
        for path in set((LITE / "pypi").glob("*")) - (set((LITE / "pypi").glob("*-none-any.whl"))):
            os.unlink(path)
        # Remove addon fetched
        for path in json.loads((EXT / "py_src" / "jupyterlite_robotkernel" / "addons" / "wheels.json").read_text()):
            for path_ in (LITE / "pypi").glob(path.rsplit("/")[-1]):
                os.unlink(path_)

    yield dict(
        name="wheels",
        file_dep=[SHA256SUMS, wheel],
        actions=[
            (doit.tools.create_folder, [LITE / "pypi"]),
            doit.tools.CmdAction(
                [PY, "-m", "pip", "wheel", "--prefer-binary", "--no-deps", wheel],
                cwd=str(LITE / "pypi"),
                shell=False,
            ),
            # Not sure, why these were not discovered from conda environment
            doit.tools.CmdAction(
                [PY, "-m", "pip", "wheel", "--no-deps", "--prefer-binary", "jupyterlab-drawio"],
                cwd=str(LITE),
                shell=False,
            ),
            _clean_wheels,
        ],
    )

    def _build():
        subprocess.check_call(
            [
                PY,
                "-m",
                "jupyter",
                "lite",
                "build",
                "--debug",
                "--contents",
                str(LITE / "contents"),
                "--LiteBuildConfig.federated_extensions",
                f"{list(LITE.glob('jupyterlab_drawio*'))[-1]}",
                "--LiteBuildConfig.federated_extensions",
                EXT_WHL,
            ],
            cwd=str(LITE)
        )
        subprocess.check_call(
            [
                "mkdir",
                "-p",
                "_",
            ],
            cwd=str(LITE)
        )
        subprocess.check_call(
            [
                "mv",
                "_output",
                "_/_",
            ],
            cwd=str(LITE)
        )

    yield dict(
        name="build",
        file_dep=[
            SHA256SUMS,
            wheel,
            EXT_WHL,
            *LITE.glob("*.json"),
            *(LITE / "retro").glob("*.json"),
            *DOCS.rglob("*.ipynb"),
        ],
        actions=[_build],
        targets=[LITE / "_/_/jupyter-lite.json"],
    )


@doit.create_after("lite")
def task_docs():
    def post():
        CONF.write_text(
            "\n".join(
                [
                    "import subprocess",
                    """subprocess.check_call(["doit", "lite"])""",
                    sub(
                        r'external_toc_path = "\S+_toc.yml"',
                        r'external_toc_path = "_toc.yml"',
                        CONF.read_text(),
                    ),
                ]
            )
        )

    yield dict(
        name="sphinx-config",
        file_dep=["_toc.yml", "_config.yml"],
        actions=[
            "jb config sphinx .",
            post,
            "black conf.py",
        ],
        targets=[CONF],
    )

    yield dict(
        name="sphinx-build",
        file_dep=[
            CONF,
            *DOCS.rglob("*.ipynb"),
            *(HERE / "_templates").glob("*.html"),
            LITE / "_/_/jupyter-lite.json",
        ],
        actions=["sphinx-build . _build/html %(pos)s"],
        pos_arg="pos",
        targets=[HERE / "_build/html/.buildinfo"],
    )


def copy_one(src, dest):
    if not src.exists():
        return False
    if not dest.parent.exists():
        dest.parent.mkdir(parents=True)
    if dest.exists():
        if dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()
    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
