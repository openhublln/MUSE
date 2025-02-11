from pymongo import MongoClient

if __name__ == '__main__':
    client = MongoClient('mongodb://localhost:27017/')
    db = client['traceroute']
    db.create_collection('traceroute', timeseries={'timeField': 'start'})
    client.close()