from pymongo import MongoClient

if __name__ == '__main__':
    client = MongoClient('mongodb://localhost:27017/')
    db = client['RM500U']
    db.create_collection('signal_strength', timeseries={'timeField': 'time'})
    db.create_collection('serving_cell', timeseries={'timeField': 'time'})
    db.create_collection('temperatures', timeseries={'timeField': 'time'})
    db.create_collection('data_counter', timeseries={'timeField': 'time'})
    db.create_collection('usbnet_ethernet_status', timeseries={'timeField': 'time'})
    client.close()