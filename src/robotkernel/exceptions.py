# -*- coding: utf-8 -*-


class BrokenOpenConnection(Exception):
    """Broken sticky connection that should be closed."""

    def __init__(self, connection):
        """Init with connection be closed."""
        self.connection = connection
