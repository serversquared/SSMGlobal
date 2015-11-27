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

name = 'Queue Utils'
version = '1.0.0'
uses_api_version = '1.0.0'
uses_api_base = 1

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
