from pymongo import MongoClient
from signal import signal, SIGINT, SIGTERM
from datetime import datetime, timezone
import gps  # the gpsd interface module

def handler(signal_received, frame):
    print('Closing MongoDB connection')
    client.close()
    session.close()
    exit(0)


if __name__ == '__main__':
    # Connect to MongoDB
    print("Connecting to MongoDB")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['gps']
    collection = db['gps']

    signal(SIGINT, handler)
    signal(SIGTERM, handler)

    session = gps.gps(mode=gps.WATCH_ENABLE)
    while 0 == session.read():
        if not (gps.MODE_SET & session.valid):
            # not useful, probably not a TPV message
            continue

        print("Inserting data to MongoDB")
        # str time to BSON UTC datetime value
        if 'time' in session.data:
            session.data['time'] = datetime.strptime(session.data['time'], "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            session.data['time'] = datetime.now(timezone.utc)
        collection.insert_one(dict(session.data))
