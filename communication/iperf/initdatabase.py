from pymongo import MongoClient

if __name__ == '__main__':
    client = MongoClient('mongodb://localhost:27017/')
    db = client['iperf']
    db.create_collection('iperf', timeseries={'timeField': 'start'})
    client.close()