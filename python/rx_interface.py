#!/usr/bin/python3
# Mars RF Relay Receiver interface
# Run this script from the command line using the following syntax before
# launching the receiver GNU radio flowgraph.
# Usage: rx_interface <gr-ip> <gr-port>
import socket
import struct
import sys
import os
import time

from tx_interface import FILE_EXTENSIONS

# ~~~ Static Variables ~~~
GR_FLOWGRAPH_IP = "127.0.0.1"
GR_FLOWGRAPH_PORT = 4000
WAIT_FOR_START = 0
WAIT_FOR_DATA = 1
START_MSG_LEN = 16
STOP_MSG_LEN = 4
FILE_EXTENSIONS = {0: "txt",
                   1: "jpg",
                   2: "mp3",
                   3: "mp4", }


# ~~~ Helper Functions ~~~
def foo():
    pass


# ~~~ Handle Input Arguments ~~~
gr_ip = GR_FLOWGRAPH_IP
gr_port = GR_FLOWGRAPH_PORT
args = sys.argv
if len(args) > 2:
    gr_port = int(args[2])
if len(args) > 1:
    gr_ip = str(args[1])

# ~~~ Start TCP Server ~~~
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((gr_ip, gr_port))
sock.listen(1)

(client, addr) = sock.accept()
print("RX Interface connected to GNU Radio Flowgraph at ", client, addr)
state = WAIT_FOR_START


recv_buf = dict()  # Buffer for received frames (key, value) is (<seq_num>, <data>)
recv_bytes = 0  # A quantity storing how many bytes were received for a file
frame_count = 0  # Keeps track of how many frames received
missing = list()  # A place to store missing sequence numbers
elapsed_millis = 0  # Stores the elapsed time
start_millis = 0  # Stores the time data receiving starts
stop_millis = 0  # Stores the time data receiving stops
curr_filename = ""

while True:
    data = client.recv(1500)

    if state == WAIT_FOR_START:  # State machine is waiting for start message
        # Event: Start Message Detected
        if len(data) == START_MSG_LEN and data[0] == 115:
            # Reset buffers and tracker variables
            recv_buf = dict()
            recv_bytes = 0
            frame_count = 0
            missing = list()
            elapsed_millis = 0
            start_millis = 0
            stop_millis = 0
            curr_filename = ""

            # Set state to waiting for data
            state = WAIT_FOR_DATA

            # Set start time upon detecting first start packet
            start_millis = int(time.time() * 1000)
            file_type = FILE_EXTENSIONS[data[1]]
            curr_filename = str(data[2:]) + file_type

            print(
                f"Detected a start packet for {curr_filename} at {time.localtime(start_millis/1000)}")

    elif state == WAIT_FOR_DATA:  # State machine is waiting for data
        # Ignore any repeated start messages
        if len(data) == START_MSG_LEN and data[0] == 115:
            pass

        # Handle stop messages
        elif len(data) == STOP_MSG_LEN and data[0] == 102 and data[3] == 102:
            # Stop timer to detect how long it took for file transfer
            stop_millis = int(time.time() * 1000)
            elapsed_millis = stop_millis - start_millis

            # Determine if any frames are missing
            expected_frame_count = data[1:2]
            expected_frame_ids = [_ for _ in range(0, expected_frame_count)]
            actual_frame_ids = recv_buf.keys()
            missing_frames = set(expected_frame_ids) - set(actual_frame_ids)
            # TODO: handle replacing these missing frames with 0s in the
            #       output file. Best way would be to add a part of the
            #       stop or start message indicating the frame size.

            # Compute packet error rate
            packet_error_rate = (len(missing_frames) /
                                 expected_frame_count) * 100
            print(
                f"Packet Error Rate (PER) for this transmission: {packet_error_rate}%")

            state = WAIT_FOR_START

        # Handle received data
        else:
            seq_num = data[0:1]  # First 2 bytes are sequence number
            info = data[2:]  # Remaining bytes are actual information
            recv_buf[seq_num] = info
            frame_count += 1
            recv_bytes += len(info)
