import pymongo
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
client = pymongo.MongoClient(CONNECTION_STRING, serverSelectionTimeoutMS=5000)
collection = client["cinema_db"]["seats"]

def run_stress_test_1(seat_id_to_spam, number_of_requests):
    print(f"\nSTRESS TEST 1: Spamming {number_of_requests} booking requests for Seat {seat_id_to_spam}...")
    
    # First, let's make sure the seat is empty before we start
    collection.update_one({"_id": seat_id_to_spam}, {"$set": {"is_booked": False, "customer_name": None}})
    
    success_count = 0
    fail_count = 0
    
    # Start a timer
    start_time = time.time()

    # Fire off the requests as fast as the loop can run
    for i in range(number_of_requests):
        # Atomic update: only books the seat if it is STILL free at the moment of writing
        result = collection.update_one(
            {"_id": seat_id_to_spam, "is_booked": False},
            {"$set": {"is_booked": True, "customer_name": f"SpamBot_Attempt_{i}"}}
        )
        if result.modified_count == 1:
            success_count += 1
        else:
            fail_count += 1

    # Stop the timer
    end_time = time.time()
    
    print("\n--- TEST RESULTS ---")
    print(f"Time taken: {end_time - start_time:.3f} seconds")
    print(f"Successful bookings: {success_count} (This should be exactly 1)")
    print(f"Rejected attempts:   {fail_count} (This should be {number_of_requests - 1})")
    
    # Verify who actually got the seat
    final_seat = collection.find_one({"_id": seat_id_to_spam})
    print(f"Final Owner of Seat: {final_seat['customer_name']}")
    print("--------------------\n")

if __name__ == "__main__":
    # Let's try to book Seat #10 exactly 1,000 times in a row
    run_stress_test_1(seat_id_to_spam=10, number_of_requests=1000)
