# This file is part of Foshelter, see <https://github.com/MestreLion/foshelter>
# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
Fallout Shelter save game encryptor and decryptor

Saved games are Vault*.sav files, generally located at:

Android: /Android/data/com.bethsoft.falloutshelter/files
Windows: C:\\Users\\<YOURUSERNAME>\\Documents\\My Games\\Fallout Shelter
Steam:   C:\\Users\\<YOURUSERNAME>\\AppData\\Local\\FalloutShelter

Decrypts binary data read from stdin outputting formatted JSON   to stdout
Encrypts JSON   data read from stdin outputting binary save data to stdout

Produces bitwise identical save data on Decryption->Encryption cycles

Examples:
    python3 savefile.py    < Vault1.sav  > Vault1.json  # Decrypt by default
    python3 savefile.py -e < Vault1.json > Vault1.sav

Constants taken from disassembled game source code:
https://androidrepublic.org/threads/6181
"""


import sys
import base64
import json
import argparse
import collections

import Crypto.Cipher.AES as AES  # PyPI: pip install pycryptodome


# IV is used as both PBKDF2 key salt and AES IV.
# Its value was very likely chosen copying from an old StackOverflow answer:
# https://stackoverflow.com/revisions/10177020/2
IV  = b'tu89geji340t89u2'

# KEY is a precomputed AES key, stored here as a base16-encoded string (ASCII
# hex format), and can be generated using the IV and a hardcoded password:
# PASSWORD = base64.b64encode(b'PlayerData')[:8]  # or simply b'UGxheWVy'
# See previous commits on how to manually generate it
KEY = b'A7CA9F3366D892C2F0BEF417341CA971B69AE9F7BACCCFFCF43C62D1D7D021F9'

CIPHER = AES.new(base64.b16decode(KEY), AES.MODE_CBC, IV)

COPYRIGHT="""
Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
"""


class FSJSONEnc(json.JSONEncoder):
    """Stripped-down JSONEncoder to format floats with trailing zeroes"""
    def iterencode(self, o, _one_shot=False):
        def floatstr(o):
            return '{0:.02f}'.format(o)

        _iterencode = json.encoder._make_iterencode(
            None, self.default, json.encoder.encode_basestring_ascii,
            self.indent, floatstr, self.key_separator, self.item_separator,
            self.sort_keys, self.skipkeys, _one_shot)

        return _iterencode(o, 0)


def decrypt(savedata: str) -> collections.OrderedDict:
    """Decrypt a Fallout Shelter save game data to a Dictionary."""

    # Decode and decrypt the save data
    data = CIPHER.decrypt(base64.b64decode(savedata.encode('ascii')))

    # Remove tailing padding, if any
    # PKCS#7 padding is N bytes of value N, unpadded data is data[:-data[-1]]
    if data[-1] != b'}':
        data = data.rstrip(data[-1:])

    # Deserialize JSON string to Python dict object
    return loadjson(data.decode('ascii'))


def encrypt(obj: dict) -> str:
    """Encrypt a Dictionary to a Fallout Shelter save game data."""

    # Serialize to a one-line JSON byte string
    data = dumpjson(obj).encode('ascii')

    # Add PKCS#7 padding
    pad = 16 - len(data) % 16
    data += pad * bytes((pad,))

    # Encrypt and encode
    return base64.b64encode(CIPHER.encrypt(data)).decode('ascii')


def dumpjson(obj: dict, pretty: bool = False, sort: bool = False) -> str:
    """Wrap json.dumps() using custom float encoder and pretty-print preset"""
    if pretty:
        kwargs= dict(sort_keys=sort, indent=4)
        newline = '\n'
    else:
        kwargs = dict(separators=(',',':'))
        newline = ''

    return json.dumps(obj, cls=FSJSONEnc, **kwargs) + newline


def loadjson(data: str) -> collections.OrderedDict:
    """Wrap json.loads() preserving key order"""
    return json.loads(data, object_pairs_hook=collections.OrderedDict)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--decrypt", action="store_true", default=True,
                       help="Decrypt save data to formatted JSON. [Default]")
    group.add_argument("-e", "--encrypt", action="store_false", dest="decrypt",
                       help="Encrypt JSON to save data.")
    parser.add_argument("-s", "--sort-keys", action="store_true", dest="sort",
                        help="Sort JSON keys on decryption.")
    args = parser.parse_args(argv)

    data = sys.stdin.read()
    if args.decrypt:
        out = dumpjson(decrypt(data), pretty=True, sort=args.sort)
    else:
        out = encrypt(loadjson(data))

    sys.stdout.write(out)




if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except (KeyboardInterrupt, BrokenPipeError):
        pass
