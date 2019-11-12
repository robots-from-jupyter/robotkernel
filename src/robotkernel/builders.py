# -*- coding: utf-8 -*-
from robotkernel.constants import HAS_RF32_PARSER


if HAS_RF32_PARSER:
    from robotkernel.builders_32 import build_suite
else:
    from robotkernel.builders_31 import build_suite

assert build_suite
