# -*- coding: utf-8 -*-
import pkg_resources


try:
    from robotkernel.selectors_white import WhiteLibraryCompanion
    import WhiteLibrary

    assert WhiteLibrary
    assert WhiteLibraryCompanion
except ImportError:
    pass

__version__ = str(pkg_resources.get_distribution("robotkernel").version)
