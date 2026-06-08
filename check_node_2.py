import pymongo\

PORTS = [27017, 27018, 27019]
print("=== REPLICATION CHECK: Reading each node independently ===\n")

for port in PORTS:
    try:
        client = pymongo.MongoClient(
            f"mongodb://localhost:{port}/?directConnection=true",
            serverSelectionTimeoutMS=1000,
            readPreference="secondary"
        )
        info = client.admin.command("isMaster")
        role = "PRIMARY  " if info.get("ismaster") else "secondary"
        collection = client["cinema_db"]["seats"]
        booked = list(collection.find({"is_booked": True}).sort("_id", 1))

        print(f"  Port {port} [{role}]  —  {len(booked)} booked seat(s)")
        for s in booked:
            print(f"    Seat {s['_id']:>2}: {s['customer_name']}")
        if not booked:
            print("    (no seats booked)")
        print()

    except Exception as e:
        print(f"  Port {port} [DOWN]  —  {e}\n")

print("If all UP nodes show the same bookings, replication is working correctly.")
