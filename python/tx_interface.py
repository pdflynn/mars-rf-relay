#!/usr/bin/python3
# Mars RF Relay Transmitter Interface
# Run this script from the command line using the following
# syntax to transmit a file through the channel.
# Usage: tx_interface <filename> <modcod> <chunk_size>
import socket
import struct
import sys
import os
import xmlrpc.client

# ~~~ Static Variables ~~~
FILESINK_SERVER_IP = "127.0.0.1"
FILESINK_SERVER_PORT = 2000
CONTROL_SERVER_IP = "127.0.0.1"
CONTROL_SERVER_PORT = 3000
FILE_EXTENSIONS = {"txt": 0,
                   "jpg": 1,
                   "jpeg": 1,
                   "mp3": 2,
                   "mp4": 3}


# ~~~ Helper Functions ~~~
def set_modcod(ip, port, modcod_id):
    # Sets the modulation and coding scheme to be used by the GNU radio server
    proxy = xmlrpc.client.ServerProxy(f"http://{ip}:{port}")
    proxy.set_encoding(modcod_id)


def set_tcp_mtu(ip, port, mtu):
    proxy = xmlrpc.client.ServerProxy(f"http://{ip}:{port}")
    proxy.set_mtu(mtu)


def read_file(path, chunk_size):
    # Reads a file into a list of frames. Assumes "path" is a valid file path.
    frames = list()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            frames.append(chunk)
            if not chunk:
                break
    return frames


def start_cmd(filename):
    # Return a start command to tell the receiver that a file is starting
    # Format: [1 Byte: "s"] [1 Byte: N] [14 Bytes: File Name]
    # Where "s" signifies a start chunk, N specifies the file type,
    # and there are 14 bytes for a UTF-8 encoded file name.
    # N = {0: .txt, 1: .jpg, 2: .mp3, 3: .mp4}
    # for Commands / Images / Audio / Video
    [name, extension] = filename.split('.')
    print(name, extension)
    if len(name) > 14:
        name = name[0:13]  # Truncate the file name if it's too long
    N = FILE_EXTENSIONS[extension.lower()]
    start_cmd = bytes("s", "utf-8") + N.to_bytes(1, "little") + \
        bytes(name, "utf-8")
    padding_len = 16 - len(start_cmd)
    for i in range(0, padding_len):
        start_cmd += struct.pack("x")  # add padding bytes if filename is short
    return start_cmd


def stop_cmd(total_chunks):
    # Returns a stop command containing the total number of chunks sent.
    # Format: [1 Byte: "f"] [2 Bytes: Total # of Chunks] [1 Byte: "f"]
    # Where "f" signifies final part of the file and the total number
    # of chunks is equal to how many chunks were sent.
    return bytes("f", "utf-8") + struct.pack(">H", total_chunks) + bytes("f", "utf-8")


def send_file(frames):
    # Send frames over TCP to the GNU radio flowgraph
    for i in range(0, len(frames)):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((FILESINK_SERVER_IP, FILESINK_SERVER_PORT))
        print(f"Sending frame {i+1} of {len(frames)}")
        sock.sendto(struct.pack(">H", i) +
                    frames[i], (FILESINK_SERVER_IP, FILESINK_SERVER_PORT))
        sock.close()

    return len(frames)  # So we can send stop command


# ~~~ Parse input arguments ~~~
modcod = 0
chunk_size = 64
filename = None
args = sys.argv
if len(args) > 3:
    chunk_size = int(args[3])
    if chunk_size > 1024 or chunk_size < 32:
        raise Exception("Please specify a frame size between 32 and 1024 bytes")

if len(args) > 2:
    modcod = int(args[2])
    if modcod < 0 or modcod > 7:
        raise Exception("""Invalid MODCOD specified. 
                The following modulation and encoding schemes are supported: 
                \n 0: BPSK 1/2, 1: BPSK 3/4, 2: QPSK 1/2, 3: QPSK 3/4, 4: 16QAM 1/2, 
                 5: 16QAM 3/4, 6: 64QAM 2/3, 7: 64QAM 3/4""")
if len(args) > 1:
    filename = args[1]
    cwd = os.getcwd()
    ftype = filename.split('.')[1]
    if ftype not in ["txt", "jpg", "jpeg", "mp3", "mp4"]:
        raise TypeError(
            "Invalid file type. Please try txt, jpg, jpeg, mp3, mp4.")

if len(args) < 1:
    raise Exception("Please at least specify a file to transmit!")


# ~~~ Send the file! ~~~

# Generate and send the start command 3 times
start = start_cmd(filename)  # First generate a start command
set_modcod(CONTROL_SERVER_IP, CONTROL_SERVER_PORT, 0)  # Set to BPSK 1/2
for i in range(0, 3):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((FILESINK_SERVER_IP, FILESINK_SERVER_PORT))
    sock.sendto(start, (FILESINK_SERVER_IP, FILESINK_SERVER_PORT))
    sock.close()


# Send the actual file data
file_chunks = read_file(filename, chunk_size)
set_modcod(CONTROL_SERVER_IP, CONTROL_SERVER_PORT,
           modcod)  # Set to higher modcod
num_chunks = send_file(file_chunks)


# Generate stop word and send it
stop = stop_cmd(num_chunks)
set_modcod(CONTROL_SERVER_IP, CONTROL_SERVER_PORT, 0)  # Set to BPSK 1/2
for i in range(0, 3):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((FILESINK_SERVER_IP, FILESINK_SERVER_PORT))
    sock.sendto(stop, (FILESINK_SERVER_IP, FILESINK_SERVER_PORT))
    sock.close()

# Flush packet
for i in range(0, 1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((FILESINK_SERVER_IP, FILESINK_SERVER_PORT))
    sock.sendto(str.encode("\n"), (FILESINK_SERVER_IP, FILESINK_SERVER_PORT))
    sock.close()

# Close the TCP port
