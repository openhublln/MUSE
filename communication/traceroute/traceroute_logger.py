import re
from subprocess import run
import argparse
import datetime
from pymongo import MongoClient
from time import sleep
from signal import signal, SIGINT, SIGTERM

def handler(signal_received, frame):
    print('Closing MongoDB connection')
    client.close()
    exit(0)

def prace_route(traceroute_output:str):
    re_hop = re.compile(r'\s*(?P<hop>\d+)\s+(?P<info>.*)')
    re_node = re.compile(r'(?P<name>\S+) \((?P<ip>(\d+.\d+.\d+.\d+)|[0-9a-fA-F:]+)\)')
    hops = []
    for l in traceroute_output.splitlines():
        nodes = []
        hop = re_hop.match(l)
        if hop:
            for n in re_node.finditer(hop.group('info')):
                nodes.append(n.groupdict())
            hops.append({'hop': hop.group('hop'), 'nodes': nodes})
    return hops

def traceroute(destination):
    traceroute = run(['traceroute', destination], capture_output=True, text=True)
    return prace_route(traceroute.stdout)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Traceroute logger')
    parser.add_argument('destination', help='Destination to traceroute')
    parser.add_argument('-i', '--interval', type=int, default=60, help='Interval between traceroutes')
    args = parser.parse_args()

    # Connect to MongoDB
    print("Connecting to MongoDB")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['traceroute']
    collection = db['traceroute']

    signal(SIGINT, handler)
    signal(SIGTERM, handler)

    while 1:
        start = datetime.datetime.now(datetime.timezone.utc)
        hops = traceroute(args.destination)
        end = datetime.datetime.now(datetime.timezone.utc)

        print("Inserting data to MongoDB")
        collection.insert_one({'destination': args.destination, 'start': start, 'end': end, 'hops': hops})
        sleep(args.interval)
