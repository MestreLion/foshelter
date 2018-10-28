#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

    Saved games are Vault*.sav files, located at:

    Android: /Android/data/com.bethsoft.falloutshelter/files
    Windows: C:\\Users\\YOURUSERNAME\\Documents\\My Games\\Fallout Shelter
    Steam:   C:\\Users\\YOURUSERNAME\\AppData\\Local\\FalloutShelter

    Currently reads binary data from stdin and output formatted JSON to stdout

    Usage:
        ./fscrypt3 < Vault1.save > Vault1.json
"""


import sys
import base64
import json

# PyPI: pycrypto, v2.5+ required for PBKDF2 support
import Crypto.Cipher.AES as AES
import Crypto.Protocol.KDF as KDF


# b64decode(): bytes -> bytes both PY2 and PY3
PY3 = sys.version_info[0] >= 3


def fs_decrypt(savedata):
    '''
    Decrypts a Fallout Shelter save game data

    @savedata: binary save game data (str in Python 2, bytes in Python 3)
    @output  : JSON text, one-liner  (str in both Python 2 and 3)

    Constants taken from disassembled game source code:
    https://androidrepublic.org/threads/6181

    IVSALT is used as both PBKDF2 key salt and AES IV.
    Its value was very likely chosen copying from an old SO answer
    https://stackoverflow.com/revisions/10177020/2
    '''

    SALTIV   = b'tu89geji340t89u2'
    PASSWORD = base64.b64encode(b'PlayerData')[:8]  # b'UGxheWVy'
    KEYSIZE  = 32

    # Derive the key from password and salt
    try:
        key = KDF.PBKDF2(PASSWORD, SALTIV, KEYSIZE)
    except AttributeError:
        # pycrypto < v2.5, without PBKDF2, so use a pre-computed key.
        # Could use hashlib.pbkdf2_hmac('sha1', PASSWORD, SALTIV, 1000, KEYSIZE)
        key = (b'\xa7\xca\x9f3f\xd8\x92\xc2\xf0\xbe\xf4\x174\x1c\xa9q'
               b'\xb6\x9a\xe9\xf7\xba\xcc\xcf\xfc\xf4<b\xd1\xd7\xd0!\xf9')

    # Use AES in Block cipher mode with key and IV
    aes = AES.new(key, AES.MODE_CBC, SALTIV)

    # Decode and decrypt the save data
    data = aes.decrypt(base64.b64decode(savedata))

    # Remove trailing padding (N bytes of value N) and convert to string
    if PY3:
        data = data[:-data[-1]].decode('ascii')
    else:
        data = data[:-ord(data[-1])]

    return data


def prettyjson(data):
    obj = json.loads(data, strict=False)
    return json.dumps(obj, sort_keys=True, indent=4, separators=(',',':'))


# Print formatted output
# b64decode() on PY2 and 3 takes bytes on input, so need a binary stdin
print(prettyjson(fs_decrypt((sys.stdin.buffer if PY3 else sys.stdin).read())))
