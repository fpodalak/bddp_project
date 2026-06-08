import pymongo
import threading
import random
import time

def find_primary_port():
    for port in [27017, 27018, 27019]:
        try:
            c = pymongo.MongoClient(f"mongodb://localhost:{port}/?directConnection=true", serverSelectionTimeoutMS=1000)
            if c.admin.command('isMaster').get('ismaster'):
                return port
        except Exception:
            pass
    raise Exception("No primary node found.")

CONNECTION_STRING = f"mongodb://localhost:{find_primary_port()}/?directConnection=true"

def random_client_worker(client_id, num_attempts):
    """This function acts as a single user navigating the app."""
    client = pymongo.MongoClient(CONNECTION_STRING, serverSelectionTimeoutMS=5000)
    collection = client["cinema_db"]["seats"]
    success_count = 0
    
    for _ in range(num_attempts):
        seat_id = random.randint(1, 50)
        seat = collection.find_one({"_id": seat_id})

        time.sleep(random.uniform(0.01, 0.05))
        
        if seat and not seat["is_booked"]:.
            result = collection.update_one(
                {"_id": seat_id, "is_booked": False}, 
                {"$set": {"is_booked": True, "customer_name": f"Client_{client_id}"}}
            )
            if result.modified_count > 0:
                success_count += 1
    print(f"Client {client_id} finished browsing. They successfully booked {success_count} seats.")

def run_stress_test_2():
    print("\nSTRESS TEST 2: 5 Clients making random requests simultaneously...")
    client = pymongo.MongoClient(CONNECTION_STRING)
    collection = client["cinema_db"]["seats"]
    collection.update_many({}, {"$set": {"is_booked": False, "customer_name": None}})
    num_clients = 5
    attempts_per_client = 15
    threads = []
    start_time = time.time()
    
    for i in range(1, num_clients + 1):
        t = threading.Thread(target=random_client_worker, args=(i, attempts_per_client))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    end_time = time.time()
    
    total_booked = collection.count_documents({"is_booked": True})
    
    print("\n--- TEST RESULTS ---")
    print(f"Time taken: {end_time - start_time:.3f} seconds")
    print(f"Total seats booked across all 5 clients: {total_booked}")
    print("--------------------\n")

if __name__ == "__main__":
    run_stress_test_2()
