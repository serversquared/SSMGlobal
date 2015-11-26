#!/usr/bin/env python3

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
		client.shutdown(socket.SHUT_RDWR)		# Properly shuts down the connection.
	except BrokenPipeError:			# We lost connection to the client.
		pass
	except socket.timeout:			# The client's timeout has exceeded.
		client.shutdown(socket.SHUT_RDWR)
	except KeyboardInterrupt:
		pass
	finally:
		client.close()			# Close the client object.
		q.put([json.dumps({'event' : 'client_disconnect', 'client_from' : client_from})])		# Let the server handler process know that we lost a client.

def server_thread(server, q, buffer_size, timeout_seconds):		# Server thread (handles client connecting).
	try:
		while True:
			client, client_from = server.accept()		# Wait for a client to connect (BLOCKING FUNCTION).
			client.settimeout(timeout_seconds)		# Set the client's timeout.
			thread = multiprocessing.Process(target=client_thread, args=(client, q, buffer_size))	# Set up a new child process for the client thread.
			q.put([json.dumps({'event' : 'client_connect', 'client_from' : client_from})])		# Let the server handler process know that we gained a client.
			thread.daemon = True				# Daemonize the client thread.
			thread.start()					# Start the client thread.
	except KeyboardInterrupt:
		pass

def server_setup(bound_ip, bound_port, buffer_size, timeout_seconds):	# Server handler thread (sets up the server and handles logs).
	try:
		q = multiprocessing.Queue()
		connected_clients = 0
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	# Create a server object.
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	# We want to be able to reuse an old address/port.
		if timeout_seconds < 1:						# This would normally do something else, but we're making this mean block.
			timeout_seconds = None
		server.bind((bound_ip, bound_port))				# Bind the server to the specified IP and port.
		server.listen(1)						# Allow up to 1 queued connection.
		server_ip, server_port = server.getsockname()			# Get our own bound IP and port (useful if port was 0).
		print('Server started on {}:{}'.format(server_ip, server_port))
		thread = multiprocessing.Process(target=server_thread, args=(server, q, buffer_size, timeout_seconds))	# Set up a child process for the server thread.
		thread.daemon = False						# Do not daemonize the server thread.
		thread.start()							# Start the server thread.
		while True:
			while not q.empty():
				item = q.get()					# Get one item at a time.
				if type(item) is list and type(item[0]) is str:	# Probably a JSON string.
					data = json.loads(item[0])
					if data['event'] and data['event'] == 'client_connect':
						connected_clients += 1		# Track number of connected clients.
						print('{}: Connected.'.format(data['client_from'][0]))
					elif data['event'] and data['event'] == 'receive_data':
						print(safe_string('{} -> {}'.format(data['client_from'][0], data['data'])))
					elif data['event'] and data['event'] == 'send_data':
						print(safe_string('{} <- {}'.format(data['client_from'][0], data['data'])))
					elif data['event'] and data['event'] == 'client_disconnect':
						connected_clients -= 1		# Track number of connected clients.
						print('{}: Disconnected.'.format(data['client_from'][0]))
			time.sleep(0.02)	# Check the queue 50 times per second.
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
	settings = vars(parser.parse_args())
	server_setup(settings['bound_ip'], settings['bound_port'], settings['buffer_size'], settings['timeout_seconds'])

if __name__ == '__main__':		# Prevent child processes from running this.
	try:
		main()
	except KeyboardInterrupt:
		print('\nCaught KeyboardInterrupt!')
	finally:
		print('Stopping!')
		sys.exit(0)
