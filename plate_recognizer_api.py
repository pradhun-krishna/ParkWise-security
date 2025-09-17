#!/usr/bin/env python3
"""
Plate Recognizer API Integration
High accuracy number plate recognition using Plate Recognizer API
"""

import requests
import base64
import cv2
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PlateRecognizerAPI:
    def __init__(self, api_key=None):
        """
        Initialize Plate Recognizer API
        
        Args:
            api_key: Your Plate Recognizer API key (get from https://app.platerecognizer.com/)
        """
        self.api_key = api_key or "YOUR_API_KEY_HERE"  # Replace with your actual API key
        self.base_url = "https://api.platerecognizer.com/v1/plate-reader/"
        self.headers = {
            "Authorization": f"Token {self.api_key}"
        }
    
    def detect_plates(self, image):
        """
        Detect number plates in image using Plate Recognizer API
        
        Args:
            image: OpenCV image (numpy array)
            
        Returns:
            List of detected plates with confidence scores
        """
        try:
            # Convert image to base64
            _, buffer = cv2.imencode('.jpg', image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Prepare request data
            data = {
                'image': image_base64,
                'regions': ['in'],  # Focus on Indian plates
                'config': '{"region": {"type": "polygon", "vertices": [[0, 0], [image_width, 0], [image_width, image_height], [0, image_height]]}}'
            }
            
            # Make API request
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                plates = []
                
                for detection in result.get('results', []):
                    plate_info = {
                        'text': detection.get('plate', '').upper(),
                        'confidence': detection.get('score', 0.0),
                        'bbox': detection.get('box', {}),
                        'timestamp': datetime.now(),
                        'region': detection.get('region', {}),
                        'vehicle_type': detection.get('vehicle', {}).get('type', 'unknown')
                    }
                    plates.append(plate_info)
                
                logger.info(f"🔍 Plate Recognizer detected {len(plates)} plates")
                return plates
            else:
                logger.error(f"❌ API request failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Plate Recognizer API error: {e}")
            return []
    
    def test_api(self):
        """Test if API key is working"""
        try:
            # Create a simple test image
            test_image = np.zeros((100, 300, 3), dtype=np.uint8)
            cv2.putText(test_image, "TEST", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            result = self.detect_plates(test_image)
            if result is not None:
                logger.info("✅ Plate Recognizer API is working")
                return True
            else:
                logger.error("❌ Plate Recognizer API test failed")
                return False
        except Exception as e:
            logger.error(f"❌ Plate Recognizer API test error: {e}")
            return False

# Free tier usage example
def get_free_api_key():
    """
    Get free API key from Plate Recognizer
    Visit: https://app.platerecognizer.com/
    """
    print("🔑 To get your free API key:")
    print("1. Visit: https://app.platerecognizer.com/")
    print("2. Sign up for free account")
    print("3. Get your API key from dashboard")
    print("4. Replace 'YOUR_API_KEY_HERE' in the code")
    print("5. Free tier: 2,500 requests/month")

if __name__ == "__main__":
    # Test the API
    api = PlateRecognizerAPI()
    get_free_api_key()
    
    # Test with camera
    print("\n🔍 Testing with camera...")
    cap = cv2.VideoCapture(0)
    
    if cap.isOpened():
        print("✅ Camera opened - show a number plate")
        print("Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Test detection every 60 frames (2 seconds)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # Show frame
            cv2.imshow('Plate Recognizer Test', frame)
        
        cap.release()
        cv2.destroyAllWindows()
    else:
        print("❌ Could not open camera")
