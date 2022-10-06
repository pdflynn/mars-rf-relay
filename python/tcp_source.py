import socket
import time
import random

IP = "127.0.0.1"
PORT = 2000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((IP, PORT))

filename = "mars.jpeg"

messages = list()
with open(filename, "rb") as f:
    # message = str.encode("Greetings!")
    # messages = f.readlines()
    while True:
        chunk = f.read(64)  # read 64 bytes
        messages.append(chunk)
        if not chunk:
            break

# while True:
try:
    for message in messages:
        # delay = 0.1  # * random.random()  # wait random amount of time
        print("Sending", message)
        sock.sendto(message, (IP, PORT))
        time.sleep(1e-4)
    # sock.sendto(str.encode("\n"), (IP, PORT))
    # sock.sendto(str.encode("\n"), (IP, PORT))

except Exception as e:
    print(e)
    print("error!")
    sock.close()
    # break
finally:
    print("closing socket")
    sock.close()
    time.sleep(1)
