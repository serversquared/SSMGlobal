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
def cmd_QUIT(*args, **kwargs):			# Close client connection.
	return {'break': True}

def cmd_MODE(*args, **kwargs):			# Change client mode.
	client_from = args[0].getpeername()
	valid_modes = ('SERVER', 'CLIENT', 'HUMAN')
	if args[4].upper() in valid_modes:
		if args[4].upper() == 'HUMAN':
			args[0].send('Welcome to serversquared Modification Global Backend.\r\n'.encode('ascii'))
		else:
			args[0].send('OK\r\n'.encode('ascii'))
		args[1].put([json.dumps({'event' : 'send_data', 'data' : '(Mode change: {})'.format(args[4].upper()), 'client_from' : client_from})])
		return {'client_mode': args[4].upper()}

def cmd_HELP(*args, **kwargs):			# Return all commands.
	if args[2] == 'HUMAN':
		client_from = args[0].getpeername()
		data = 'Available commands:\r\n'
		args[0].send(data.encode('ascii'))
		for command_name in command_dispatch:
			data = '\t{}\r\n'.format(command_name)
			args[0].send(data.encode('ascii'))
		args[1].put([json.dumps({'event' : 'send_data', 'data' : '(Help message)', 'client_from' : client_from})])

def cmd_HW(*args, **kwargs):			# Return "Hello, world!"
	client_from = args[0].getpeername()
	iters = (len(args) > 4 and args[4]) or 1
	for i in range(int(iters)):
		args[0].send('Hello, world!\r\n'.encode('ascii'))
	args[1].put([json.dumps({'event' : 'send_data', 'data' : '(Hello world message)', 'client_from' : client_from})])
# End command functions.

# Dictionary of command functions.
command_dispatch = {
	'QUIT' : cmd_QUIT,
	'MODE' : cmd_MODE,
	'HELP' : cmd_HELP,
	'HW' : cmd_HW,
}
