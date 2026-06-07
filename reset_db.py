import pymongo

def find_primary_port():
    """Finds which local port is the current replica set primary."""
    for port in [27017, 27018, 27019]:
        try:
            c = pymongo.MongoClient(f"mongodb://localhost:{port}/?directConnection=true", serverSelectionTimeoutMS=1000)
            if c.admin.command('isMaster').get('ismaster'):
                return port
        except Exception:
            pass
    raise Exception("No primary node found. Is Docker running?")

port = find_primary_port()
print(f"Primary node found on port {port}.")
client = pymongo.MongoClient(f"mongodb://localhost:{port}/?directConnection=true")
collection = client["cinema_db"]["seats"]

print("Clearing old database...")
collection.delete_many({}) 

print("Creating 70 brand new seats...")
new_seats = [{"_id": i, "is_booked": False, "customer_name": None, "version": 1} for i in range(1, 71)]
collection.insert_many(new_seats)

print("Done! You can now run your GUI.")