#!/usr/bin/env python3
#
#    Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. See <http://www.gnu.org/licenses/gpl.html>


"""
Fallout Shelter save game encryptor and decryptor

Saved games are Vault*.sav files, generally located at:

Android: /Android/data/com.bethsoft.falloutshelter/files
Windows: C:\\Users\\<YOURUSERNAME>\\Documents\\My Games\\Fallout Shelter
Steam:   C:\\Users\\<YOURUSERNAME>\\AppData\\Local\\FalloutShelter

Decrypts binary data read from stdin outputting formatted JSON   to stdout
Encrypts JSON   data read from stdin outputting binary save data to stdout

Examples:
    python3 fscrypt.py    < Vault1.sav  > Vault1.json  # Decrypt by default
    python3 fscrypt.py -e < Vault1.json > Vault1.sav

Constants taken from disassembled game source code:
https://androidrepublic.org/threads/6181
"""


import sys
import base64
import json
import argparse

import Crypto.Cipher.AES as AES  # PyPI: pip install pycrypto


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


def decrypt(savedata: str) -> dict:
    """Decrypt a Fallout Shelter save game data to a Dictionary."""

    # Decode and decrypt the save data
    data = CIPHER.decrypt(base64.b64decode(savedata.encode('ascii')))

    # Remove PKCS#7 trailing padding (N bytes of value N)
    data = data[:-data[-1]]

    # Deserialize JSON string to Python dict object
    return json.loads(data.decode('ascii'))


def encrypt(obj: dict) -> str:
    """Encrypt a Dictionary to a Fallout Shelter save game data."""

    # Serialize to a one-line JSON byte string
    data = json.dumps(obj).encode('ascii')

    # Add PKCS#7 padding
    pad = 16 - len(data) % 16
    data += pad * bytes((pad,))

    # Encrypt and encode
    return base64.b64encode(CIPHER.encrypt(data)).decode('ascii')


def prettyjson(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, indent=4, separators=(',',':')) + '\n'




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--decrypt", action="store_true", default=True,
                        help="Decrypt save data to formatted JSON [Default]")
    group.add_argument("-e", "--encrypt", dest='decrypt', action="store_false",
                        help="Encrypt JSON to save data")
    args = parser.parse_args()

    data = sys.stdin.read()
    if args.decrypt:
        out = prettyjson(decrypt(data))
    else:
        out = encrypt(json.loads(data))

    sys.stdout.write(out)
