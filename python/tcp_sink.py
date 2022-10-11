import socket
import time
import os

IP = "127.0.0.1"
PORT = 4000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((IP, PORT))
sock.listen(1)

# filename = "received.jpg"

# # delete output file if it exists
# if os.path.exists(filename):
#     os.remove(filename)

(client, addr) = sock.accept()
print("connected to", client, addr)
data_packets = 0
tot_datasize = 0
while True:
    data = client.recv(1500)
    if len(data) == 16 and data[0] == 115: # corresponds to utf-8 "s"
        print("Received Start Packet")
    elif len(data) == 4 and data[0] == 102: # "f" utf-8
        print("Received Stop Packet")
    else:
        data_packets += 1
        print(f"Received packet of size {len(data)} [{data_packets} total] - {data[0]}")
        tot_datasize += len(data)
        print(f"Total Data Bytes Received: {tot_datasize}")
    if not data:
        break





    # print(len(data))
    # print(data, "\n")
    
    # with open(filename, "ab") as f:
    #     f.write(data)
