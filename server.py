import socket
import json

# loads takes JSON
# dumps takes python

local_IP = '127.0.0.1'
local_port = 12345
buffer_size = 1024

server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
server_socket.bind((local_IP, local_port))