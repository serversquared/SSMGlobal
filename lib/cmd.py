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

import json

name = 'Command Pack'
version = '1.0.0'
uses_api_version = '1.0.0'
uses_api_base = 1

# Command functions.
def cmd_quit(*args, **kwargs):			# Close client connection.
	return True

def cmd_help(*args, **kwargs):			# Return all commands.
	client_from = args[0].getpeername()
	data = 'Available commands:\r\n'
	args[0].send(data.encode('ascii'))
	for command_name in command_dispatch:
		data = '\t{}\r\n'.format(command_name)
		args[0].send(data.encode('ascii'))
	args[1].put([json.dumps({'event' : 'send_data', 'data' : '(Help message)', 'client_from' : client_from})])

def cmd_hw(*args, **kwargs):			# Return "Hello, world!"
	client_from = args[0].getpeername()
	iters = (len(args) > 3 and args[3]) or 1
	for i in range(int(iters)):
		args[0].send('Hello, world!\r\n'.encode('ascii'))
	args[1].put([json.dumps({'event' : 'send_data', 'data' : '(Hello world message)', 'client_from' : client_from})])
# End command functions.

# Dictionary of command functions.
command_dispatch = {
	'quit' : cmd_quit,
	'help' : cmd_help,
	'hw' : cmd_hw
}
