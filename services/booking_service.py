from database.db_connection import MongoDBConnection
from models.booking import Booking
from datetime import datetime
import threading

class BookingService:
    def __init__(self):
        self.db = MongoDBConnection().database
        self.lock = threading.Lock()

    def fetch_available_halls(self, start_time, end_time):
        bookings = self.db.bookings.find({
            "$or": [
                {"start_time": {"$lte": end_time, "$gte": start_time}},
                {"end_time": {"$lte": end_time, "$gte": start_time}}
            ]
        })
        booked_halls = [booking['hall_id'] for booking in bookings]
        all_halls = ['A', 'B', 'C', 'D', 'E', 'F']
        available_halls = [hall for hall in all_halls if hall not in booked_halls]
        return available_halls

    def book_hall(self, hall_id, start_time, end_time):
        with self.lock:
            if hall_id in self.fetch_available_halls(start_time, end_time):
                booking = Booking(hall_id, start_time, end_time)
                result = self.db.bookings.insert_one(booking.__dict__)
                booking.set_booking_id(result.inserted_id)
                self.db.bookings.update_one({'_id': result.inserted_id}, {'$set': {'booking_id': booking.booking_id}})
                return "Booking successful"
            else:
                return "Hall is already booked for the given time slot"
            
    def book_multiple_halls(self, bookings):
        results = []
        for booking in bookings:
            hall_id = booking['hall_id']
            start_time = booking['start_time']
            end_time = booking['end_time']
            result = self.book_hall(hall_id, start_time, end_time)
            results.append({ "hall_id": hall_id, "result": result })
        return results
    
    # to be deleted
    # def fetch_alll_booked_halls(self,start_time, end_time):
    #     bookings = self.db.bookings.find({
    #         "$and": [
    #             {"start_time": {"$lte": end_time}},
    #             {"end_time": {"$gte": start_time}}
    #         ]
    #     })
    #     print("hello")
    #     for hall in bookings:
    #         print(hall)
    #     return bookings

    
    
    def fetch_all_booked_halls(self, start_date, end_date):

        try:
            # print("w0")
            # start_date_obj = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S')
            start_date_obj = start_date+"T00:00:00"
            end_date_obj = end_date+"T23:59:59"
            # print("w1")
            # end_date_obj = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
            bookings = self.db.bookings.find({
                "$and": [
                {"start_time": {"$lte": end_date_obj}},
                {"end_time": {"$gte": start_date_obj}}
                ]
                # "$or": [
                #     {"start_time": {"$lte": start_date_obj}, "end_time": {"$gte": start_date_obj}},
                #     {"start_time": {"$lte": end_date_obj}, "end_time": {"$gte": end_date_obj}}
                # ]
            })
            # print(len(bookings))
            booked_records = []
            for booking in bookings:
                booked_records.append({
                    "booking_id": booking["booking_id"],
                    "hall_id": booking["hall_id"],
                    "start_time": booking["start_time"],
                    "end_time": booking["end_time"],
                })
            print("showing records...")
            # print(booked_records)
            for record in booked_records:
                print(record)
            return booked_records
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def cancel_booking(self, data):
        with self.lock:
            result = self.db.bookings.delete_one({'booking_id': data["booking_id"]})
            if result.deleted_count > 0:
                return f"Booking with ID {data["booking_id"]} has been canceled successfully."
            else:
                return f"Booking with ID {data["booking_id"]} not found."


    def update_booking(self, short_booking_id, new_start_time, new_end_time):
        with self.lock:
            booking = self.db.bookings.find_one({'booking_id': short_booking_id})
            if not booking:
                return f"Booking with ID {short_booking_id} not found."

            hall_id = booking['hall_id']
            # Check if the new time slot is available
            if hall_id in self.fetch_available_halls(new_start_time, new_end_time):
                result = self.db.bookings.update_one(
                    {'booking_id': short_booking_id},
                    {'$set': {'start_time': new_start_time, 'end_time': new_end_time}}
                )
                if result.modified_count > 0:
                    return f"Booking with ID {short_booking_id} has been updated successfully."
                else:
                    return f"Failed to update booking with ID {short_booking_id}."
            else:
                return "The new time slot is not available for the selected hall."