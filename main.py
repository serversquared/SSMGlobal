#!/usr/bin/env python3

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

import socket
import json
import multiprocessing
import sys
import time
import argparse

# Default server settings. Changeable via command-line options.
default_bound_ip = ''		# IP to bind to (or blank string for all).
default_bound_port = 53450	# Port to bind to (or 0 for random).
default_buffer_size = 1024	# Packet buffer size (power of 2).
default_timeout = 10		# Client timeout in seconds (or 0 to block).
default_max_clients = 32	# Total number of clients allowed.
default_max_clients_per_ip = 4	# Number of clients allowed per IP address.
default_server_delay = 0.02	# Time in seconds to delay various server operations.

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
	iters = (len(args) > 2 and args[2]) or 1
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

def search_queue(q, key):	# Return one matched item from the queue, put the rest back.
	mismatched = []		# List of non-matching items.
	matched = None		# Variable to store a matched item.
	while not q.empty():
		item = q.get()
		if type(item) is list and type(item[0]) is str:
			data = json.loads(item[0])
			try:
				if key in data:
					matched = data
					break
				else:
					mismatched.append(item)
			except KeyError:	# Now unnecessary?
				mismatched.append(item)
	for i in range(len(mismatched)):
		q.put(mismatched[i])
	return matched

def replace_queue_item(q, key, value, server_delay):
	data = search_queue(q, key)
	while not type(data) is dict:
		time.sleep(server_delay)
		data = search_queue(q, key)
	data[key] = value
	q.put([json.dumps(data)])

def get_client_tracker(q, server_delay, peer_name=None):
	data = search_queue(q, 'connected_clients')
	while not type(data) is dict:
		time.sleep(server_delay)
		data = search_queue(q, 'connected_clients')
	q.put([json.dumps(data)])
	if not peer_name:
		return data['connected_clients']
	else:
		if peer_name[0] in data:
			return data[peer_name[0]]
		else:
			return 0

def update_tracked_client(q, peer_name, server_delay, remove=False):
	data = None
	while not type(data) is dict:
		time.sleep(server_delay)
		data = search_queue(q, 'connected_clients')
	if not peer_name[0] in data:
		data[peer_name[0]] = 1
	elif not remove:
		data[peer_name[0]] += 1
	elif remove:
		if data[peer_name[0]] <= 1:
			del data[peer_name[0]]
		else:
			data[peer_name[0]] -= 1
	q.put([json.dumps(data)])

def safe_string(dangerous_string):		# Replace escape sequences.
	return dangerous_string.replace('\n', '\\n').replace('\r', '\\r').replace('\033[', '[CSI]').replace('\033', '[ESC]')

def client_thread(client, q, buffer_size):	# Client thread (one per connected client).
	client_from = client.getpeername()
	try:
		while True:
			client.send('> '.encode('ascii'))	# Encourage user input.
			data = client.recv(buffer_size)		# Get client input (BLOCKING FUNCTION).
			data = data.decode('ascii')
			if data == '':				# Data is blank usually when a client's connection is terminated.
				break				# End the loop to close the client object.
			q.put([json.dumps({'event' : 'receive_data', 'data' : data, 'client_from' : client_from})])		# Let the server handler process know what the client sent us.
			try:					# Try to run a command based off of user input.
				command_args = data[:-2].split()
				do_break = command_dispatch[command_args[0]](client, q, *command_args[1:])
				if do_break:			# Terminate the connection if command returns true.
					break
			except KeyError:			# Not a valid command.
				client.send('< {}'.format(data).encode('ascii'))						# Echo back what the client sent us.
				q.put([json.dumps({'event' : 'send_data', 'data' : data, 'client_from' : client_from})])	# Let the server handler process know what we sent.
			except ValueError:			# Probably invalid arguments.
				data = 'ERROR: ValueError\r\n'	# Send the client an error message.
				client.send(data.encode('ascii'))
				q.put([json.dumps({'event' : 'send_data', 'data' : data, 'client_from' : client_from})])	# Let the server handler process know what we sent.
			except BaseException:			# Something not so good happened.
				break				# Terminate the client connection to attempt to preserve the server.
		try:
			client.shutdown(socket.SHUT_RDWR)	# Properly shuts down the connection.
		except BaseException:
			pass
	except BrokenPipeError:			# We lost connection to the client.
		pass
	except socket.timeout:			# The client's timeout has exceeded.
		client.shutdown(socket.SHUT_RDWR)
	except KeyboardInterrupt:
		pass
	finally:
		client.close()			# Close the client object.
		q.put([json.dumps({'event' : 'client_disconnect', 'client_from' : client_from})])		# Let the server handler process know that we lost a client.

