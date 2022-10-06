#!/usr/bin/python3
# Mars RF Relay Transmitter Interface
# Run this script from the command line using the following
# syntax to transmit a file through the channel.
# Usage: tx_interface <filename> <modcod> <frame_size>
import socket
import time
import sys
from os.path import exists

# Static Variables
FILESINK_SERVER_IP = "127.0.0.1"
FILESINK_SERVER_PORT = 2000
CONTROL_SERVER_IP = "127.0.0.1"
CONTROL_SERVER_PORT = 3000

# Helper Functions


def set_modcod(ip, port, modcod_id):
    # Sets the modulation and coding scheme to be used by the GNU radio server
    control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_sock.connect((ip, port))
    control_sock.sendto(str.encode(f"(encoding, {modcod_id})"), (ip, port))
    control_sock.close()


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


def send_file(ip, port, frames):
    # TODO: send start word with BPSK 1/2 3 times
    # Send frames over TCP to the GNU radio flowgraph
    file_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    file_sock.connect((ip, port))
    # TODO: set the MTU so the flowgraph handles frames individually
    for i in range(0, len(frames)):
        print(f"Sending frame {i} of {len(frames)}")
        file_sock.sendto(frames(i), (ip, port))
    # TODO: send stop word with BPSK 1/2 3 times
    file_sock.close()


# Parse input arguments
modcod = 0
frame_size = 64
filename = None
args = sys.argv
if len(args) > 3:
    frame_size = args[3]
    if frame_size > 512 or frame_size < 4:
        raise Exception("Please specify a frame size between 4 and 512 bytes")

if len(args) > 2:
    modcod = args[2]
    if modcod < 0 or modcod > 7:
        raise Exception("""Invalid MODCOD specified. 
                The following modulation and encoding schemes are supported: 
                \n 0: BPSK 1/2, 1: BPSK 3/4, 2: QPSK 1/2, 3: QPSK 3/4, 4: 16QAM 1/2, 
                 5: 16QAM 3/4, 6: 64QAM 2/3, 7: 64QAM 3/4""")
if len(args) > 1:
    filename = args[1]
    if ~exists(filename):
        raise FileNotFoundError(
            "The specified file does not exist. Please try again.")

if len(args) < 1:
    raise Exception("Please at least specify a file to transmit!")
