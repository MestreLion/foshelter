# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Fallout Shelter Dwellers info
"""

import sys
import os.path
import json
import logging
import re
import argparse


MAX_LEVEL = 50

FULL_END  = 10
MID_END   = 15
MAX_END   = 17


log = logging.getLogger(__name__)




def total_hp(total_endurance, level=0):
    """
    Total Hit Points at level based on total endurance points gained
    https://www.reddit.com/r/foshelter/comments/3jmnhy
    """
    if not level:
        level = MAX_LEVEL

    return 105 + ((level - 1) * 2.5) + (0.5 * total_endurance)


def endurance_points(l1, e1, l2=0, e2=0, level=0):
    """
    Total Endurance Points gained at level based on leveling pattern

    Pattern is: Leveled from level 1 to l1 with e1 endurance, then until level
    `l2` with `e2` endurance, finally until level `level` with MAX_END.

    If falsy, `l2` is set to `l1`, effectively ignoring it along with `e2`
    If falsy, `level` is considered to be MAX_LEVEL
    """
    if not l2:
        l2=l1

    if not level:
        level = MAX_LEVEL

    endpts = (
                e1 * (l1  -  1)
        +       e2 * (l2  - l1)
        +  MAX_END * (level - l2)
    )
    # e1 and e2 might be floats for equivalence purposes, but if they model
    # a real leveling pattern then result will be an integer, save for
    # binary floating-point precision limitation. Hence the assert
    assert round(endpts, 5) == round(endpts)
    return int(round(endpts))


def e17_equiv(l1, e1, l2=0, e2=0):
    """
    E17-equivalent level based on leveling pattern

    Outputs the level that yields the same Endurance Points, hence total HP,
    as if the dweller had leveled from 1 to level with FULL_END endurance
    and then started leveling with MAX_END.

    For example, a dweller that leveled from 1 to 50 with 13 endurance is a 29,
    which means he has the same HP as someone who leveled from 1 to 29 with 10E,
    and then 17E afterwards. Their leveling patterns yielded the same result.

    This gives a common baseline to compare total HP of dwellers with different
    leveling patterns. Each level means one more level up with FULL_END instead
    of MAX_END, which corresponds to 3.5 less points in maximum total HP.

    Note that this equivalent level is an abstraction, might be more than 50
    and is not necessarily an integer

    For reference, the equivalent level for a dweller that leveled up from 1 to
    50 with a constant endurance is:
     1E: 113, HP=252,   lowest possible max HP
     5E:  85, HP=350
    10E:  50, HP=472.5, 50 is by definition
    13E:  29, HP=546
    15E:  15, HP=595
    17E:   1, HP=644,   1 also by definition, and 644 is max possible HP

    Pattern is like in endurance_points(): Leveled from level 1 to l1 with e1
    endurance, then until level `l2` with `e2` endurance. Assumed to be
    MAX_END afterwards until MAX_LEVEL.

    If falsy, `l2` is set to `l1`, effectively ignoring it along with `e2`
    """
    if not l2:
        l2 = l1

    # Alternative:
    #e17= 1.0 * (l2*(MAX_END-e2) + l1*(e2-e1) + e1   - FULL_END) / (MAX_END-FULL_END)
    e17 = 1.0 * (MAX_END*l2 - e2*(l2-l1) - e1*(l1-1) - FULL_END) / (MAX_END-FULL_END)

    epts  = endurance_points(l1, e1, l2, e2)
    hptot =  total_hp(epts)

    log.debug("(%2d, %2d), (%2d, %2d): %4.1fE%d, EPTS=%d, HPMAX=%.1f",
              l1, e1, l2, e2, e17, MAX_END, epts, hptot)

    # Assert the equivalence in Total Endurance Points
    epts_test = endurance_points(e17, FULL_END)
    try:
        assert epts == epts_test
    except AssertionError:
        raise FSException(
            "Assertion Failed!"
            " epts({l1}, {e1}, {l2}, {e2})=%s !="
            " epts(%s, BASEEND)=%s" %
            (l1, e1, l2, e2, epts, e17, endurance_points(e17, FULL_END))
        )

    return e17, hptot




class FSException(Exception):
    pass



class Dweller():

    re_einfo = re.compile(
        r'\b(?P<einfo>'
            r'[0-9]{1,2},([0-9]{1,2}|\?{1,2})|'  # 09,09|??
            r'[0-9]{1,4}|'                       # 0009
            r'[0-9]{0,2}E[0-9]{1,2}'             # 00E09
        r')\b'
    )
    re_job = re.compile(r'^([A-Z]([0-9]{2}|[A-Z]{2}|\?\?)) +')


    @classmethod
    def from_dict(cls, d):
        return cls(
            d['serializeId'],
            '{name} {lastName}'.format(**d),
            d['experience']['currentLevel'],
            d['health']['maxHealth'],
        )


    def __init__(self, ID, name, level, hp):
        self.id = ID
        self.name = name
        self.hp = hp
        self.level = level

        self.job      = self._job(self.name)
        self.newcomer = not self.job
        self.erating  = self._e17equiv()
        self.einfo    = self._einfo(self.name)
        self.e17info  = self._parse_einfo(self.einfo)
        self.badinfo  = self.einfo and abs(self.e17info - self.erating) >= 1


    def _job(self, name):
        m = re.search(self.re_job, name)
        if m:
            return m.group(1)


    def _newcomer(self, name):
        m = re.search(self.re_job, name)
        return False if m else True


    def _einfo(self, name):
        m = re.search(self.re_einfo, name)
        if m:
            return m.group('einfo')


    def _e17equiv(self):
        endpts = (self.hp - 105 - 2.5 * (self.level - 1)) / 0.5
        e17 = 1.0 * (self.level*MAX_END - FULL_END - endpts) / (MAX_END - FULL_END)

        assert total_hp(endpts, self.level) == self.hp
        assert endurance_points(e17, FULL_END, 0, 0, self.level) == endpts

        return e17


    def _parse_einfo(self, einfo):
        """
        Parse the Endurance Information, a way to describe a leveling pattern.
        Return the E17-equivalent level of that information. See e17_equiv()
        Formats are:
        xx   : E10 (FULL_END) until level xx, and E17 (MAX_END) afterwards
        xxyy : E10 until level xx, E15 (MID_END) until level yy, E17 afterwards
                   both xx and yy are required to be double digits
        xx,y:  E0y until level xx, E17 afterwards.
        xxEyy: E10 until level xx, Eyy* afterwards
        Exx  : Exx* all the way from level 1 to 50 (MAXLEVEL). Same as 1Exx
        All formats but 'xxyy' allow single digits to either or both xx and yy
        * : When using E notation, a single-digit Ez actually means E(10+z)
        """

        if not einfo:
            return 0

        # Try 'E' notation: xxEyy, Exx, Ex
        '([0-9]{0,2})E([0-9]{1,2})'
        if 'E' in einfo:
            log.debug("xxEyy")
            lvl, end = einfo.split('E', 1)

            if len(end) == 1:
                end = int(end) + FULL_END  # single digit after E. Assume x+10
            end = int(end)

            if not lvl:
                lvl = 1  # Exx/Ex
            lvl = int(lvl)

            return e17_equiv(lvl, FULL_END, MAX_LEVEL, end)[0]

        # Try 'xx,y'
        if ',' in einfo:
            log.debug("xx,y")
            lvl, end = (int(_) for _ in einfo.split(',', 1))
            return e17_equiv(lvl, end)[0]

        # Try 'xxyy'
        if len(einfo) > 2:
            log.debug("xxyy")
            l1, l2 = int(einfo[:2]), int(einfo[2:])
            if l2 < l1:
                raise FSException("%r: Invalid endurance format: %r (%d <= %d)" %
                                  (self, einfo, l2, l1))
            if False and l2 == l1:
                log.warning("%r: Possibly erroneous endurance format: %r (%d == %d)",
                            self, einfo, l2, l1)
            return e17_equiv(l1, FULL_END, l2, MID_END)[0]

        # Assume 'xx'
        log.debug("xx")
        lvl = int(einfo)
        return e17_equiv(lvl, FULL_END)[0]


    def __repr__(self):
        return '<{name}>'.format(**vars(self))


    def __str__(self):
        return ('\t'.join((
            '{badinfo}',
            '{id:3d}',
            '{level:2d}',
            '{hp:.1f}',
            '{erating:4.1f}',
            '{e17info:4.1f}',
            '{job}',
            '{newcomer}',
            '{name}',
        )).format(**vars(self)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-q', '--quiet',
                       dest='loglevel',
                       const=logging.WARNING,
                       default=logging.INFO,
                       action="store_const",
                       help="Suppress informative messages.")
    group.add_argument('-v', '--verbose',
                       dest='loglevel',
                       const=logging.DEBUG,
                       action="store_const",
                       help="Verbose mode, output extra info.")

    parser.add_argument(nargs='?',
                        metavar='JSONFILE',
                        default=os.path.join(os.path.dirname(__file__),
                                             'Vault1.json'),
                        dest='path',
                        help="Decrypted save game data in JSON format."
                            " [Default: %(default)s")

    args = parser.parse_args()
    args.debug = args.loglevel == logging.DEBUG

    logging.basicConfig(level=args.loglevel, format='%(levelname)s: %(message)s')

    try:
        with open(args.path) as fp:
            data = json.load(fp)
    except json.decoder.JSONDecodeError as e:
        log.error('Could not load Vault data. is it a decrypted JSON file? %s',
                  args.path)
        sys.exit(1)

    dwellers = [Dweller.from_dict(_) for _ in data['dwellers']['dwellers']]

    for d in dwellers:
        print(d)
