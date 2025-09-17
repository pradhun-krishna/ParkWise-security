# 🚗 ANPR Trigger System Guide

## 🎯 **OVERVIEW**

The ANPR Trigger System automatically detects license plates from CCTV cameras, checks them against the database, and controls boom barriers for entry/exit.

## 🔧 **SYSTEM COMPONENTS**

### **1. Cameras**
- **Entry Camera**: Detects vehicles entering the parking lot
- **Exit Camera**: Detects vehicles leaving the parking lot
- **Trigger**: Continuous monitoring with plate detection every 2-3 seconds

### **2. Database Integration**
- **Permanent Parking Table**: `shobha_permanent_parking`
- **Sessions Table**: `shobha_permanent_parking_sessions`
- **Real-time Checking**: Each detected plate is checked against database

### **3. Boom Barriers**
- **Entry Barrier**: Opens for authorized vehicles entering
- **Exit Barrier**: Opens for authorized vehicles leaving
- **LED Indicators**: Green when open, Red when closed
- **Buzzer**: Audio feedback for authorized/unauthorized vehicles

## 🚀 **TRIGGER WORKFLOW**

### **Entry Process**
1. **Camera Detection**: Entry camera continuously monitors
2. **Plate Detection**: OpenCV detects license plates in video feed
3. **OCR Processing**: Extracts text from detected plates
4. **Validation**: Validates Indian license plate format
5. **Database Check**: Queries `shobha_permanent_parking` table
6. **Authorization**:
   - ✅ **Authorized**: Opens entry barrier, creates session, triggers buzzer
   - ❌ **Unauthorized**: Triggers buzzer, barrier remains closed
7. **Session Management**: Creates entry record in database
8. **Barrier Control**: Closes barrier after 10-15 seconds

### **Exit Process**
1. **Camera Detection**: Exit camera continuously monitors
2. **Plate Detection**: OpenCV detects license plates in video feed
3. **OCR Processing**: Extracts text from detected plates
4. **Validation**: Validates Indian license plate format
5. **Database Check**: Queries `shobha_permanent_parking` table
6. **Authorization**:
   - ✅ **Authorized**: Opens exit barrier, updates session, triggers buzzer
   - ❌ **Unauthorized**: Triggers buzzer, barrier remains closed
7. **Session Management**: Updates exit record in database
8. **Barrier Control**: Closes barrier after 10-15 seconds

## 📁 **FILES CREATED**

### **1. `anpr_trigger_system.py`** - Complete System
- **Purpose**: Full ANPR system with all features
- **Features**:
  - Dual camera support (entry/exit)
  - Real-time plate detection
  - Database integration
  - Boom barrier control
  - Session management
  - GPIO control (Raspberry Pi)
- **Usage**: `python anpr_trigger_system.py`

### **2. `simple_anpr_trigger.py`** - Simplified Version
- **Purpose**: Easy-to-test version
- **Features**:
  - Dual camera support
  - Simulated OCR (for testing)
  - Database checking
  - Barrier control simulation
  - Session management
- **Usage**: `python simple_anpr_trigger.py`

## ⚙️ **CONFIGURATION**

### **Environment Variables** (`.env` file)
```env
# Camera Configuration
ENTRY_CAMERA_INDEX=0
EXIT_CAMERA_INDEX=1

# GPIO Configuration (Raspberry Pi)
ENTRY_BARRIER_PIN=18
EXIT_BARRIER_PIN=19
ENTRY_LED_PIN=20
EXIT_LED_PIN=21
BUZZER_PIN=22

# Detection Settings
DETECTION_INTERVAL=3
BARRIER_OPEN_TIME=10
```

### **Database Tables Required**
- `shobha_permanent_parking` - Permanent vehicle database
- `shobha_permanent_parking_sessions` - Session tracking

## 🎮 **TESTING THE SYSTEM**

### **Step 1: Test Simple Version**
```bash
python simple_anpr_trigger.py
```
This will:
- Start both cameras
- Simulate plate detection
- Check database
- Control barriers
- Show real-time video feeds

### **Step 2: Test Complete System**
```bash
python anpr_trigger_system.py
```
This will:
- Start both cameras
- Real plate detection
- Database integration
- GPIO control (if available)
- Full session management

## 🔍 **DETECTION PROCESS**

### **1. Camera Monitoring**
- Continuous video feed from both cameras
- Processes every 30th frame to reduce CPU load
- Detection interval: 2-3 seconds between checks

### **2. Plate Detection**
- OpenCV contour detection
- Aspect ratio filtering (2:1 to 5:1)
- Size filtering (width > 100px, height > 30px)
- Rectangle shape validation

### **3. OCR Processing**
- Image preprocessing (grayscale, threshold)
- Tesseract OCR (if available)
- Text cleaning and validation
- Indian license plate format validation

### **4. Database Checking**
- Real-time query to `shobha_permanent_parking`
- Vehicle number matching
- Authorization decision

## 🚧 **BARRIER CONTROL**

### **Entry Barrier**
- **Open**: When authorized vehicle detected
- **LED**: Green when open
- **Duration**: 10-15 seconds
- **Close**: Automatic after delay

### **Exit Barrier**
- **Open**: When authorized vehicle detected
- **LED**: Green when open
- **Duration**: 10-15 seconds
- **Close**: Automatic after delay

### **Unauthorized Vehicles**
- **Barrier**: Remains closed
- **Buzzer**: Short beep (1 second)
- **LED**: Red (closed)

## 📊 **SESSION MANAGEMENT**

### **Entry Session**
- Creates record in `shobha_permanent_parking_sessions`
- Records entry time
- Links to permanent parking record

### **Exit Session**
- Updates existing session record
- Records exit time
- Calculates duration
- Marks session as completed

## 🔧 **HARDWARE REQUIREMENTS**

### **Cameras**
- USB cameras or IP cameras
- Good lighting for plate detection
- Stable mounting
- Clear view of license plates

### **Raspberry Pi (Optional)**
- GPIO pins for barrier control
- Relay modules for barrier motors
- LED indicators
- Buzzer for audio feedback

### **Boom Barriers**
- Motorized barriers
- Power supply
- Relay control
- Safety sensors

## 🚀 **QUICK START**

1. **Configure cameras**: Update `.env` with camera indices
2. **Test detection**: Run `python simple_anpr_trigger.py`
3. **Check database**: Ensure vehicles are in `shobha_permanent_parking`
4. **Test barriers**: Verify barrier control works
5. **Start system**: Run `python anpr_trigger_system.py`

## 📝 **TROUBLESHOOTING**

### **Camera Issues**
- Check camera indices (0, 1, 2)
- Ensure cameras are not used by other apps
- Verify camera permissions

### **Detection Issues**
- Ensure good lighting
- Check plate visibility
- Adjust detection parameters

### **Database Issues**
- Verify database connection
- Check table permissions
- Ensure data exists

### **Barrier Issues**
- Check GPIO connections
- Verify relay modules
- Test barrier motors

## 🎯 **EXPECTED BEHAVIOR**

### **Authorized Vehicle**
1. Camera detects plate
2. OCR extracts text
3. Database check passes
4. Barrier opens
5. LED turns green
6. Buzzer sounds
7. Session created/updated
8. Barrier closes after delay

### **Unauthorized Vehicle**
1. Camera detects plate
2. OCR extracts text
3. Database check fails
4. Barrier remains closed
5. LED stays red
6. Buzzer sounds (short)
7. No session created

**Your ANPR Trigger System is ready for automatic entry/exit control!** 🚗

