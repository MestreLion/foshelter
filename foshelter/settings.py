# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Settings and directories
"""

import os.path
import configparser
import logging


FACTORY = {
    'main': {
        'platform': 'android',
    },
    'android': {
        'method'  : 'ftp',  # options: 'local', 'ftp', 'adb'
    },
    'windows': {
        'savepath': r'%UserProfile%\Documents\My Games\Fallout Shelter',
    },
    'steam': {
        'savepath': r'%LocalAppData%\FalloutShelter',
    },
    'ftp': {
        'hostname': '',
        'username': '',  # Leave blank for anonymous access
        'password': '',
        'savepath': '/Android/data/com.bethsoft.falloutshelter/files',
        'port'    : 0,   # 0 for default FTP port (21)
    },
}
OPTIONS = {}

log = logging.getLogger(__name__)




def get_options() -> dict:
    if OPTIONS:
        # Use the "cached" copy
        return OPTIONS

    options = OPTIONS
    options.update(FACTORY)

    configdir = os.path.join(
        os.environ.get('APPDATA') or
        os.environ.get('XDG_CONFIG_HOME') or
        os.path.join(os.environ['HOME'], '.config'),
        __package__
    )

    paths = tuple(os.path.realpath(os.path.join(path, 'config.ini')) for path in
                  (os.path.join(os.path.dirname(__file__), '..'), configdir))

    cp = configparser.ConfigParser(inline_comment_prefixes='#')
    config = cp.read(paths, encoding='utf-8')

    if not config:
        log.warning("Use factory default settings, config not found in %s", paths)
        return FACTORY

    def getlist(s, o):
        return [_.strip() for _ in cp.get(s, o).split(',')]

    # .keys() to avoid 'RuntimeError: dictionary changed size during iteration'
    for section in options.keys():
        if not cp.has_section(section):
            log.warning("Section [%s] not found in %s", section, config)
            continue

        for opt in options[section]:
            if   isinstance(options[section][opt], bool ): get = cp.getboolean
            elif isinstance(options[section][opt], int  ): get = cp.getint
            elif isinstance(options[section][opt], float): get = cp.getfloat
            elif isinstance(options[section][opt], list ): get = getlist
            else                                         : get = cp.get

            try:
                options[section][opt] = get(section, opt)

            except configparser.NoOptionError as e:
                log.warning("%s in %s", e, config)

            except ValueError as e:
                log.warning("%s in '%s' option of %s", e, opt, config)

    return options


def basic_logging():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s: %(message)s')




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    print(get_options())
