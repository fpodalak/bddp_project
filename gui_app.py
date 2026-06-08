import tkinter as tk
from tkinter import messagebox, simpledialog
import pymongo
import sys

def connect_to_cluster():
    """Checks all nodes, finds the primary, and returns a collection handle to it."""
    primary_port = None
    for port in [27017, 27018, 27019]:
        try:
            c = pymongo.MongoClient(f"mongodb://localhost:{port}/?directConnection=true", serverSelectionTimeoutMS=500)
            info = c.admin.command('isMaster')
            role = "PRIMARY" if info.get('ismaster') else "secondary"
            print(f"Node on port {port}: UP ({role})")
            if info.get('ismaster'):
                primary_port = port
                primary_client = c
        except Exception:
            print(f"Node on port {port}: DOWN")

    if primary_port is None:
        messagebox.showerror("Critical Error", "All database nodes are currently down! Please check Docker.")
        sys.exit()

    print(f"Connected to primary on port {primary_port}.")
    return primary_client["cinema_db"]["seats"]

collection = connect_to_cluster()
seat_labels = {}

def get_collection():
    """Returns the active collection, reconnecting to the current primary if the last node failed."""
    global collection
    try:
        collection.database.client.admin.command('ping')
    except Exception:
        print("Lost connection to node — reconnecting to current primary...")
        collection = connect_to_cluster()
    return collection

def view_seats():
    """Fetches all seats and updates the color and text of the grid blocks."""
    coll = get_collection()
    seats = coll.find().sort("_id", 1)
    
    for seat in seats:
        seat_id = seat["_id"]
        if seat["is_booked"]:
            name = seat["customer_name"]
            short_name = name[:8] + ".." if len(name) > 8 else name
            seat_labels[seat_id].config(bg="#f8d7da", fg="#721c24", text=f"{seat_id}\n{short_name}")
        else:
            seat_labels[seat_id].config(bg="#d4edda", fg="#155724", text=f"{seat_id}\nFree")

def book_seat():
    """Pops up a dialog to book one or multiple seats."""
    seat_input = simpledialog.askstring("Book Seats", "Enter Seat Numbers (e.g., 1, 2, 5):")
    if not seat_input:
        return 
    
    try:
        requested_ids = [int(s.strip()) for s in seat_input.split(",")]
    except ValueError:
        messagebox.showerror("Error", "Invalid format! Please use numbers separated by commas.")
        book_seat() 
        return

    if any(sid < 1 or sid > 70 for sid in requested_ids):
        messagebox.showerror("Error", "Seat numbers must be between 1 and 70.")
        book_seat() 
        return

    name = simpledialog.askstring("Name", "Enter your name for the reservation:")
    if not name:
        return

    result = get_collection().update_many(
        {"_id": {"$in": requested_ids}, "is_booked": False},
        {"$set": {"is_booked": True, "customer_name": name}}
    )

    if result.modified_count == len(requested_ids):
        messagebox.showinfo("Success", f"✅ Seats {', '.join(map(str, requested_ids))} successfully booked for {name}!")
    elif result.modified_count == 0:
        messagebox.showwarning("Seats Taken", "Sorry, all of those seats are already booked!")
    else:
        # Partial success — roll back the seats we did book and ask user to retry
        get_collection().update_many(
            {"_id": {"$in": requested_ids}, "customer_name": name, "is_booked": True},
            {"$set": {"is_booked": False, "customer_name": None}}
        )
        messagebox.showwarning(
            "Booking Failed",
            f"Some seats were taken by another user just now. Booking rolled back — please try again."
        )
    view_seats()

