#!/usr/bin/env python3

import socket
import json
import multiprocessing
import sys
import time
import argparse

default_bound_ip = ''
default_bound_port = 53450
default_buffer_size = 1024
default_timeout = 10

def safe_string(dangerous_string):
	return dangerous_string.replace('\n', '\\n').replace('\r', '\\r').replace('\033', '[ESC]')

def client_thread(client, q, buffer_size):
	client_from = client.getpeername()
	try:
		while True:
			client.send('> '.encode('ascii'))
			data = client.recv(buffer_size)		# BLOCKING FUNCTION!!!
			data = data.decode('ascii')
			q.put([json.dumps({'event' : 'receive_data', 'data' : data, 'client_from' : client_from})])
			client.send('< {}'.format(data).encode('ascii'))
			q.put([json.dumps({'event' : 'send_data', 'data' : data, 'client_from' : client_from})])
			if data[:-2] == 'quit':
				break
		client.shutdown(socket.SHUT_RDWR)
		client.close()
	except BrokenPipeError:
		pass
	except socket.timeout:
		client.shutdown(socket.SHUT_RDWR)
		client.close()
	except KeyboardInterrupt:
		pass
	finally:
		q.put([json.dumps({'event' : 'lostclient', 'client_from' : client_from})])

def server_thread(server, q, buffer_size, timeout_seconds):
	try:
		while True:
			client, client_from = server.accept()		# BLOCKING FUNCTION!!!
			client.settimeout(timeout_seconds)
			thread = multiprocessing.Process(target=client_thread, args=(client, q, buffer_size))
			q.put([json.dumps({'event' : 'newclient', 'client_from' : client_from})])
			thread.daemon = True
			thread.start()
	except KeyboardInterrupt:
		pass

def server_setup(bound_ip, bound_port, buffer_size, timeout_seconds):
	try:
		q = multiprocessing.Queue()
		connected_clients = 0
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		if timeout_seconds < 1:
			timeout_seconds = None
		server.bind((bound_ip, bound_port))
		server.listen(1)
		server_ip, server_port = server.getsockname()
		print('Server started on {}:{}'.format(server_ip, server_port))
		thread = multiprocessing.Process(target=server_thread, args=(server, q, buffer_size, timeout_seconds))
		thread.daemon = False
		thread.start()
		while True:
			while not q.empty():
				item = q.get()
				if type(item) is list and type(item[0]) is str:
					data = json.loads(item[0])
					if data['event'] and data['event'] == 'newclient':
						connected_clients += 1
						print('{}: Connected.'.format(data['client_from'][0]))
					elif data['event'] and data['event'] == 'receive_data':
						print(safe_string('{} -> {}'.format(data['client_from'][0], data['data'])))
					elif data['event'] and data['event'] == 'send_data':
						print(safe_string('{} <- {}'.format(data['client_from'][0], data['data'])))
					elif data['event'] and data['event'] == 'lostclient':
						connected_clients -= 1
						print('{}: Disconnected.'.format(data['client_from'][0]))
			time.sleep(0.02)	# 50 times per second.
	finally:
		server.shutdown(socket.SHUT_RDWR)
		server.close()
		print('\nServer closed.')

def main():
	parser = argparse.ArgumentParser(description='(server)^2 Modification Global Backend')
	parser.add_argument('-a', '--address', type=str, metavar='IP', dest='bound_ip', help='address to bind to', action='store', default=default_bound_ip)
	parser.add_argument('-p', '--port', type=int, metavar='PORT', dest='bound_port', help='port to bind to', action='store', default=default_bound_port)
	parser.add_argument('-b', '--buffer', type=int, metavar='BYTES', dest='buffer_size', help='size of network buffer in bytes', action='store', default=default_buffer_size)
	parser.add_argument('-t', '--timeout', type=int, metavar='SECONDS', dest='timeout_seconds', help='timeout in seconds or 0 to block', action='store', default=default_timeout)
	settings = vars(parser.parse_args())
	server_setup(settings['bound_ip'], settings['bound_port'], settings['buffer_size'], settings['timeout_seconds'])

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print('\nCaught KeyboardInterrupt!')
	finally:
		print('Stopping!')
		sys.exit(0)
