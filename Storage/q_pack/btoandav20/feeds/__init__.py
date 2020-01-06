#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

try:
    from .oandav20feed import OandaV20Data
except ImportError as e:
    pass  # The user may not have something installed
