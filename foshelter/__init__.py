# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Package setup
"""

# Add dummy Null Handler so in-package logging does fail
import logging as _logging
_logging.getLogger(__name__).addHandler(_logging.NullHandler())


class FSException(Exception):
    pass
