import socket
import time
import os

IP = "127.0.0.1"
PORT = 3000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((IP, PORT))
sock.listen(1)

filename = "received.jpg"

# delete output file if it exists
if os.path.exists(filename):
    os.remove(filename)

(client, addr) = sock.accept()
print("connected to", client, addr)
while True:
    data = client.recv(1500)
    if not data:
        break
    print(data)
    with open(filename, "ab") as f:
        f.write(data)
