import pymongo
import threading
import random
import time

# Connect to the database
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

def aggressive_client(client_name):
    """This client tries to book every single seat in the cinema as fast as possible."""
    client = pymongo.MongoClient(CONNECTION_STRING, serverSelectionTimeoutMS=5000)
    collection = client["cinema_db"]["seats"]
    
    # Create a list of all 70 seats and shuffle it so the clients fight over different ones first
    all_seats = list(range(1, 71))
    random.shuffle(all_seats)
    
    success_count = 0
    
    for seat_id in all_seats:
        # Try to book it immediately! No waiting.
        result = collection.update_one(
            {"_id": seat_id, "is_booked": False}, 
            {"$set": {"is_booked": True, "customer_name": client_name}}
        )
        
        if result.modified_count > 0:
            success_count += 1
            
    print(f"{client_name} finished! They managed to secure {success_count} seats.")

def run_stress_test_3():
    print("\nSTRESS TEST 3: Two aggressive clients trying to buy out the entire cinema...")
    
    # Reset all seats to empty
    client = pymongo.MongoClient(CONNECTION_STRING)
    collection = client["cinema_db"]["seats"]
    collection.update_many({}, {"$set": {"is_booked": False, "customer_name": None}})
    
    start_time = time.time()
    
    # Spin up our 2 aggressive clients
    thread1 = threading.Thread(target=aggressive_client, args=("Client_A",))
    thread2 = threading.Thread(target=aggressive_client, args=("Client_B",))
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
        
    end_time = time.time()
    
    # Verify the final state
    client_a_seats = collection.count_documents({"customer_name": "Client_A"})
    client_b_seats = collection.count_documents({"customer_name": "Client_B"})
    total_booked = collection.count_documents({"is_booked": True})
    
    print("\n--- TEST RESULTS ---")
    print(f"Time taken: {end_time - start_time:.3f} seconds")
    print(f"Client A total seats: {client_a_seats}")
    print(f"Client B total seats: {client_b_seats}")
    print(f"Total seats booked:   {total_booked} (Should be 70)")
    
    if client_a_seats > 0 and client_b_seats > 0 and total_booked == 70:
        print("SUCCESS: Both clients got seats and the cinema is sold out!")
    else:
        print("FAILED: One client took everything or not all seats were booked.")
    print("--------------------\n")

if __name__ == "__main__":
    run_stress_test_3()