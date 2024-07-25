import socket
import struct
import time
import os
import signal
from utils import *
from datetime import datetime

def report(*arg):
    print(f"[{datetime.now()}]", *arg)

def requires_connection(func):
    def call(*args, **kwargs):
        if args[0].SOCKET is None:
            report(f"connection required (func='{func.__name__}' aborted)")
            return
        else:
            return func(*args, **kwargs)
    return call

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

class Radar:
    def __init__(self, IP='192.168.16.2', PORT=6172, TIMEOUT=3.0):
        self.IP, self.PORT, self.TIMEOUT = IP, PORT, TIMEOUT
        self.SOCKET = None

        self.buffer = bytearray(8)
        self.memory = memoryview(self.buffer)
        
    def connect(self):
        try:
            self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.SOCKET.settimeout(self.TIMEOUT)
            self.SOCKET.connect((self.IP, self.PORT))
            report("connection to radar : OK")
        except Exception as e:
            self.SOCKET = None
            report(f"connection to the radar : NOT OK (error : {e})")
            
    @requires_connection
    def disconnect(self):
        try:
            self.send_message("GBYE")
            time.sleep(1)  # 等待雷達伺服器處理GBYE指令
            self.SOCKET.close()
            report("disconnection from the radar : OK")
        except Exception as e:
            report(f"disconnection from the radar : NOT OK (error : {e})")
    
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
    
    @requires_connection
    def init_transmission(self):
        for init_command in init_commands:
            self.send_message(*init_command)
            time.sleep(0.05)
        time.sleep(1.2)
    
    @requires_connection
    def listening(self):
        start, it = time.time(), 0
        prev_time = int(start)
        while True:
            command = self.receive_command()
            if command.type == "RADC":
                directory = "Data/dev/frames/"
                if not os.path.exists(directory):
                    os.makedirs(directory)
                open(directory + str(command.timestamp) + ".raw", "wb+").write(command.buffer)
                if int(command.timestamp) == prev_time:
                    it += 1
                else:
                    print("n :", it)
                    prev_time = int(command.timestamp)
                    it = 1

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

def signal_handler(sig, frame):
    """Handle the SIGINT (Ctrl+C) signal."""
    report("CTRL+C detected, stopping radar server...")
    time.sleep(1)  # 等待雷達伺服器處理STOP指令
    radar.disconnect()
    report("Shutdown complete")
    exit(0)

# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

try:
    radar.listening()
except Exception as e:
    print("error during function:", e)
    time.sleep(1)  # 等待雷達伺服器處理STOP指令
    radar.disconnect()
