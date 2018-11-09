# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Android-related functions
"""

import os.path
import logging
import ftplib
import io

try:
    # PyPI: pip install adb  # Require libusb1>=1.0.16 (Ubuntu 16.06+_
    import adb.adb_commands, adb.sign_pycryptodome  # @UnresolvedImport
except ImportError:
    adb = None

from . import FSException


GAMEDIR = '/Android/data/com.bethsoft.falloutshelter/files'

log = logging.getLogger(__name__)




def get_filename(vault: int) -> str:
    return 'Vault{0}.sav'.format(vault)




def adb_read(vault: int) -> bytes:
    # https://github.com/google/python-adb
    if not adb:
        raise FSException("adb package is not available")

    # KitKat+ devices require authentication
    path = os.path.join(os.path.expanduser('~'), '.android', 'adbkey')
    signer = adb.sign_pycryptodome.PycryptodomeAuthSigner(path)

    # Connect to the device
    device = adb.adb_commands.AdbCommands()
    device.ConnectDevice(rsa_keys=[signer])

    return device.Pull(os.path.join('/mnt/sdcard', GAMEDIR, get_filename(vault)))


def adb_write(vault: int, data: bytes) -> None:
    pass




def ftp_read(vault: int, **ftp_options) -> bytes:
    return _ftp_readwrite(vault, True, None, **ftp_options)


def ftp_write(vault: int, data: bytes, **ftp_options) -> None:
    _ftp_readwrite(vault, False, data, **ftp_options)


def _ftp_readwrite(vault, read, data, **ftp_options):
    if not ftp_options['hostname']:
        raise FSException("FTP hostname is blank, check your settings?")

    ftp = ftplib.FTP()
    ftp.set_debuglevel(1 if ftp_options.get('debug', False) else 0)
    ftp.connect(ftp_options['hostname'], ftp_options['port'])

    try:
        ftp.login(ftp_options['username'], ftp_options['password'])
        ftp.cwd(ftp_options['savepath'])

        # read
        if read:
            data = bytearray()
            ftp.retrbinary('RETR {0}'.format(get_filename(vault)), data.extend)
            return bytes(data)

        # write
        ftp.storbinary('STOR {0}'.format(get_filename(vault)), io.BytesIO(data))

    finally:
        ftp.quit()




if __name__ == '__main__':
    from .settings import get_options, basic_logging
    basic_logging()

    options = get_options()
    method = options['android']['method']
    options['ftp']['debug'] = True
    vault = 1

    if method == 'ftp':
        try:
            data = ftp_read(vault, **options['ftp'])
            print("{0}, {1} bytes: {2}...".format(
                    get_filename(vault),
                    len(data),
                    data[:80]))
            ftp_write(4, data, **options['ftp'])
        except OSError as e:
            if e.errno not in (111, 113):  # Connection Refused, No route to host
                raise
            log.error("%s: is FTP enabled on Android device %s, port %d?", e,
                      options['ftp']['hostname'],options['ftp']['port'] or 21)
        except FSException as e:
            log.error(e)

    elif method == 'adb':
        print(adb_read(1)[:80])

    else:
        log.error("Invalid or blank Android method: %s", method)
