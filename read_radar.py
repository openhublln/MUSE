import socket
import struct
import time
import os
import signal
from utils import *
from datetime import datetime

# Function to print log messages with timestamps
def report(*arg):
    print(f"[{datetime.now()}]", *arg)

# Decorator to ensure a connection is established before calling the function
def requires_connection(func):
    def call(*args, **kwargs):
        if args[0].SOCKET is None:
            report(f"connection required (func='{func.__name__}' aborted)")
            return
        else:
            return func(*args, **kwargs)
    return call

# Class representing a command to be sent/received
class Command:
    def __init__(self, type: str, length: int):
        self.type = type
        self.length = length
        self.timestamp = None

        if length > 0:
            self.buffer = bytearray(length)
            self.memory = memoryview(self.buffer)
        else:
            self.buffer = self.memory = None
    
    def __repr__(self):
        return f"Command<{self.type},{self.length}> [{self.timestamp}]"

# Class to handle radar operations
class Radar:
    def __init__(self, IP='192.168.16.2', PORT=6172, TIMEOUT=3.0):
        self.IP, self.PORT, self.TIMEOUT = IP, PORT, TIMEOUT
        self.SOCKET = None

        self.buffer = bytearray(8)
        self.memory = memoryview(self.buffer)
        
    # Connect to the radar server
    def connect(self):
        try:
            self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.SOCKET.settimeout(self.TIMEOUT)
            self.SOCKET.connect((self.IP, self.PORT))
            report("connection to radar : OK")
        except Exception as e:
            self.SOCKET = None
            report(f"connection to the radar : NOT OK (error : {e})")
    
    # Disconnect from the radar server
    @requires_connection
    def disconnect(self):
        try:
            self.send_message("GBYE")
            time.sleep(1)  # Wait for the radar server to process the GBYE command
            self.SOCKET.close()
            report("disconnection from the radar : OK")
        except Exception as e:
            report(f"disconnection from the radar : NOT OK (error : {e})")
    
    # Send a message to the radar server
    @requires_connection
    def send_message(self, header, payload_length=0, payload=None):
        try:
            if isinstance(payload, str):
                b_payload = payload.encode()
            elif isinstance(payload, (int, float)):
                b_payload = struct.pack("<I", payload)
            else:
                b_payload = b""
                
            self.SOCKET.send(header.encode() + struct.pack("<I", payload_length) + b_payload)
            report(f"sent : <{header},{payload}>")
        except Exception as e:
            report(f"not sent : <{header},{payload}> (error : {e})")
    
    # Initialize transmission with a series of commands
    @requires_connection
    def init_transmission(self):
        for init_command in init_commands:
            self.send_message(*init_command)
            time.sleep(0.05)
        time.sleep(1.2)
    
    # Listen for commands from the radar server
    @requires_connection
    def listening(self):
        start, it = time.time(), 0
        prev_time = int(start)
        while True:
            command = self.receive_command()

    # Receive a command from the radar server
    def receive_command(self):
        nbytes = self.SOCKET.recv_into(self.memory)
        command = Command(bytes(self.buffer[:4]).decode(), struct.unpack("<I", bytes(self.buffer[4:]))[0])
        command.timestamp = time.time()
        
        nbytes = 0
        while nbytes != command.length:
            nbytes += self.SOCKET.recv_into(command.memory[nbytes:])
        
        if nbytes != command.length:
            report(f" not received : {command} (with only {nbytes} bytes)")
        return command

# Radar setup and connection
radar = Radar()
radar.connect()
radar.init_transmission()

# Signal handler for graceful shutdown on CTRL+C
def signal_handler(sig, frame):
    """Handle the SIGINT (Ctrl+C) signal."""
    report("CTRL+C detected, stopping radar server...")
    time.sleep(1)  # Wait for the radar server to process the STOP command
    radar.disconnect()
    report("Shutdown complete")
    exit(0)

# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

# Start listening for commands
try:
    radar.listening()
except Exception as e:
    print("error during function:", e)
    time.sleep(1)  # Wait for the radar server to process the STOP command
    radar.disconnect()
