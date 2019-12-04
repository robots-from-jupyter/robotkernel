"""Completion implementations."""

from IPython.core.completerlib import get_root_modules
from robot.libraries import STDLIBS
from typing import List


def complete_libraries(needle: str,) -> List[str]:
    """Complete library names."""
    matches = []

    for lib in list(STDLIBS) + list(get_root_modules()):
        if needle in lib.lower():
            matches.append(lib)

    return matches
