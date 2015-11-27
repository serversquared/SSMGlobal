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

name = 'Safe String'
version = '1.0.0'
uses_api_version = '1.0.0'
uses_api_base = 1

def safe_string(dangerous_string):		# Replace escape sequences.
	return dangerous_string.replace('\n', '\\n').replace('\r', '\\r').replace('\033[', '[CSI]').replace('\033', '[ESC]')
