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
default_auto_save_delay = 300	# How often in seconds to auto-save (or 0 for never).

# Custom libraries.
import lib.cmd as cmd
import lib.queue_utils as queue_utils
import lib.safe_string as safe_string
import lib.network_core as network_core
libs = [
	cmd,
	queue_utils,
	safe_string,
	network_core,
]
# Extensions (to be checked; primarily extends commands).
extensions = (
)

core = {
	'version': '1.0.0',
	'api_version': '1.0.0',
	'api_base': 1,
}

def lib_check(libs, core):
	mismatched = []
	incompatible = []
	for lib in libs:
		if lib.uses_api_version != core['api_version']:
			mismatched.append(lib)
		if lib.uses_api_base != core['api_base']:
			incompatible.append(lib)
	return mismatched, incompatible

def save_server():
	pass

def server_handler(bound_ip, bound_port, buffer_size, timeout_seconds, max_clients, max_clients_per_ip, server_delay, auto_save_delay, extensions):	# Server handler thread (sets up the server and handles logs).
	try:
		q = multiprocessing.Queue()
		connected_clients = 0
		q.put([json.dumps({'connected_clients' : connected_clients})])
		last_auto_save = time.time()
		auto_save = auto_save_delay > 0
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	# Create a server object.
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	# We want to be able to reuse an old address/port.
		server.settimeout(None)
		if timeout_seconds < 1:						# This would normally do something else, but we're making this mean block.
			timeout_seconds = None
		server.bind((bound_ip, bound_port))				# Bind the server to the specified IP and port.
		server.listen(1)						# Allow up to 1 queued connection.
		server_ip, server_port = server.getsockname()			# Get our own bound IP and port (useful if port was 0).
		print('Server started on {}:{}'.format(server_ip, server_port))
		thread = multiprocessing.Process(target=network_core.server_thread, args=(server, q, buffer_size, timeout_seconds, max_clients, max_clients_per_ip, server_delay, queue_utils, cmd, extensions))	# Set up a child process for the server thread.
		thread.daemon = False						# Do not daemonize the server thread.
		thread.start()							# Start the server thread.
		while True:
			if auto_save and int(time.time() - last_auto_save) >= auto_save_delay:
				save_server()
				last_auto_save = time.time()

			data = queue_utils.search_queue(q, 'event')
			if data:
				if data['event'] == 'client_connect':
					connected_clients += 1		# Track number of connected clients.
					queue_utils.update_tracked_client(q, data['client_from'], server_delay, False)
					print('{}: Connected ({}/{}).'.format(data['client_from'][0], connected_clients, max_clients))
				elif data['event'] == 'receive_data':
					print(safe_string.safe_string('{} -> {}'.format(data['client_from'][0], data['data'])))
				elif data['event'] == 'send_data':
					print(safe_string.safe_string('{} <- {}'.format(data['client_from'][0], data['data'])))
				elif data['event'] == 'client_disconnect':
					connected_clients -= 1		# Track number of connected clients.
					queue_utils.update_tracked_client(q, data['client_from'], server_delay, True)
					print('{}: Disconnected ({}/{}).'.format(data['client_from'][0], connected_clients, max_clients, max_clients_per_ip))
			queue_utils.replace_queue_item(q, 'connected_clients', connected_clients, server_delay)
			time.sleep(server_delay)	# Check the queue based on server delay.
	finally:
		server.shutdown(socket.SHUT_RDWR)	# Properly shutdown the server.
		server.close()				# Close the server object.
		print('\nServer closed.')

def main():
	mismatched, incompatible = lib_check(libs, core)
	if len(mismatched) > 0:
		print('WARN: Mismatched library API loaded.')
		for lib in mismatched:
			print('\tName: {}\tAPI: {}'.format(lib.name, lib.uses_api_version))
	if len(incompatible) > 0:
		print('FATAL: Incompatible library loaded!')
		for lib in incompatible:
			print('\tName: {}\tAPI: {}'.format(lib.name, lib.uses_api_version))
		return
	mismatched, incompatible = lib_check(extensions, core)
	if len(mismatched) > 0:
		print('WARN: Mismatched extension API loaded.')
		for lib in mismatched:
			print('\tName: {}\tAPI: {}'.format(lib.name, lib.uses_api_version))
	if len(incompatible) > 0:
		print('WARN: Incompatible extension loaded!')
		for lib in incompatible:
			print('\tName: {}\tAPI: {}'.format(lib.name, lib.uses_api_version))
	parser = argparse.ArgumentParser(description='(server)^2 Modification Global Backend')
	parser.add_argument('-a', '--address', type=str, metavar='IP', dest='bound_ip', help='address to bind to', action='store', default=default_bound_ip)
	parser.add_argument('-p', '--port', type=int, metavar='PORT', dest='bound_port', help='port to bind to', action='store', default=default_bound_port)
	parser.add_argument('-b', '--buffer', type=int, metavar='BYTES', dest='buffer_size', help='size of network buffer in bytes', action='store', default=default_buffer_size)
	parser.add_argument('-t', '--timeout', type=int, metavar='SECONDS', dest='timeout_seconds', help='timeout in seconds or 0 to block', action='store', default=default_timeout)
	parser.add_argument('-m', '--max-clients', type=int, metavar='CLIENTS', dest='max_clients', help='total number of clients allowed', action='store', default=default_max_clients)
	parser.add_argument('-c', '--clients-per-ip', type=int, metavar='CLIENTS', dest='max_clients_per_ip', help='max number of clients allowed per address', action='store', default=default_max_clients_per_ip)
	parser.add_argument('-D', '--server-delay', type=float, metavar='SECONDS', dest='server_delay', help='time in seconds to delay verious server operations', action='store', default=default_server_delay)
	parser.add_argument('-A', '--auto-save', type=int, metavar='SECONDS', dest='auto_save_delay', help='how often to auto-save in seconds', action='store', default=default_auto_save_delay)
	settings = vars(parser.parse_args())
	server_handler(settings['bound_ip'], settings['bound_port'], settings['buffer_size'], settings['timeout_seconds'], settings['max_clients'], settings['max_clients_per_ip'], settings['server_delay'], settings['auto_save_delay'], extensions)

if __name__ == '__main__':		# Prevent child processes from running this.
	try:
		main()
	except KeyboardInterrupt:
		print('\nCaught KeyboardInterrupt!')
	finally:
		print('Stopping!')
		sys.exit(0)
