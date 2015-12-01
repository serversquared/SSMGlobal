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
import time
import multiprocessing
from socket import timeout, SHUT_RDWR

name = 'Global Backend Network Core'
version = '1.0.0'
uses_api_version = '1.0.0'
uses_api_base = 1

def format_message(client_mode, state, message, extra=None):
	reply = ''
	if client_mode == 'HUMAN':
		if state.upper() == 'ERROR':	reply += 'ERROR: '
		reply += message
	else:
		reply_dict = {}
		if extra:	reply_dict.update(extra)
		reply_dict['state'] = state
		reply_dict['msg'] = message
		reply += json.dumps(reply_dict)
	return reply

def client_thread(client, q, buffer_size, cmd, libs):	# Client thread (one per connected client).
	client_from = client.getpeername()
	client_mode = None
	try:
		while True:
			if client_mode == 'HUMAN':	client.send('> '.encode())

			data = client.recv(buffer_size)
			data = data.decode()
			args = data[:-2].split()
			data_json = None
			try:	data_json = json.loads(data[:-2])
			except ValueError:	pass

			if data == '' or len(args) == 0:	break
			q.put([json.dumps({'event': 'receive_data', 'data': data, 'client_from': client_from})])

			command = None
			command_args = ()
			if not client_mode:
				if args[0].upper() == 'MODE' or (data_json and data_json['cmd'].upper() == 'MODE'):
					command = 'MODE'
					if data_json:	command_args = (data_json['args'].split())
					else:	command_args = args[1:]
				else:
					client.send('{}\r\n'.format(json.dumps({'state': 'ERROR', 'msg': 'No mode set.'})).encode())
					break
			elif client_mode == 'HUMAN':
				command = args[0]
				if len(args) > 1:	command_args = args[1:]
			elif client_mode == 'CLIENT':
				if data_json:
					if 'cmd' in data_json:	command = data_json['cmd']
					if 'args' in data_json:	command_args = data_json['args'].split()
				else:
					client.send('{}\r\n'.format(format_message(client_mode, 'ERROR', 'Invalid JSON.')).encode())
			elif client_mode == 'SERVER':
				pass	# TODO: Server authentication.

			result = None
			if command and command.upper() in cmd.command_dispatch:
				result = cmd.command_dispatch[command.upper()](client, q, client_mode, libs, *command_args)
			elif command:
				client.send('{}\r\n'.format(format_message(client_mode, 'ERROR', 'Command not found.')).encode())
				q.put([json.dumps({'event': 'receive_data', 'data': '(Error: Command not found.)', 'client_from': client_from})])
			if type(result) is dict:
				if 'break' in result and result['break']:	break
				if 'client_mode' in result:	client_mode = result['client_mode']

			'''
			if client_mode == 'HUMAN':
				client.send('> '.encode('ascii'))

			data = client.recv(buffer_size)		# Get client input (BLOCKING FUNCTION).
			data = data.decode('ascii')
			if data == '':				# Data is blank usually when a client's connection is terminated.
				break				# End the loop to close the client object.
			q.put([json.dumps({'event': 'receive_data', 'data': data, 'client_from': client_from})])		# Let the server handler process know what the client sent us.

			try:					# Try to run a command based off of user input.
				result = None
				if client_mode and client_mode != 'HUMAN':
					try:
						data = json.loads(data[:-2])
					except ValueError:
						client.send('{}\r\n'.format(json.dumps({'state': 'ERROR', 'msg': 'Bad JSON string.'})).encode('ascii'))
						q.put([json.dumps({'event': 'send_data', 'data': '(Error: Bad JSON string)', 'client_from': client_from})])
						break
					if 'cmd' in data:
						result = cmd.command_dispatch[data['cmd'].upper()](client, q, client_mode, libs, 'args' in data and data['args'] or ())
				else:
					command_args = data[:-2].split()
					if not client_mode and command_args[0].upper() != 'MODE':
						break

					result = cmd.command_dispatch[command_args[0].upper()](client, q, client_mode, libs, *command_args[1:])
				if type(result) is dict:
					if 'client_mode' in result:
						client_mode = result['client_mode']
					if 'break' in result and result['break']:		# Terminate the connection if command returns true.
						break
			except KeyError:			# Not a valid command.
				if client_mode and client_mode != 'HUMAN':
					client.send('{}\r\n'.format(json.dumps({'state': 'ERROR', 'msg': 'Command not found.'})).encode('ascii'))
				else:
					client.send('Error: Command not found.\r\n'.encode('ascii'))
				q.put([json.dumps({'event': 'send_data', 'data': '(Error: No command found)', 'client_from': client_from})])		# Let the server handler process know what we sent.
			except ValueError:			# Probably invalid arguments.
				if client_mode and client_mode != 'HUMAN':
					client.send('{}\r\n'.format(json.dumps({'state': 'ERROR', 'msg': 'Invalid value.'})).encode('ascii'))
				else:
					client.send('Error: Invalid value.\r\n')
				q.put([json.dumps({'event': 'send_data', 'data': '(Error: Invalid value)', 'client_from': client_from})])	# Let the server handler process know what we sent.
			except BaseException as e:			# Something not so good happened.
				q.put([json.dumps({'event': 'send_data', 'data': '(Error: Unknown error)', 'client_from': client_from})])	# Let the server handler process know what we sent.
				try:
					if client_mode and client_mode != 'HUMAN':
						client.send('{}\r\n'.format(json.dumps({'state': 'ERROR', 'msg': 'Unknown error.'})).encode('ascii'))
					else:
						client.send('Error: Unknown error.\r\n')
				except BaseException:
					pass
				break				# Terminate the client connection to attempt to preserve the server.
			'''
		try:
			client.shutdown(SHUT_RDWR)	# Properly shuts down the connection.
		except BaseException:
			pass
	except BrokenPipeError:			# We lost connection to the client.
		pass
	except timeout:			# The client's timeout has exceeded.
		client.shutdown(SHUT_RDWR)
	except KeyboardInterrupt:
		pass
	finally:
		client.close()			# Close the client object.
		q.put([json.dumps({'event': 'client_disconnect', 'client_from': client_from})])		# Let the server handler process know that we lost a client.