def server_thread(server, q, buffer_size, timeout_seconds, max_clients, max_clients_per_ip, server_delay):	# Server thread (handles client connecting).
	try:
		while True:
			connected_clients = get_client_tracker(q, server_delay)
			if type(connected_clients) is int and connected_clients < max_clients:
				client, client_from = server.accept()		# Wait for a client to connect (BLOCKING FUNCTION).
				if get_client_tracker(q, server_delay, client_from) < max_clients_per_ip:
					client.settimeout(timeout_seconds)		# Set the client's timeout.
					thread = multiprocessing.Process(target=client_thread, args=(client, q, buffer_size))	# Set up a new child process for the client thread.
					q.put([json.dumps({'event' : 'client_connect', 'client_from' : client_from})])		# Let the server handler process know that we gained a client.
					thread.daemon = True				# Daemonize the client thread.
					thread.start()					# Start the client thread.
				else:
					client.shutdown(socket.SHUT_RDWR)		# Immediately terminate the connection.
					client.close()
				time.sleep(0.1)
			else:		# The server is full (or there was an error loading the queue).
				try:
					server.settimeout(0.1)				# Reload the queue 10 times per second.
					client, client_from = server.accept()
					client.shutdown(socket.SHUT_RDWR)		# Immediately terminate the connection.
					client.close()
				except socket.timeout:
					pass
				finally:
					server.settimeout(None)
	except KeyboardInterrupt:
		pass

def server_setup(bound_ip, bound_port, buffer_size, timeout_seconds, max_clients, max_clients_per_ip, server_delay):	# Server handler thread (sets up the server and handles logs).
	try:
		q = multiprocessing.Queue()
		connected_clients = 0
		q.put([json.dumps({'connected_clients' : connected_clients})])
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	# Create a server object.
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	# We want to be able to reuse an old address/port.
		server.settimeout(None)
		if timeout_seconds < 1:						# This would normally do something else, but we're making this mean block.
			timeout_seconds = None
		server.bind((bound_ip, bound_port))				# Bind the server to the specified IP and port.
		server.listen(1)						# Allow up to 1 queued connection.
		server_ip, server_port = server.getsockname()			# Get our own bound IP and port (useful if port was 0).
		print('Server started on {}:{}'.format(server_ip, server_port))
		thread = multiprocessing.Process(target=server_thread, args=(server, q, buffer_size, timeout_seconds, max_clients, max_clients_per_ip, server_delay))	# Set up a child process for the server thread.
		thread.daemon = False						# Do not daemonize the server thread.
		thread.start()							# Start the server thread.
		while True:
			data = search_queue(q, 'event')
			if data:
				if data['event'] == 'client_connect':
					connected_clients += 1		# Track number of connected clients.
					update_tracked_client(q, data['client_from'], server_delay, False)
					print('{}: Connected ({}/{}).'.format(data['client_from'][0], connected_clients, max_clients))
				elif data['event'] == 'receive_data':
					print(safe_string('{} -> {}'.format(data['client_from'][0], data['data'])))
				elif data['event'] == 'send_data':
					print(safe_string('{} <- {}'.format(data['client_from'][0], data['data'])))
				elif data['event'] == 'client_disconnect':
					connected_clients -= 1		# Track number of connected clients.
					update_tracked_client(q, data['client_from'], server_delay, True)
					print('{}: Disconnected ({}/{}).'.format(data['client_from'][0], connected_clients, max_clients, max_clients_per_ip))
			replace_queue_item(q, 'connected_clients', connected_clients, server_delay)
			time.sleep(server_delay)	# Check the queue based on server delay.
	finally:
		server.shutdown(socket.SHUT_RDWR)	# Properly shutdown the server.
		server.close()				# Close the server object.
		print('\nServer closed.')

def main():
	parser = argparse.ArgumentParser(description='(server)^2 Modification Global Backend')
	parser.add_argument('-a', '--address', type=str, metavar='IP', dest='bound_ip', help='address to bind to', action='store', default=default_bound_ip)
	parser.add_argument('-p', '--port', type=int, metavar='PORT', dest='bound_port', help='port to bind to', action='store', default=default_bound_port)
	parser.add_argument('-b', '--buffer', type=int, metavar='BYTES', dest='buffer_size', help='size of network buffer in bytes', action='store', default=default_buffer_size)
	parser.add_argument('-t', '--timeout', type=int, metavar='SECONDS', dest='timeout_seconds', help='timeout in seconds or 0 to block', action='store', default=default_timeout)
	parser.add_argument('-m', '--max-clients', type=int, metavar='CLIENTS', dest='max_clients', help='total number of clients allowed', action='store', default=default_max_clients)
	parser.add_argument('-c', '--clients-per-ip', type=int, metavar='CLIENTS', dest='max_clients_per_ip', help='max number of clients allowed per address', action='store', default=default_max_clients_per_ip)
	parser.add_argument('-D', '--server-delay', type=float, metavar='SECONDS', dest='server_delay', help='time in seconds to delay verious server operations', action='store', default=default_server_delay)
	settings = vars(parser.parse_args())
	server_setup(settings['bound_ip'], settings['bound_port'], settings['buffer_size'], settings['timeout_seconds'], settings['max_clients'], settings['max_clients_per_ip'], settings['server_delay'])

if __name__ == '__main__':		# Prevent child processes from running this.
	try:
		main()
	except KeyboardInterrupt:
		print('\nCaught KeyboardInterrupt!')
	finally:
		print('Stopping!')
		sys.exit(0)
