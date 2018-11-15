# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Android-related functions
"""

import sys
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




def backup(slot: int, target=None, **options):
    """Backup a save file from an Android device, configurable by options."""
    opts = settings.get_options()
    opts.update(options.copy())
    method = opts['android'].get('method', '').lower()

    if method == 'ftp':
        try:
            return ftp_get(slot, target, **opts['ftp'])
        except OSError as e:
            if e.errno not in (101,  # Network is unreachable
                               111,  # No route to host
                               113): # Connection Refused
                raise
            raise u.FSException(
                "%s: is FTP enabled on Android device %s, port %d?", e,
                opts['ftp'].get('hostname'),
                opts['ftp'].get('port') or 21,
                errno=e.errno
            )

    elif method == 'adb':
        try:
            return adb_pull(slot, target, **opts['ftp'])
        #TODO: check for expected Exceptions and re-raise as FSException
        except Exception:
            raise

    elif method == 'local':
        opts.update({'main': {'platform': 'android'}})  # force platform
        source = os.path.join(settings.savepath(**opts), u.savename(slot))
        target = u.localpath(slot, target)
        return u.copy_file(source, target)

    raise u.FSException("Invalid or blank Android method: %r", method)




def adb_pull(slot: int, target: str = None) -> str:
    target = u.localpath(slot, target)
    data = adb_read(slot)
    with open(target, 'wb') as fd:
        fd.write(data)
    return target


def adb_push(slot: int, source: str = None) -> str:
    source = u.localpath(slot, source)
    with open(source, 'rb') as fd:
        data = fd.read()
    return adb_write(slot, data)


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


def adb_write(slot: int, data: bytes) -> str:  # @UnusedVariable
    # because raise NotImplementedError is too blunt...
    log.warning("adb_write() is currently a stub dummy!")
    return ""




def ftp_get(slot: int, target: str = None, **ftp_options) -> str:
    """
    Download a game save file from an Android FTP server to a local file.

    If `path` is a directory, save to that directory using game save file name.
    If blank save to current directory, else use it as full file and path name.

    See ftp_read() for documentation on other parameters.

    Return the saved local file full path, as a convenience.
    """
    target = u.localpath(slot, target)
    log.info("Saving game slot %s from Android FTP to %s", slot, target)
    data = ftp_read(slot, **ftp_options)
    with open(target, 'wb') as fd:
        fd.write(data)
    return target


def ftp_put(slot: int, source: str = None, **ftp_options) -> str:
    """
    Upload a local file to an Android FTP server as a game save file

    Use `source` file or 'VaultX.sav' in current directory. See ftp_write() for
    documentation on return value and other parameters.
    """
    source = u.localpath(slot, source)
    with open(source, 'rb') as fd:
        data = fd.read()
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
    - 'debug', if truthy, print FTP messages to stderr.
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
    options = settings.get_options()['ftp']
    options.update(ftp_options)
    debug = options['debug']

    if not options['hostname']:
        raise u.FSException("FTP hostname is blank, check your settings?")

    savename = u.savename(slot)

    ftp = ftplib.FTP()

    if debug:
        ftp.set_debuglevel(1 if debug else 0)
        # Redirect print() to stderr so ftplib debugging does not mix with
        # potentially print()-ed output
        stdout = sys.stdout  # save current stdout
        sys.stdout = sys.stderr

    try:
        log.info("Connecting to %s:%s", options['hostname'], options['port'] or 21)
        ftp.connect(options['hostname'], options['port'])
        ftp.login(options['username'], options['password'])
        ftp.cwd(options['savepath'])

        # read
        if read:
            data = bytearray()
            ftp.retrbinary('RETR {0}'.format(savename), data.extend)
            return bytes(data)

        # write
        log.debug("%s: %s", savename, info)
        ftp.storbinary('STOR {0}'.format(savename), io.BytesIO(data))
        return posixpath.join(options['savepath'], savename)
        # FTP always use Unix '/' as path separator, hence posixpath

    finally:
        try:
            ftp.quit()
        except AttributeError:  # Exception before or at ftp.connect()
            pass
        finally:
            if debug:
                sys.stdout = stdout  # restore original stdout


def _main(argv=None):  # @UnusedVariable
    #FIXME: this _main() is terribly outdated, replace with something useful
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




if __name__ == '__main__':
    try:
        sys.exit(_main(sys.argv[1:]))
    except u.FSException as e:
        log.error(e)
    except (KeyboardInterrupt, BrokenPipeError):
        pass
