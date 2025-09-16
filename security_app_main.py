# security_app_main.py

import os
import cv2
import time
import requests
import qrcode
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
PARKING_LOT_ID = os.getenv("PARKING_LOT_ID")
PLATE_RECOGNIZER_TOKEN = os.getenv("PLATE_RECOGNIZER_TOKEN")

# If .env loading failed, set them manually
if not SUPABASE_URL:
    SUPABASE_URL = "https://ukyfzkeyficphxzkdzwf.supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVreWZ6a2V5ZmljcGh4emtkendmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mjg2Mjg0MiwiZXhwIjoyMDY4NDM4ODQyfQ.I0Q1f8gzowMQeD-aPSE3xfmkxPMCx8K1_YrS778-Lik"
if not PLATE_RECOGNIZER_TOKEN:
    PLATE_RECOGNIZER_TOKEN = "e271442317f75fad8e72ab8c4f0c6e0590cc8d0c"
if not PARKING_LOT_ID:
    PARKING_LOT_ID = "1"

if not all([SUPABASE_URL, SUPABASE_KEY, PARKING_LOT_ID, PLATE_RECOGNIZER_TOKEN]):
    print("❌ Missing keys in .env file")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def capture_plate_image():
    cam = cv2.VideoCapture(0)
    cv2.namedWindow("Press SPACE to capture number plate")

    img_name = "captured_plate.jpg"
    while True:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame from camera.")
            break
        cv2.imshow("Press SPACE to capture number plate", frame)

        k = cv2.waitKey(1)
        if k%256 == 27:
            print("ESC pressed. Exiting camera.")
            break
        elif k%256 == 32:
            cv2.imwrite(img_name, frame)
            print(f"✅ Image captured: {img_name}")
            break

    cam.release()
    cv2.destroyAllWindows()
    return img_name

def recognize_plate(image_path):
    url = "https://api.platerecognizer.com/v1/plate-reader/"
    with open(image_path, 'rb') as image_file:
        response = requests.post(
            url,
            files={"upload": image_file},
            headers={"Authorization": f"Token {PLATE_RECOGNIZER_TOKEN}"}
        )

    if response.status_code in [200, 201]:
        results = response.json().get("results")
        if results:
            plate = results[0]["plate"].upper()
            print(f"✅ Plate detected: {plate}")
            return plate
        else:
            print("❌ Plate not recognized.")
            return None
    else:
        print("❌ PlateRecognizer API error:", response.status_code)
        return None

def generate_upi_qr(vehicle_number: str, upi_id: str = "merchant@upi"):
    try:
        # Get the booking session with total_fee
        result = supabase.table("booking_sessions") \
            .select("total_fee, duration_minutes") \
            .eq("vehicle_number", vehicle_number) \
            .eq("status", "completed") \
            .order("exit_time", desc=True) \
            .limit(1) \
            .execute()
        
        if result.data:
            total_fee = result.data[0]["total_fee"]
            duration = result.data[0]["duration_minutes"]
            
            print(f"💰 Total Amount: ₹{total_fee} for {duration} minutes")
            
            # Create UPI URI
            upi_uri = f"upi://pay?pa={upi_id}&pn=ParkWise&am={total_fee}&cu=INR&tn={vehicle_number}"
            
            # Generate QR
            qr = qrcode.make(upi_uri)
            filename = f"upi_qr_{vehicle_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            qr.save(filename)
            
            print(f"✅ QR code saved as {filename}")
            return filename
        else:
            print("❌ No completed booking found for this vehicle")
            return None
            
    except Exception as e:
        print(f"❌ Error generating QR: {e}")
        return None

def handle_entry(plate):
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Find booking session with status "booked" for this vehicle
        booking = supabase.table("booking_sessions") \
            .select("*") \
            .eq("vehicle_number", plate) \
            .eq("status", "booked") \
            .limit(1) \
            .execute()
        
        if booking.data:
            booking_id = booking.data[0]["id"]
            # Update the existing booking with entry time and change status to "active"
            result = supabase.table("booking_sessions").update({
                "entry_time": now,
                "status": "active"
            }).eq("id", booking_id).execute()
            
            print("✅ Entry logged successfully!")
            print(f"   Vehicle: {plate}")
            print(f"   Entry time: {now}")
            print(f"   Status: active")
            return True
        else:
            print("⚠️ No booked session found for this vehicle")
            return False
            
    except Exception as e:
        print(f"❌ Error logging entry: {e}")
        return False

def handle_exit(plate):
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    # Find the latest active session
    try:
        session = supabase.table("booking_sessions") \
            .select("*") \
            .eq("vehicle_number", plate) \
            .eq("status", "active") \
            .order("entry_time", desc=True) \
            .limit(1) \
            .execute()

        if session.data:
            session_id = session.data[0]["id"]
            result = supabase.table("booking_sessions").update({
                "exit_time": now,
                "status": "completed"
            }).eq("id", session_id).execute()
            print("✅ Exit logged successfully!")
            print(f"   Vehicle: {plate}")
            print(f"   Exit time: {now}")
            print(f"   Status: completed")
            
            # Generate QR code for payment
            generate_upi_qr(plate)
            return True
        else:
            print("⚠️ No active session found for this vehicle.")
            return False
    except Exception as e:
        print(f"❌ Error logging exit: {e}")
        return False

def main():
    print("🚨 Welcome to Security App 🚨")
    mode = input("Enter mode (entry/exit): ").strip().lower()
    if mode not in ["entry", "exit"]:
        print("❌ Invalid mode. Choose 'entry' or 'exit'.")
        return

    image_path = capture_plate_image()
    plate = recognize_plate(image_path)

    if plate:
        print(f"🔍 Plate detected: {plate}")
        if mode == "entry":
            handle_entry(plate)
        else:
            handle_exit(plate)
    else:
        print("❌ Could not recognize plate. Try again.")

if __name__ == "__main__":
    main()
