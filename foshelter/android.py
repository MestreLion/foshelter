# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Android-related functions
"""

import os.path
import posixpath
import logging
import ftplib
import io

try:
    # PyPI: pip install adb  # Require libusb1>=1.0.16 (Ubuntu 16.06+_
    import adb.adb_commands, adb.sign_pycryptodome  # @UnresolvedImport
except ImportError:
    adb = None

from . import util as u
from . import settings


GAMEDIR = '/Android/data/com.bethsoft.falloutshelter/files'

log = logging.getLogger(__name__)




def adb_read(slot: int) -> bytes:
    # https://github.com/google/python-adb
    if not adb:
        raise u.FSException("adb package is not available")

    # KitKat+ devices require authentication
    path = os.path.join(os.path.expanduser('~'), '.android', 'adbkey')
    signer = adb.sign_pycryptodome.PycryptodomeAuthSigner(path)

    # Connect to the device
    device = adb.adb_commands.AdbCommands()
    device.ConnectDevice(rsa_keys=[signer])

    return device.Pull(os.path.join('/mnt/sdcard', GAMEDIR, u.savename(slot)))


def adb_write(slot: int, data: bytes) -> None:
    pass


def ftp_get(slot: int, path: str = None, **ftp_options) -> str:
    """
    Download a game save file from an Android FTP server to a local file
    Save file as `path` or as 'VaultX.sav' in current directory. See ftp_read()
    for documentation on other parameters.
    Return the saved local file full path, as a convenience.
    """
    if not path:
        path = u.savename(slot)
    data = ftp_read(slot, **ftp_options)
    open(path, 'wb').write(data)
    return path


def ftp_put(slot: int, path: str = None, **ftp_options) -> str:
    """
    Upload a local file to an Android FTP server as a game save file
    Use `path` file or 'VaultX.sav' in current directory. See ftp_write() for
    documentation on return value and other parameters.
    """
    if not path:
        path = u.savename(slot)
    data = open(path, 'rb').read()
    return ftp_write(slot, data, **ftp_options)


def ftp_read(slot: int, **ftp_options) -> bytes:
    """
    Read and return a game save file data from an Android Device FTP server.

    Source FTP file is determined by `slot` number, which is translated
    to a filename such as 'Vault1.sav'. Currently Fallout Shelter only supports
    3 save slots, but this is not enforced here.

    `ftp_options` is a dict for FTP access and credentials. Expected keys are:
    'hostname', 'username', 'password', 'savepath', 'port' and 'debug'.
    For missing keys the default values from config file will be used.
    Additional keys are ignored.

    Most keys are self-explanatory, with a few caveats:
    - 'hostname' might be an IP address, usually from a LAN, and a blank string
      raises an exception.
    - 'port', if 0 or otherwise falsy, uses the default FTP port, 21.
    - if 'username' is blank, use anonymous FTP access and ignore 'password'
    - 'debug', if truthy, print FTP messages to stdout. Note it does NOT print
      to stderr, unfortunately, so it can and WILL cause a mess if return data
      is also printed, specially if output is redirected to file.
    """
    return _ftp_readwrite(slot, True, None, **ftp_options)


def ftp_write(slot: int, data: bytes, **ftp_options) -> str:
    """
    Write data to game save file via FTP server on an Android device.

    'slot' and 'ftp_options' are as documented in ftp_read().

    Create (or replace) the selected FTP file with `data` content.
    Return the full remote file path written, as a convenience.
    """
    return _ftp_readwrite(slot, False, data, **ftp_options)


def _ftp_readwrite(slot: int, read: bool, data: bytes, **ftp_options):
    """
    Read or write save game data to an Android device FTP server.

    `read` indicates mode of operation, truthy for Read, otherwise Write.

    This is not meant to be called directly. Use ftp_read()/ftp_write() instead
    See their respective documentation for parameters and return value
    """
    options = settings.get_options()['ftp'].update(ftp_options)

    if not options['hostname']:
        raise u.FSException("FTP hostname is blank, check your settings?")

    savename = u.savename(slot)

    #TODO: if debug, temporarily redirect print() to stderr

    ftp = ftplib.FTP()
    ftp.set_debuglevel(1 if options.get('debug', False) else 0)
    ftp.connect(options['hostname'], options['port'])

    try:
        ftp.login(options['username'], options['password'])
        ftp.cwd(options['savepath'])

        # read
        if read:
            data = bytearray()
            ftp.retrbinary('RETR {0}'.format(savename), data.extend)
            return bytes(data)

        # write
        ftp.storbinary('STOR {0}'.format(savename), io.BytesIO(data))
        return posixpath.join(options['savepath'], savename)
        # FTP always use Unix '/' as path separator, hence posixpath

    finally:
        ftp.quit()




if __name__ == '__main__':
    u.setup_logging()

    options = settings.get_options()
    method = options['android']['method']
    options['ftp']['debug'] = True
    slot = 1

    if method == 'ftp':
        try:
            data = ftp_read(slot, **options['ftp'])
            print("{0}, {1} bytes: {2}...".format(
                    u.savename(slot),
                    len(data),
                    data[:80]))
            ftp_write(4, data, **options['ftp'])
        except OSError as e:
            if e.errno not in (111, 113):  # Connection Refused, No route to host
                raise
            log.error("%s: is FTP enabled on Android device %s, port %d?", e,
                      options['ftp']['hostname'],options['ftp']['port'] or 21)
        except u.FSException as e:
            log.error(e)

    elif method == 'adb':
        print(adb_read(1)[:80])

    else:
        log.error("Invalid or blank Android method: %s", method)
