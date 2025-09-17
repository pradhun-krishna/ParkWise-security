#!/usr/bin/env python3
"""
Shobha Apartment Smart ANPR Dashboard
Uses smart hybrid detection - OpenCV for initial detection, API for accurate OCR
Only sends to API when potential plate is detected
"""

from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import cv2
import numpy as np
import threading
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShobhaSmartANPRSystem:
    def __init__(self):
        self.camera = None
        self.running = False
        self.detected_plates = []
        self.last_detection_time = 0
        self.detection_interval = 2.0  # 2 seconds between detections
        
        # Smart detection settings
        self.min_plate_area = 1000
        self.max_plate_area = 100000
        self.min_aspect_ratio = 1.5
        self.max_aspect_ratio = 5.0
        
        # API settings
        self.api_key = os.getenv('PLATE_RECOGNIZER_API_KEY')
        self.api_available = bool(self.api_key and self.api_key != "YOUR_API_KEY_HERE")
        
        # Detection history to avoid duplicates
        self.recent_detections = []
        self.detection_cooldown = 10  # seconds
        
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
        
        logger.info(f"🔧 Smart ANPR System initialized - API: {'✅ Available' if self.api_available else '❌ Not available'}")
    
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
    
    def detect_potential_plates_opencv(self, frame):
        """Use OpenCV to detect potential plate regions (fast, local)"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Apply bilateral filter
            filtered = cv2.bilateralFilter(enhanced, 11, 17, 17)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(filtered, (5, 5), 0)
            
            # Apply sharpening
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(blurred, -1, kernel)
            
            # Multiple edge detection
            edges1 = cv2.Canny(sharpened, 50, 150)
            edges2 = cv2.Canny(sharpened, 100, 200)
            edges3 = cv2.Canny(sharpened, 30, 100)
            
            # Combine edges
            combined_edges = cv2.bitwise_or(edges1, edges2)
            combined_edges = cv2.bitwise_or(combined_edges, edges3)
            
            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morphed = cv2.morphologyEx(combined_edges, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            potential_plates = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by area
                if self.min_plate_area < area < self.max_plate_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Filter by aspect ratio
                    if self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio:
                        # Calculate quality metrics
                        hull = cv2.convexHull(contour)
                        hull_area = cv2.contourArea(hull)
                        solidity = area / hull_area if hull_area > 0 else 0
                        
                        rect_area = w * h
                        extent = area / rect_area if rect_area > 0 else 0
                        
                        # Quality filter
                        if solidity > 0.3 and extent > 0.2:
                            potential_plates.append({
                                'bbox': (x, y, w, h),
                                'area': area,
                                'aspect_ratio': aspect_ratio,
                                'solidity': solidity,
                                'extent': extent
                            })
            
            # Sort by quality and return top 3
            potential_plates.sort(key=lambda x: x['area'] * x['solidity'] * x['extent'], reverse=True)
            return potential_plates[:3]
            
        except Exception as e:
            logger.error(f"OpenCV detection error: {e}")
            return []
    
    def send_to_api(self, frame, region):
        """Send image region to Plate Recognizer API"""
        if not self.api_available:
            return self.fallback_ocr(frame, region)
        
        try:
            import requests
            import base64
            
            x, y, w, h = region['bbox']
            plate_region = frame[y:y+h, x:x+w]
            
            # Convert to base64
            _, buffer = cv2.imencode('.jpg', plate_region)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Prepare request
            data = {
                'image': image_base64,
                'regions': ['in'],  # Focus on Indian plates
            }
            
            headers = {
                "Authorization": f"Token {self.api_key}"
            }
            
            # Make API request
            response = requests.post(
                "https://api.platerecognizer.com/v1/plate-reader/",
                headers=headers,
                data=data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                plates = []
                
                for detection in result.get('results', []):
                    plate_text = detection.get('plate', '').upper().strip()
                    confidence = detection.get('score', 0.0)
                    
                    if plate_text and len(plate_text) >= 4:
                        plates.append({
                            'text': plate_text,
                            'confidence': confidence,
                            'timestamp': datetime.now(),
                            'bbox': region['bbox'],
                            'source': 'api'
                        })
                
                logger.info(f"🔍 API detected {len(plates)} plates")
                return plates
            else:
                logger.error(f"❌ API request failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ API error: {e}")
            return []
    
    def fallback_ocr(self, frame, region):
        """Fallback OCR when API is not available"""
        try:
            x, y, w, h = region['bbox']
            plate_region = frame[y:y+h, x:x+w]
            
            # Simple fallback - return a placeholder
            return [{
                'text': f"PLATE_{int(time.time())}",
                'confidence': 0.5,
                'timestamp': datetime.now(),
                'bbox': region['bbox'],
                'source': 'fallback'
            }]
            
        except Exception as e:
            logger.error(f"Fallback OCR error: {e}")
            return []
    
    def is_duplicate_detection(self, plate_text, bbox):
        """Check if this is a duplicate detection"""
        current_time = time.time()
        
        # Clean up old detections
        self.recent_detections = [
            d for d in self.recent_detections 
            if current_time - d['timestamp'] < self.detection_cooldown
        ]
        
        # Check for duplicates
        for detection in self.recent_detections:
            if (detection['text'] == plate_text and 
                abs(detection['bbox'][0] - bbox[0]) < 50 and
                abs(detection['bbox'][1] - bbox[1]) < 50):
                return True
        
        return False
    
    def detect_license_plates(self, frame):
        """Main detection function - smart hybrid approach"""
        try:
            # Step 1: Use OpenCV to find potential plate regions
            potential_plates = self.detect_potential_plates_opencv(frame)
            
            if not potential_plates:
                return [], frame
            
            logger.info(f"🔍 Found {len(potential_plates)} potential plates")
            
            detected_plates = []
            
            for region in potential_plates:
                x, y, w, h = region['bbox']
                
                # Draw rectangle around potential plate
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Potential Plate", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Step 2: Send to API for accurate OCR
                api_results = self.send_to_api(frame, region)
                
                for plate in api_results:
                    # Check for duplicates
                    if not self.is_duplicate_detection(plate['text'], plate['bbox']):
                        detected_plates.append(plate)
                        
                        # Add to recent detections
                        self.recent_detections.append({
                            'text': plate['text'],
                            'bbox': plate['bbox'],
                            'timestamp': time.time()
                        })
                        
                        # Draw final result
                        cv2.putText(frame, plate['text'], (x, y - 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.putText(frame, f"Conf: {plate['confidence']:.2f}", (x, y - 50), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        logger.info(f"✅ Plate detected: {plate['text']} (confidence: {plate['confidence']:.2f})")
            
            return detected_plates, frame
            
        except Exception as e:
            logger.error(f"Plate detection error: {e}")
            return [], frame
    
    def check_shobha_database(self, plate_number):
        """Check if plate exists in Shobha permanent parking"""
        if not self.db_available:
            # Demo mode
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
            
            # Find active session
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
        """Determine if this is an entry or exit"""
        if not self.db_available:
            return len(self.detected_plates) % 2 == 0
        
        try:
            permanent_id = vehicle_info['id']
            
            # Check if there's an active session
            query = """
                SELECT COUNT(*) as active_count FROM shobha_permanent_parking_sessions 
                WHERE permanent_parking_id = %s AND exit_time IS NULL
            """
            result = self.db.execute_query(query, (permanent_id,), fetch_one=True)
            
            if result and result['active_count'] > 0:
                return False  # Has active session - this is an EXIT
            else:
                return True   # No active session - this is an ENTRY
                
        except Exception as e:
            logger.error(f"Entry/Exit determination error: {e}")
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
                        
                        # Detect plates every detection_interval seconds
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
                                            else:
                                                logger.error(f"❌ ENTRY: {plate_text} - Session creation failed")
                                        else:
                                            # Handle EXIT
                                            success = self.handle_vehicle_exit(plate_text, vehicle_info)
                                            if success:
                                                logger.info(f"🚪 EXIT: {plate_text} - Barrier opening")
                                            else:
                                                logger.error(f"❌ EXIT: {plate_text} - Session update failed")
                                    else:
                                        logger.info(f"❌ Unauthorized vehicle: {plate_text}")
                                        plate['is_entry'] = None
                                
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
                'barrier_status': 'closed',
                'api_available': self.api_available,
                'recent_detections': len(self.recent_detections)
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
                'barrier_status': 'closed',
                'api_available': self.api_available,
                'recent_detections': len(self.recent_detections)
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {
                'total_vehicles': 0,
                'vehicles_in': 0,
                'vehicles_out': 0,
                'active_sessions': 0,
                'detected_today': 0,
                'barrier_status': 'closed',
                'api_available': self.api_available,
                'recent_detections': len(self.recent_detections)
            }

# Create global ANPR system instance
anpr_system = ShobhaSmartANPRSystem()

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
    print("🏠 Shobha Apartment Smart ANPR System")
    print("=" * 50)
    print("Features:")
    print("• Smart hybrid detection (OpenCV + API)")
    print("• Only sends to API when plate detected")
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

