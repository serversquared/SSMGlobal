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

def client_thread(client, q, buffer_size, cmd):	# Client thread (one per connected client).
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
				do_break = cmd.command_dispatch[command_args[0]](client, q, *command_args[1:])
				if do_break:			# Terminate the connection if command returns true.
					break
			except KeyError:			# Not a valid command.
				client.send('< {}'.format(data).encode('ascii'))						# Echo back what the client sent us.
				q.put([json.dumps({'event' : 'send_data', 'data' : data, 'client_from' : client_from})])	# Let the server handler process know what we sent.
			except ValueError:			# Probably invalid arguments.
				data = 'ERROR: ValueError\r\n'	# Send the client an error message.
				client.send(data.encode('ascii'))
				q.put([json.dumps({'event' : 'send_data', 'data' : data, 'client_from' : client_from})])	# Let the server handler process know what we sent.
			except BaseException as e:			# Something not so good happened.
				break				# Terminate the client connection to attempt to preserve the server.
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
		q.put([json.dumps({'event' : 'client_disconnect', 'client_from' : client_from})])		# Let the server handler process know that we lost a client.

def server_thread(server, q, buffer_size, timeout_seconds, max_clients, max_clients_per_ip, server_delay, queue_utils, cmd):	# Server thread (handles client connecting).
	try:
		while True:
			connected_clients = queue_utils.get_client_tracker(q, server_delay)
			if type(connected_clients) is int and connected_clients < max_clients:
				client, client_from = server.accept()		# Wait for a client to connect (BLOCKING FUNCTION).
				if queue_utils.get_client_tracker(q, server_delay, client_from) < max_clients_per_ip:
					client.settimeout(timeout_seconds)		# Set the client's timeout.
					thread = multiprocessing.Process(target=client_thread, args=(client, q, buffer_size, cmd))	# Set up a new child process for the client thread.
					q.put([json.dumps({'event' : 'client_connect', 'client_from' : client_from})])		# Let the server handler process know that we gained a client.
					thread.daemon = True				# Daemonize the client thread.
					thread.start()					# Start the client thread.
				else:
					client.shutdown(SHUT_RDWR)		# Immediately terminate the connection.
					client.close()
				time.sleep(0.1)
			else:		# The server is full (or there was an error loading the queue).
				try:
					server.settimeout(0.1)				# Reload the queue 10 times per second.
					client, client_from = server.accept()
					client.shutdown(SHUT_RDWR)		# Immediately terminate the connection.
					client.close()
				except timeout:
					pass
				finally:
					server.settimeout(None)
	except KeyboardInterrupt:
		pass
