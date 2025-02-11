from pymongo import MongoClient


def clean_rm500u_db(client):
    db = client["RM500U"]
    db["signal_strength"].delete_many({})
    db["serving_cell"].delete_many({})
    db["temperatures"].delete_many({})
    db["data_counter"].delete_many({})
    db["usbnet_ethernet_status"].delete_many({})


def clean_iperf_db(client):
    db = client["iperf"]
    db["iperf"].delete_many({})


def clean_traceroute_db(client):
    db = client["traceroute"]
    db["traceroute"].delete_many({})


def clean_gps_db(client):
    db = client["gps"]
    db["gps"].delete_many({})


if __name__ == "__main__":
    print("Are you sure you want to clean the database? (yes/no)")
    answer = input()
    if answer != "yes":
        exit(0)

    client = MongoClient("mongodb://localhost:27017/")
    clean_rm500u_db(client)
    clean_iperf_db(client)
    clean_traceroute_db(client)
    clean_gps_db(client)
    client.close()