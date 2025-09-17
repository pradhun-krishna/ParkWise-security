#!/usr/bin/env python3
# Webcam Debug - Debug webcam issues

import cv2
import sys
import time

def main():
    print("🔍 Webcam Debug Tool")
    print("=" * 30)
    
    # Check OpenCV version
    print(f"OpenCV version: {cv2.__version__}")
    
    # Try to open camera
    print("Trying to open camera...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Camera 0 failed")
        print("Trying camera 1...")
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("❌ Camera 1 failed")
            print("Trying camera 2...")
            cap = cv2.VideoCapture(2)
            if not cap.isOpened():
                print("❌ No cameras found")
                return
    
    print("✅ Camera opened successfully")
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Camera properties:")
    print(f"  Width: {width}")
    print(f"  Height: {height}")
    print(f"  FPS: {fps}")
    
    # Set window properties
    cv2.namedWindow('Webcam Debug', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Webcam Debug', 800, 600)
    
    print("\n📺 Opening webcam window...")
    print("If you don't see a window, check:")
    print("1. Look for a window titled 'Webcam Debug'")
    print("2. Check if it's minimized in taskbar")
    print("3. Press 'q' to quit")
    print("4. Wait 10 seconds for window to appear...")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame")
                break
            
            frame_count += 1
            elapsed = time.time() - start_time
            
            # Add debug info
            cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Time: {elapsed:.1f}s", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'q' to quit", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Show frame
            cv2.imshow('Webcam Debug', frame)
            
            # Print status every 30 frames
            if frame_count % 30 == 0:
                print(f"Frame {frame_count} - {elapsed:.1f}s elapsed")
            
            # Check for quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("🛑 Quitting...")
                break
            elif key == 27:  # ESC key
                print("🛑 ESC pressed, quitting...")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Debug completed")

if __name__ == "__main__":
    main()

