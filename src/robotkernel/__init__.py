# -*- coding: utf-8 -*-
import pkg_resources


try:
    import WhiteLibrary
    from robotkernel.selectors_white import WhiteLibraryCompanion

    assert WhiteLibrary
    assert WhiteLibraryCompanion
except ImportError:
    pass

__version__ = str(pkg_resources.get_distribution("robotkernel").version)
