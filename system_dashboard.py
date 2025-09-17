# System Dashboard - Web UI for ANPR Parking System
# Provides data monitoring and manual boom barrier control

from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import threading
import time
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️ RPi.GPIO not available - running in simulation mode")
from secure_database_connection import secure_db as db

load_dotenv()

app = Flask(__name__)

class SystemDashboard:
    def __init__(self):
        # Database connection is handled by database_connection.py
        self.db = db
        
        # GPIO Configuration
        self.boom_barrier_pin = int(os.getenv('BOOM_BARRIER_PIN', 18))
        self.led_green_pin = int(os.getenv('LED_GREEN_PIN', 20))
        self.led_red_pin = int(os.getenv('LED_RED_PIN', 21))
        self.buzzer_pin = int(os.getenv('BUZZER_PIN', 22))
        
        # Initialize GPIO
        self.setup_gpio()
        
        # System state
        self.barrier_status = "closed"
        self.system_stats = {
            'total_sessions': 0,
            'active_sessions': 0,
            'completed_sessions': 0,
            'permanent_vehicles': 0
        }
        
        # Start background stats update
        self.start_stats_updater()
    
    def setup_gpio(self):
        """Initialize GPIO for boom barrier control"""
        if not GPIO_AVAILABLE:
            print("⚠️ GPIO not available on Windows - running in simulation mode")
            return
            
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.boom_barrier_pin, GPIO.OUT)
            GPIO.setup(self.led_green_pin, GPIO.OUT)
            GPIO.setup(self.led_red_pin, GPIO.OUT)
            GPIO.setup(self.buzzer_pin, GPIO.OUT)
            
            # Initialize all pins to LOW
            GPIO.output(self.boom_barrier_pin, GPIO.LOW)
            GPIO.output(self.led_green_pin, GPIO.LOW)
            GPIO.output(self.led_red_pin, GPIO.LOW)
            GPIO.output(self.buzzer_pin, GPIO.LOW)
            
            print("✅ GPIO initialized for dashboard")
        except Exception as e:
            print(f"⚠️ GPIO setup failed: {e}")
            print("Running in simulation mode")
    
    def start_stats_updater(self):
        """Start background thread to update system statistics"""
        def update_stats():
            while True:
                try:
                    self.update_system_stats()
                    time.sleep(30)  # Update every 30 seconds
                except Exception as e:
                    print(f"Error updating stats: {e}")
                    time.sleep(60)
        
        stats_thread = threading.Thread(target=update_stats, daemon=True)
        stats_thread.start()
    
    def update_system_stats(self):
        """Update system statistics"""
        try:
            stats = self.db.get_system_stats()
            self.system_stats.update(stats)
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    def control_boom_barrier(self, action):
        """Control boom barrier"""
        try:
            if action == "open":
                if GPIO_AVAILABLE:
                    GPIO.output(self.boom_barrier_pin, GPIO.HIGH)
                    GPIO.output(self.led_green_pin, GPIO.HIGH)
                    GPIO.output(self.led_red_pin, GPIO.LOW)
                self.barrier_status = "open"
                print("🚧 Boom barrier OPENED manually")
                
                # Auto-close after 15 seconds
                def auto_close():
                    time.sleep(15)
                    self.control_boom_barrier("close")
                
                threading.Thread(target=auto_close, daemon=True).start()
                
            elif action == "close":
                if GPIO_AVAILABLE:
                    GPIO.output(self.boom_barrier_pin, GPIO.LOW)
                    GPIO.output(self.led_green_pin, GPIO.LOW)
                    GPIO.output(self.led_red_pin, GPIO.LOW)
                self.barrier_status = "closed"
                print("🚧 Boom barrier CLOSED manually")
                
            return True
        except Exception as e:
            print(f"Error controlling boom barrier: {e}")
            return False

# Initialize dashboard
dashboard = SystemDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    return jsonify(dashboard.system_stats)

@app.route('/api/sessions')
def get_sessions():
    """Get parking sessions"""
    try:
        sessions = dashboard.db.get_recent_sessions(50)
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/active-sessions')
def get_active_sessions():
    """Get active parking sessions"""
    try:
        sessions = dashboard.db.get_active_sessions()
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/permanent-vehicles')
def get_permanent_vehicles():
    """Get permanent parking vehicles"""
    try:
        vehicles = dashboard.db.get_permanent_vehicles()
        return jsonify(vehicles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Payment endpoints removed

@app.route('/api/barrier/status')
def get_barrier_status():
    """Get boom barrier status"""
    return jsonify({'status': dashboard.barrier_status})

@app.route('/api/barrier/open', methods=['POST'])
def open_barrier():
    """Manually open boom barrier"""
    success = dashboard.control_boom_barrier("open")
    return jsonify({'success': success})

@app.route('/api/barrier/close', methods=['POST'])
def close_barrier():
    """Manually close boom barrier"""
    success = dashboard.control_boom_barrier("close")
    return jsonify({'success': success})

@app.route('/api/session/<session_id>/complete', methods=['POST'])
def complete_session(session_id):
    """Manually complete a parking session"""
    try:
        success = dashboard.db.update_session_exit(session_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vehicle/<vehicle_number>/add-permanent', methods=['POST'])
def add_permanent_vehicle():
    """Add vehicle to permanent parking"""
    try:
        data = request.get_json()
        vehicle_number = data.get('vehicle_number')
        owner_name = data.get('owner_name')
        parking_lot_id = data.get('parking_lot_id', '1')
        
        item = {
            'vehicle_number': vehicle_number,
            'owner_name': owner_name,
            'parking_lot_id': parking_lot_id,
            'valid_from': datetime.now().strftime('%Y-%m-%d'),
            'valid_until': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'vehicle_type': 'car',
            'created_at': datetime.now().isoformat()
        }
        
        dashboard.permanent_table.put_item(Item=item)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vehicle/<vehicle_number>/remove-permanent', methods=['DELETE'])
def remove_permanent_vehicle(vehicle_number):
    """Remove vehicle from permanent parking"""
    try:
        dashboard.permanent_table.delete_item(
            Key={'vehicle_number': vehicle_number}
        )
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting ANPR System Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🔧 Boom barrier control enabled")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
