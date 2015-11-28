'''=========================================================================\\\
||| serversquared Modification Global Backend                               |||
||| Copyright (C) 2015 Niko Geil.                                           |||
|||                                                                         |||
||| This program is free software: you can redistribute it and/or modify it |||
||| under the terms of the GNU Affero General Public License as published   |||
||| by the Free Software Foundation, either version 3 of the License, or    |||
||| (at your option) any later version.                                     |||
|||                                                                         |||
||| This program is distributed in the hope that it will be useful,         |||
||| but WITHOUT ANY WARRANTY; without even the implied warranty of          |||
||| MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           |||
||| GNU Affero General Public License for more details.                     |||
|||                                                                         |||
||| You should have received a copy of the                                  |||
||| GNU Affero General Public License along with this program.              |||
||| If not, see <http://www.gnu.org/licenses/>.                             |||
\\\========================================================================='''

# Trust that hashlib is secure.
import hashlib
import random
import string

name = 'Password Hasher'
version = '1.0.0'
uses_api_version = '1.0.0'
uses_api_base = 1

random.seed()
random.seed(''.join(random.SystemRandom().choice(string.ascii_letters + string.digits + string.punctuation)) for _ in range(64))

# How we hash a password:
# 	1) Generate a random string (salt).
# 	2) Derive a key using PBKDF2.
# 	3) Hash key with SHA-512 (for nice ASCII string storage).

def gen_salt(length, charset='0123456789abcdef'):
	return ''.join(random.SystemRandom().choice(str(charset)) for _ in range(length))

def derive_key(password, salt=None, rounds=12, key=None):
	if not salt:	salt = gen_salt(128)
	if key:		return derive_key(password, salt, rounds)[0] == key

	bytes = hashlib.pbkdf2_hmac('sha512', password.encode('ascii'), salt.encode('ascii'), 2**rounds)
	sha512_obj = hashlib.sha512(bytes)
	digest = sha512_obj.hexdigest()
	return (digest, salt, rounds)
