from pymongo import MongoClient

if __name__ == '__main__':
    client = MongoClient('mongodb://localhost:27017/')
    db = client['gps']
    db.create_collection('gps', timeseries={'timeField': 'time'})
    client.close()