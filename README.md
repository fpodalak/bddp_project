# Distributed Cinema Reservation System

## Description
A distributed cinema seat reservation system backed by a **3-node MongoDB Replica Set** running in Docker. The system ensures high availability and prevents double-booking through atomic database operations. It ships with two front-ends — a console menu (`app.py`) and a graphical seat-grid GUI (`gui_app.py`) — and three multithreaded stress tests that demonstrate the system's correctness and throughput under heavy concurrent load.

## Project Structure
```
app.py              – Console-based reservation interface
gui_app.py          – Tkinter GUI seat-grid interface
stress_test_1.py    – Sequential spam test (single seat, many requests)
stress_test_2.py    – Random concurrent load (5 clients, random seats)
stress_test_3.py    – Full buy-out race (2 aggressive clients, all 70 seats)
reset_db.py         – Utility to reset all seats to available
check_node_2.py     – Utility to inspect the state of replica set node 2
docker-compose.yaml – Spins up the 3-node MongoDB replica set
```

## Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker Compose)
* Python 3.8+
* pymongo: `pip install pymongo`

## How to Run

### 1. Start the Database Cluster
```bash
docker-compose up -d
```
Wait ~15 seconds for the replica set (`rs0`) to elect a primary.

### 2. Run the Console Application
```bash
python app.py
```
An interactive menu lets you view all 70 seats, book an available seat, or update an existing reservation. **Note:** `app.py` resets all seats on every startup (useful for demos).

### 3. Run the GUI Application
```bash
python gui_app.py
```
Opens a Tkinter window showing a color-coded 10×7 seat grid. Green = available, Red = booked. Click any seat to book or update it. The GUI automatically reconnects if the current primary fails.

### 4. Run the Stress Tests
```bash
python stress_test_1.py   # Sequential spam – one seat, 100 attempts
python stress_test_2.py   # 5 concurrent clients booking random seats
python stress_test_3.py   # 2 aggressive clients racing to buy all 70 seats
```
All tests print a summary of successes, failures, and elapsed time, and verify that no seat was double-booked.

### 5. Stop the Cluster
```bash
docker-compose down
```

## Key Design Decisions
* **Atomic updates** – every booking uses `update_one({"_id": seat_id, "is_booked": False}, ...)` so only one client can win a race; no application-level locks are needed.
* **Primary-direct connection** – clients locate the current primary at startup so writes always land on the correct node without router overhead.
* **Automatic failover** – the GUI detects a lost connection and re-discovers the new primary, demonstrating replica-set resilience.