def server_thread(server, q, buffer_size, timeout_seconds, max_clients, max_clients_per_ip, server_delay, queue_utils, cmd, libs):	# Server thread (handles client connecting).
	try:
		while True:
			connected_clients = queue_utils.get_client_tracker(q, server_delay)
			if type(connected_clients) is int and connected_clients < max_clients:
				client, client_from = server.accept()		# Wait for a client to connect (BLOCKING FUNCTION).
				if queue_utils.get_client_tracker(q, server_delay, client_from) < max_clients_per_ip:
					client.settimeout(timeout_seconds)		# Set the client's timeout.
					client.send('{}\r\n'.format(json.dumps({'state': 'OK', 'msg': 'CONNECTED serversquaredGlobal'})).encode())
					thread = multiprocessing.Process(target=client_thread, args=(client, q, buffer_size, cmd, libs))	# Set up a new child process for the client thread.
					q.put([json.dumps({'event': 'client_connect', 'client_from': client_from})])		# Let the server handler process know that we gained a client.
					thread.daemon = True				# Daemonize the client thread.
					thread.start()					# Start the client thread.
				else:
					client.send('ERROR TOO MANY CLIENTS\r\n'.encode())
					client.shutdown(SHUT_RDWR)		# Immediately terminate the connection.
					client.close()
				time.sleep(0.1)
			else:		# The server is full (or there was an error loading the queue).
				try:
					server.settimeout(0.1)				# Reload the queue 10 times per second.
					client, client_from = server.accept()
					client.send('ERROR SERVER FULL\r\n'.encode())
					client.shutdown(SHUT_RDWR)		# Immediately terminate the connection.
					client.close()
				except timeout:
					pass
				finally:
					server.settimeout(None)
	except KeyboardInterrupt:
		pass
