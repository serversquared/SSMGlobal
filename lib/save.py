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

name = 'Global Backend Storage'
version = '1.0.0'
uses_api_version = '1.0.0'
uses_api_base = 1

from os.path import isfile as isfile
from time import time
import pickle

def write_save(global_dict, save_file, human_readable=False, pretty=True):
	global_dict['last_save'] = int(time())
	if not human_readable:
		with open(save_file, 'wb') as f:
			pickle.dump(global_dict, f)
	else:
		if pretty:
			human_string = ''
			indent_level = 0
			last_char = None
			for char in str(global_dict):
				if char == '{' or char == '[' or char == '(':
					human_string += char
					indent_level += 1
					human_string += '\n'
					for _ in range(indent_level):	human_string += '\t'
				elif char == '}' or char == ']' or char == ')':
					indent_level -= 1
					human_string += '\n'
					for _ in range(indent_level):	human_string += '\t'
					human_string += char
				elif char == ',':
					human_string += char
					human_string += '\n'
					for _ in range(indent_level):	human_string += '\t'
				elif char == ' ' and last_char == ',':
					pass
				else:
					human_string += char
				last_char = char
			with open(save_file, 'w') as f:
				f.write(human_string)
		else:
			with open(save_file, 'w') as f:
				f.write(str(global_dict))

def load_save(save_file, human_readable=False):
	global_dict = {}
	if not isfile(save_file):
		write_save(global_dict, save_file, human_readable)
	else:
		if not human_readable:
			with open(save_file, 'rb') as f:
				global_dict = pickle.load(f)
		else:
			with open(save_file, 'r') as f:
				global_dict = eval(f.read())
	return global_dict
