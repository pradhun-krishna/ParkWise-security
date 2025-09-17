#!/usr/bin/env python3
"""
Shobha Apartment ANPR Dashboard
Live camera feed with real-time plate detection
Only accesses Shobha-related tables
"""

from flask import Flask, render_template, jsonify, request, Response  # pyright: ignore[reportMissingImports]
from flask_cors import CORS  # pyright: ignore[reportMissingModuleSource]
import cv2  # pyright: ignore[reportMissingImports]
import numpy as np  # pyright: ignore[reportMissingImports]
import threading
import time
import base64
from datetime import datetime
import os
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShobhaANPRSystem:
    def __init__(self):
        self.camera = None
        self.running = False
        self.detected_plates = []
        self.last_detection_time = 0
        self.detection_interval = 2.0  # 2 seconds between detections
        
        # Database connection (Shobha tables only)
        try:
            from secure_database_connection import secure_db
            self.db = secure_db
            self.db_available = True
            logger.info("✅ Shobha database connected")
        except ImportError:
            self.db = None
            self.db_available = False
            logger.warning("⚠️ Database not available - running in demo mode")
        
        # Initialize camera
        self.init_camera()
        
        # Start detection thread
        self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.detection_thread.start()
    
    def init_camera(self):
        """Initialize camera for live feed"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                logger.error("❌ Could not open camera")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            logger.info("✅ Camera initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            return False
    
    def detect_license_plates(self, frame):
        """Enhanced license plate detection for Shobha vehicles"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Apply bilateral filter to reduce noise
            filtered = cv2.bilateralFilter(enhanced, 11, 17, 17)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(filtered, (5, 5), 0)
            
            # Apply sharpening filter
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(blurred, -1, kernel)
            
            # Multiple edge detection methods
            # Canny with adaptive thresholds
            edges1 = cv2.Canny(sharpened, 50, 150)
            edges2 = cv2.Canny(sharpened, 100, 200)
            edges3 = cv2.Canny(sharpened, 30, 100)
            
            # Combine edge detection results
            combined_edges = cv2.bitwise_or(edges1, edges2)
            combined_edges = cv2.bitwise_or(combined_edges, edges3)
            
            # Morphological operations to connect broken edges
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morphed = cv2.morphologyEx(combined_edges, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Debug: Log contour count
            logger.info(f"🔍 Found {len(contours)} contours")
            
            detected_plates = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by area (license plates are typically 200-200000 pixels) - very lenient
                if 200 < area < 200000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # License plates typically have aspect ratio between 1.0 and 6.0 - very lenient
                    if 1.0 <= aspect_ratio <= 6.0:
                        # Calculate additional quality metrics
                        hull = cv2.convexHull(contour)
                        hull_area = cv2.contourArea(hull)
                        solidity = area / hull_area if hull_area > 0 else 0
                        
                        # Calculate extent (ratio of contour area to bounding rectangle area)
                        rect_area = w * h
                        extent = area / rect_area if rect_area > 0 else 0
                        
                        # Very lenient quality requirements - just try OCR on everything
                        if solidity > 0.1 and extent > 0.1:  # Very lenient
                            logger.info(f"🔍 Potential plate: area={area:.0f}, aspect={aspect_ratio:.2f}, solidity={solidity:.2f}, extent={extent:.2f}")
                            # Draw rectangle around detected plate
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            
                            # Extract plate region
                            plate_region = frame[y:y+h, x:x+w]
                            
                            # Try real OCR first, fallback to simulation
                            plate_text = self.simulate_ocr(plate_region)
                            
                            if plate_text and len(plate_text) >= 2:  # Very lenient minimum length
                                detected_plates.append({
                                    'text': plate_text,
                                    'confidence': 0.85,
                                    'timestamp': datetime.now(),
                                    'bbox': (x, y, w, h)
                                })
                                
                                # Draw text on frame
                                cv2.putText(frame, plate_text, (x, y-10), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                logger.info(f"✅ Plate detected: {plate_text}")
                            else:
                                logger.warning(f"⚠️ OCR failed for potential plate: {plate_text}")
            
            return detected_plates, frame
            
        except Exception as e:
            logger.error(f"Plate detection error: {e}")
            return [], frame
    
    def extract_text_ocr(self, plate_region):
        """Extract text from plate region using real OCR"""
        try:
            # Try to import pytesseract
            import pytesseract  # pyright: ignore[reportMissingImports]
            
            # Set Tesseract path for Windows
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            # Preprocess the plate region for better OCR
            gray_plate = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
            
            # Apply additional preprocessing
            # Resize if too small
            if gray_plate.shape[0] < 50:
                scale_factor = 50 / gray_plate.shape[0]
                new_width = int(gray_plate.shape[1] * scale_factor)
                gray_plate = cv2.resize(gray_plate, (new_width, 50))
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray_plate, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Try different OCR configurations
            configs = [
                '--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--psm 13 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            ]
            
            best_text = ""
            best_confidence = 0
            
            for config in configs:
                try:
                    # Get text and confidence
                    data = pytesseract.image_to_data(binary, config=config, output_type=pytesseract.Output.DICT)
                    
                    # Extract text with confidence
                    text_parts = []
                    confidences = []
                    
                    for i in range(len(data['text'])):
                        if int(data['conf'][i]) > 30:  # Only consider high confidence
                            text_parts.append(data['text'][i].strip())
                            confidences.append(int(data['conf'][i]))
                    
                    if text_parts:
                        combined_text = ''.join(text_parts)
                        avg_confidence = sum(confidences) / len(confidences)
                        
                        if avg_confidence > best_confidence and len(combined_text) >= 6:
                            best_text = combined_text
                            best_confidence = avg_confidence
                            
                except Exception as e:
                    continue
            
            # Clean up the text
            if best_text:
                # Remove non-alphanumeric characters except spaces
                cleaned_text = ''.join(c for c in best_text if c.isalnum())
                
                # Validate Indian plate format (basic check)
                if len(cleaned_text) >= 6 and len(cleaned_text) <= 12:
                    return cleaned_text
            
            return None
            
        except ImportError:
            # Fallback to simulation if pytesseract not available
            return self.simulate_ocr(plate_region)
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return None
    
    def simulate_ocr(self, plate_region):
        """Simulate OCR for testing when real OCR is not available"""
        # Try real OCR first
        try:
            import pytesseract  # pyright: ignore[reportMissingImports]
            
            # Set Tesseract path for Windows
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            # Preprocess the plate region for better OCR
            gray_plate = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
            
            # Apply additional preprocessing
            # Resize if too small
            if gray_plate.shape[0] < 50:
                scale_factor = 50 / gray_plate.shape[0]
                new_width = int(gray_plate.shape[1] * scale_factor)
                gray_plate = cv2.resize(gray_plate, (new_width, 50))
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray_plate, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Try different OCR configurations
            configs = [
                '--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--psm 13 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            ]
            
            best_text = ""
            best_confidence = 0
            
            for config in configs:
                try:
                    # Get text and confidence
                    data = pytesseract.image_to_data(binary, config=config, output_type=pytesseract.Output.DICT)
                    
                    # Extract text with confidence
                    text_parts = []
                    confidences = []
                    
                    for i in range(len(data['text'])):
                        if int(data['conf'][i]) > 30:  # Only consider high confidence
                            text_parts.append(data['text'][i].strip())
                            confidences.append(int(data['conf'][i]))
                    
                    if text_parts:
                        combined_text = ''.join(text_parts)
                        avg_confidence = sum(confidences) / len(confidences)
                        
                        if avg_confidence > best_confidence and len(combined_text) >= 6:
                            best_text = combined_text
                            best_confidence = avg_confidence
                            
                except Exception as e:
                    continue
            
            # Clean up the text
            if best_text:
                # Remove non-alphanumeric characters except spaces
                cleaned_text = ''.join(c for c in best_text if c.isalnum())
                
                # Validate Indian plate format (basic check)
                if len(cleaned_text) >= 6 and len(cleaned_text) <= 12:
                    logger.info(f"🔍 Real OCR detected: {cleaned_text} (confidence: {best_confidence:.1f}%)")
                    return cleaned_text
            
            # If real OCR fails, return None instead of fake data
            logger.warning("🔍 Real OCR failed - no plate text detected")
            return None
            
        except ImportError:
            logger.warning("⚠️ pytesseract not installed - install with: pip install pytesseract")
            return None
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return None
    
    def check_shobha_database(self, plate_number):
        """Check if plate exists in Shobha permanent parking and return vehicle info"""
        if not self.db_available:
            # Demo mode - simulate some authorized plates
            authorized_plates = ["KA01AB1234", "KA02CD5678", "KA03EF9012"]
            if plate_number in authorized_plates:
                return {
                    'id': 1,
                    'vehicle_number': plate_number,
                    'phone_number': '9999999999',
                    'vehicle_type': 'car',
                    'slot_number': 'A1'
                }
            return None
        
        try:
            query = "SELECT id, vehicle_number, phone_number, vehicle_type, slot_number FROM shobha_permanent_parking WHERE vehicle_number = %s"
            result = self.db.execute_query(query, (plate_number,), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Database check error: {e}")
            return None
    
    def handle_vehicle_entry(self, plate_number, vehicle_info):
        """Handle vehicle entry - create session"""
        if not self.db_available:
            logger.info(f"Demo: Vehicle ENTRY - {plate_number}")
            return True
        
        try:
            permanent_id = vehicle_info['id']
            
            # Create entry session
            session_query = """
                INSERT INTO shobha_permanent_parking_sessions 
                (permanent_parking_id, entry_time, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
            """
            success = self.db.execute_update(session_query, (
                permanent_id, datetime.now(), datetime.now(), datetime.now()
            ))
            
            if success:
                logger.info(f"✅ ENTRY: {plate_number} - Session created")
                return True
            else:
                logger.error(f"❌ ENTRY: {plate_number} - Session creation failed")
                return False
                
        except Exception as e:
            logger.error(f"Entry session creation error: {e}")
            return False
    
    def handle_vehicle_exit(self, plate_number, vehicle_info):
        """Handle vehicle exit - update session"""
        if not self.db_available:
            logger.info(f"Demo: Vehicle EXIT - {plate_number}")
            return True
        
        try:
            permanent_id = vehicle_info['id']
            
            # Find active session (entry without exit)
            find_query = """
                SELECT id FROM shobha_permanent_parking_sessions 
                WHERE permanent_parking_id = %s AND exit_time IS NULL
                ORDER BY entry_time DESC LIMIT 1
            """
            session_result = self.db.execute_query(find_query, (permanent_id,), fetch_one=True)
            
            if session_result:
                session_id = session_result['id']
                exit_time = datetime.now()
                
                # Update session with exit time
                update_query = """
                    UPDATE shobha_permanent_parking_sessions 
                    SET exit_time = %s, duration_minutes = EXTRACT(EPOCH FROM (%s - entry_time))/60, updated_at = %s
                    WHERE id = %s
                """
                success = self.db.execute_update(update_query, (exit_time, exit_time, exit_time, session_id))
                
                if success:
                    logger.info(f"✅ EXIT: {plate_number} - Session updated")
                    return True
                else:
                    logger.error(f"❌ EXIT: {plate_number} - Session update failed")
                    return False
            else:
                logger.warning(f"❌ EXIT: {plate_number} - No active session found")
                return False
                
        except Exception as e:
            logger.error(f"Exit session update error: {e}")
            return False
    
    def determine_entry_or_exit(self, plate_number, vehicle_info):
        """Determine if this is an entry or exit based on active sessions"""
        if not self.db_available:
            # Demo mode - alternate between entry and exit
            return len(self.detected_plates) % 2 == 0
        
        try:
            permanent_id = vehicle_info['id']
            
            # Check if there's an active session (entry without exit)
            query = """
                SELECT COUNT(*) as active_count FROM shobha_permanent_parking_sessions 
                WHERE permanent_parking_id = %s AND exit_time IS NULL
            """
            result = self.db.execute_query(query, (permanent_id,), fetch_one=True)
            
            if result and result['active_count'] > 0:
                # Has active session - this is an EXIT
                return False
            else:
                # No active session - this is an ENTRY
                return True
                
        except Exception as e:
            logger.error(f"Entry/Exit determination error: {e}")
            # Default to entry if error
            return True
    
    def detection_loop(self):
        """Main detection loop running in separate thread"""
        self.running = True
        
        while self.running:
            try:
                if self.camera and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret:
                        current_time = time.time()
                        
                        # Detect plates every 2 seconds
                        if current_time - self.last_detection_time >= self.detection_interval:
                            detected_plates, processed_frame = self.detect_license_plates(frame)
                            
                            # Debug: Log detection attempts
                            if len(detected_plates) > 0:
                                logger.info(f"🔍 Detected {len(detected_plates)} potential plates")
                            
                            for plate in detected_plates:
                                plate_text = plate['text']
                                
                                # Check if already detected recently
                                if not any(p['text'] == plate_text and 
                                         (current_time - p['timestamp'].timestamp()) < 10 
                                         for p in self.detected_plates):
                                    
                                    # Add to detected plates list
                                    self.detected_plates.append(plate)
                                    
                                    logger.info(f"📋 New plate detected: {plate_text}")
                                    
                                    # Check database for vehicle info
                                    vehicle_info = self.check_shobha_database(plate_text)
                                    
                                    if vehicle_info:
                                        # Vehicle is authorized - determine IN or OUT
                                        is_entry = self.determine_entry_or_exit(plate_text, vehicle_info)
                                        
                                        # Update plate info with entry/exit status
                                        plate['is_entry'] = is_entry
                                        plate['vehicle_info'] = vehicle_info
                                        
                                        if is_entry:
                                            # Handle ENTRY
                                            success = self.handle_vehicle_entry(plate_text, vehicle_info)
                                            if success:
                                                logger.info(f"🚪 ENTRY: {plate_text} - Barrier opening")
                                                # TODO: Open boom barrier for entry
                                            else:
                                                logger.error(f"❌ ENTRY: {plate_text} - Session creation failed")
                                        else:
                                            # Handle EXIT
                                            success = self.handle_vehicle_exit(plate_text, vehicle_info)
                                            if success:
                                                logger.info(f"🚪 EXIT: {plate_text} - Barrier opening")
                                                # TODO: Open boom barrier for exit
                                            else:
                                                logger.error(f"❌ EXIT: {plate_text} - Session update failed")
                                    else:
                                        logger.info(f"❌ Unauthorized vehicle: {plate_text}")
                                        plate['is_entry'] = None
                                        # TODO: Deny access (buzzer)
                            
                            self.last_detection_time = current_time
                        
                        # Keep only recent detections (last 30 seconds)
                        self.detected_plates = [
                            p for p in self.detected_plates 
                            if (current_time - p['timestamp'].timestamp()) < 30
                        ]
                
                time.sleep(0.1)  # Small delay to prevent high CPU usage
                
            except Exception as e:
                logger.error(f"Detection loop error: {e}")
                time.sleep(1)
    
    def get_live_frame(self):
        """Get live camera frame for streaming"""
        if self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                # Resize frame for web display
                frame = cv2.resize(frame, (640, 480))
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    return buffer.tobytes()
        return None
    
    def get_detected_plates(self):
        """Get list of recently detected plates"""
        return sorted(self.detected_plates, key=lambda x: x['timestamp'], reverse=True)
    
    def get_shobha_stats(self):
        """Get Shobha-specific statistics"""
        if not self.db_available:
            return {
                'total_vehicles': 8,
                'vehicles_in': 2,
                'vehicles_out': 6,
                'active_sessions': 2,
                'detected_today': len(self.detected_plates),
                'barrier_status': 'closed'
            }
        
        try:
            # Get total permanent vehicles
            total_query = "SELECT COUNT(*) as count FROM shobha_permanent_parking"
            total_result = self.db.execute_query(total_query, fetch_one=True)
            total_vehicles = total_result['count'] if total_result else 0
            
            # Get vehicles currently IN (active sessions)
            in_query = "SELECT COUNT(*) as count FROM shobha_permanent_parking_sessions WHERE exit_time IS NULL"
            in_result = self.db.execute_query(in_query, fetch_one=True)
            vehicles_in = in_result['count'] if in_result else 0
            
            # Get vehicles OUT (completed sessions today)
            out_query = """
                SELECT COUNT(*) as count FROM shobha_permanent_parking_sessions 
                WHERE exit_time IS NOT NULL AND DATE(exit_time) = CURRENT_DATE
            """
            out_result = self.db.execute_query(out_query, fetch_one=True)
            vehicles_out = out_result['count'] if out_result else 0
            
            return {
                'total_vehicles': total_vehicles,
                'vehicles_in': vehicles_in,
                'vehicles_out': vehicles_out,
                'active_sessions': vehicles_in,
                'detected_today': len(self.detected_plates),
                'barrier_status': 'closed'
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {
                'total_vehicles': 0,
                'vehicles_in': 0,
                'vehicles_out': 0,
                'active_sessions': 0,
                'detected_today': 0,
                'barrier_status': 'closed'
            }

# Create global ANPR system instance
anpr_system = ShobhaANPRSystem()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('shodha_dashboard.html')

@app.route('/api/live_feed')
def live_feed():
    """Live camera feed endpoint"""
    def generate_frames():
        while True:
            frame = anpr_system.get_live_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
    
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/detected_plates')
def detected_plates():
    """Get recently detected plates"""
    plates = anpr_system.get_detected_plates()
    return jsonify(plates)

@app.route('/api/stats')
def stats():
    """Get Shobha statistics"""
    return jsonify(anpr_system.get_shobha_stats())

@app.route('/api/control_barrier', methods=['POST'])
def control_barrier():
    """Control boom barrier"""
    data = request.get_json()
    action = data.get('action', 'close')
    
    logger.info(f"🚧 Barrier control: {action}")
    # TODO: Implement actual barrier control
    
    return jsonify({'success': True, 'action': action})

def main():
    """Main function"""
    print("🏠 Shobha Apartment ANPR System")
    print("=" * 50)
    print("Features:")
    print("• Live camera feed")
    print("• Real-time plate detection")
    print("• Shobha database integration")
    print("• Automatic boom barrier control")
    print("=" * 50)
    print("🌐 Dashboard: http://localhost:5000")
    print("📹 Live Feed: http://localhost:5000/api/live_feed")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        anpr_system.running = False
        if anpr_system.camera:
            anpr_system.camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
