from subprocess import run
import argparse
import datetime
from pymongo import MongoClient
from time import sleep
from signal import signal, SIGINT, SIGTERM
from json import loads

def handler(signal_received, frame):
    print('Closing MongoDB connection')
    client.close()
    exit(0)

def iperf(server, duration=10, bitrate='1M'):
    iperf = run(['iperf3', '-c', server, '-t', str(duration), '-Z', '-u', '-b', bitrate, '-J'], capture_output=True, text=True)
    iperf_result = loads(iperf.stdout)
    return iperf_result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Iperf logger')
    parser.add_argument('server', help='Iperf server')
    parser.add_argument('-i', '--interval', type=int, default=60, help='Interval between iperf tests')
    args = parser.parse_args()

    # Connect to MongoDB
    print("Connecting to MongoDB")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['iperf']
    collection = db['iperf']

    signal(SIGINT, handler)
    signal(SIGTERM, handler)

    # bitrates = ['464k', '739k', '1124k'] 
    bitrates = ['386k', '635k', '1020k'] 

    i = 0
    while 1:
        start = datetime.datetime.now(datetime.timezone.utc)
        iperf_result = iperf(args.server, duration=30, bitrate=bitrates[i])
        end = datetime.datetime.now(datetime.timezone.utc)

        print("Inserting data to MongoDB")
        collection.insert_one({'server': args.server, 'start': start, 'end': end, 'bitrate':bitrates[i], 'result': iperf_result})
        sleep(args.interval)
        i = (i + 1) % len(bitrates)