def update_reservation():
    """Pops up a dialog to update an existing reservation."""
    seat_id = simpledialog.askinteger("Update", "Enter ONE Seat Number to update:", minvalue=1, maxvalue=70)
    if not seat_id:
        return
        
    seat = get_collection().find_one({"_id": seat_id})

    if not seat["is_booked"]:
        messagebox.showwarning("Not Booked", "That seat is not booked yet!")
        return
        
    new_name = simpledialog.askstring("New Name", f"Enter the new name for Seat {seat_id}:")
    if new_name:
        get_collection().update_one(
            {"_id": seat_id}, 
            {"$set": {"customer_name": new_name}}
        )
        messagebox.showinfo("Success", f"✅ Reservation updated to {new_name}!")
        view_seats()

def cancel_reservation():
    """Pops up a dialog to cancel one or multiple reservations."""
    seat_input = simpledialog.askstring("Cancel Reservation", "Enter Seat Numbers to cancel (e.g., 1, 2, 5):")
    if not seat_input:
        return 
        
    try:
        requested_ids = [int(s.strip()) for s in seat_input.split(",")]
    except ValueError:
        messagebox.showerror("Error", "Invalid format! Please use numbers separated by commas.")
        cancel_reservation() 
        return
        
    if any(sid < 1 or sid > 70 for sid in requested_ids):
        messagebox.showerror("Error", "Seat numbers must be between 1 and 70.")
        cancel_reservation() 
        return
        
    seats_to_cancel = list(get_collection().find({"_id": {"$in": requested_ids}}))
    not_booked = [str(s["_id"]) for s in seats_to_cancel if not s["is_booked"]]
    
    if not_booked:
        messagebox.showwarning("Not Booked", f"These seats are not currently booked: {', '.join(not_booked)}")
        cancel_reservation() 
        return
        
    confirm = messagebox.askyesno("Confirm Cancellation", f"Are you sure you want to cancel seats: {', '.join(map(str, requested_ids))}?")
    
    if confirm:
        get_collection().update_many(
            {"_id": {"$in": requested_ids}},
            {"$set": {"is_booked": False, "customer_name": None}}
        )
        messagebox.showinfo("Success", f"✅ Reservations for seats {', '.join(map(str, requested_ids))} have been cancelled!")
        view_seats()

root = tk.Tk()
root.title("Distributed Cinema System")
root.geometry("750x750") 
root.configure(bg="#f0f0f0")

title_label = tk.Label(root, text="🎟️ Cinema Box Office", font=("Helvetica", 16, "bold"), bg="#f0f0f0")
title_label.pack(pady=10)

button_frame = tk.Frame(root, bg="#f0f0f0")
button_frame.pack(pady=5)

btn_view = tk.Button(button_frame, text="Refresh Seats", command=view_seats, width=15, bg="#e0e0e0")
btn_view.grid(row=0, column=0, padx=5)

btn_book = tk.Button(button_frame, text="Book Seats", command=book_seat, width=15, bg="#d4edda")
btn_book.grid(row=0, column=1, padx=5)

btn_update = tk.Button(button_frame, text="Update Reservation", command=update_reservation, width=15, bg="#fff3cd")
btn_update.grid(row=0, column=2, padx=5)

btn_cancel = tk.Button(button_frame, text="Cancel", command=cancel_reservation, width=15, bg="#f8d7da")
btn_cancel.grid(row=0, column=3, padx=5)

grid_frame = tk.Frame(root, bg="#333333", padx=5, pady=5)
grid_frame.pack(pady=20)

screen_label = tk.Label(grid_frame, text="S C R E E N", bg="#555555", fg="white", font=("Helvetica", 10, "bold"))
screen_label.grid(row=0, column=0, columnspan=10, sticky="ew", pady=(0, 10))

for i in range(1, 71):
    row = ((i - 1) // 10) + 1
    col = (i - 1) % 10
    
    lbl = tk.Label(grid_frame, text=str(i), width=8, height=3, relief="raised", font=("Helvetica", 8, "bold"))
    lbl.grid(row=row, column=col, padx=2, pady=2)
    
    seat_labels[i] = lbl

view_seats()
root.mainloop()
