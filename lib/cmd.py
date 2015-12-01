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
	if len(args) > 4 and args[4].upper() in valid_modes:
		if args[4].upper() == 'HUMAN':
			args[0].send('Welcome to serversquared Modification Global Backend.\r\n'.encode())
		else:
			args[0].send('{}\r\n'.format(json.dumps({'state': 'OK', 'msg': 'Mode: {}'.format(args[4].upper())})).encode())
		args[1].put([json.dumps({'event' : 'send_data', 'data' : '(Mode change: {})'.format(args[4].upper()), 'client_from' : client_from})])
		return {'client_mode': args[4].upper()}
	elif len(args) > 4 and args[4].upper() == 'LIST':
		args[0].send('{}\r\n'.format(json.dumps({'state': 'OK', 'msg': ' '.join(valid_modes)})).encode())
		args[1].put([json.dumps({'event' : 'send_data', 'data' : '(Mode list)'.format(args[4].upper()), 'client_from' : client_from})])
	else:
		args[0].send('{}\r\n'.format(json.dumps({'state': 'ERROR', 'msg': 'Invalid mode: {}'.format((len(args) > 4  and args[4].upper()) or '')})).encode())
		args[1].put([json.dumps({'event' : 'send_data', 'data' : '(Error: Invalid mode.)', 'client_from' : client_from})])
		return {'break': True}

def cmd_HELP(*args, **kwargs):			# Return all commands.
	client_from = args[0].getpeername()
	if args[2] == 'HUMAN':
		data = 'Available commands:\r\n'
		args[0].send(data.encode())
		for command_name in command_dispatch:
			data = '\t{}\r\n'.format(command_name)
			args[0].send(data.encode())
	else:
		command_list = ' '.join(command_dispatch)
		args[0].send('{}\r\n'.format(json.dumps({'state': 'OK', 'msg': command_list})).encode())
	args[1].put([json.dumps({'event' : 'send_data', 'data' : '(Command list)', 'client_from' : client_from})])

def cmd_HW(*args, **kwargs):			# Return "Hello, world!"
	client_from = args[0].getpeername()
	iters = (len(args) > 4 and args[4]) or 1
	if args[2] == 'HUMAN':
		for i in range(int(iters)):
			if i >= 64:	break
			args[0].send('Hello, world!\r\n'.encode())
	else:
		hw_string = ''
		for i in range(int(iters)):
			if i >= 64:	break
			hw_string += 'Hello, world! '
		hw_string = hw_string[:-1]
		args[0].send('{}\r\n'.format(json.dumps({'state': 'OK', 'msg': hw_string})).encode())
	args[1].put([json.dumps({'event' : 'send_data', 'data' : '(Hello world message)', 'client_from' : client_from})])
# End command functions.

# Dictionary of command functions.
command_dispatch = {
	'QUIT' : cmd_QUIT,
	'MODE' : cmd_MODE,
	'HELP' : cmd_HELP,
	'HW' : cmd_HW,
}
