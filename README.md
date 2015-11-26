# SSMGlobal
(server)² Modification Global Backend
  
This server is the official global backend of (server)² Modification.

## Features
* Global player database for records, settings, and more!
* Player registration system.
* Global records database.
* Global server settings database (for optional setting storage and retrieval).
* Inter-server communication system.
* Server status viewer (for connected servers opted in).
* Player mail system (message registered players, offline or on another server).

## Accsesing the Backend
Although the Global Backend is primarily designed to be accessed by the
Modification, it can also be accessed with a Telnet (or similar) client. The
official Global Backend runs at `serversquared.org:53450`.

## How the server operates
The Global Backend has a _minimum_ of 2 processes running at all times:

* The server handler thread, which processes messages (primarily for logs).
* The server thread itself, which handles client connecting.

This improves server speed and efficiency while handling multiple connections.
For each connected client, a child process is spawned exclusively to handle that
client's connection (commands, messages, data, timeouts, etc). This allows many
clients to be connected at one time, each performing tasks at the exact same
time. This works because of the `multiprocessing` library, allowing for
[symmetric multiprocessing](https://en.wikipedia.org/wiki/Symmetric_multiprocessing "Wikipedia article on SMP").

## Found a problem? Want a feature?
If you found a problem or want a feature added, please view the [Issues](https://github.com/serversquared/SSMGlobal/issues)
page on GitHub. Before submitting a new issue, please be **sure** that the issue
does not already exist!

## License
This project is licensed under the GNU Affero General Public License, version 3.
Before using any code from this project, read and agree to its terms. It's a
cool license, I promise! Please note that this is the _Affero_ General Public
License, which means there's special terms for code that runs over a
network (like this project).
  
Copyright (C) 2015 Niko Geil.
