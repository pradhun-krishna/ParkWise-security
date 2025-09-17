# ANPR Automated Parking System

A comprehensive Automated Number Plate Recognition (ANPR) system for automated parking management with boom barrier control, payment integration, and AWS database connectivity.

## 🚀 Features

- **Automatic License Plate Recognition** using OpenCV and Tesseract OCR
- **Dual Camera Support** for entry and exit monitoring
- **AWS DynamoDB Integration** for session management
- **Boom Barrier Control** via GPIO (Raspberry Pi)
- **UPI Payment Integration** with QR code generation
- **Permanent Parking Support** for authorized vehicles
- **Real-time Payment Processing** with timeout handling
- **Hardware Status Indicators** (LEDs, Buzzer)
- **Comprehensive Logging** and error handling

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Entry Camera  │    │   Exit Camera   │    │   Display       │
│   (ANPR)        │    │   (ANPR)        │    │   (QR Codes)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │    Main Controller        │
                    │  (Raspberry Pi/Computer)  │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼───────┐    ┌───────────▼───────────┐    ┌────────▼────────┐
│  AWS DynamoDB │    │   Boom Barrier        │    │  Payment System │
│  (Sessions)   │    │   Control (GPIO)      │    │  (UPI QR)       │
└───────────────┘    └───────────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

### Hardware Requirements
- **Raspberry Pi 4** (recommended) or compatible computer
- **USB Camera(s)** for license plate capture
- **Boom Barrier** with GPIO control capability
- **LED Indicators** (Green/Red)
- **Buzzer** for audio feedback
- **External Display** for QR codes

### Software Requirements
- **Python 3.8+**
- **OpenCV 4.x**
- **Tesseract OCR**
- **AWS Account** with DynamoDB access
- **Raspberry Pi OS** (if using Pi)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ParkWise-security
```

### 2. Run Automated Setup
```bash
python setup_system.py
```

### 3. Manual Setup (if automated setup fails)

#### Install System Dependencies

**On Raspberry Pi/Ubuntu:**
```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-eng python3-opencv python3-pip
```

**On Windows:**
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Add to PATH environment variable

**On macOS:**
```bash
brew install tesseract
```

#### Install Python Packages
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp config.env.example .env
# Edit .env with your actual configuration
```

### 5. Setup AWS Tables
```bash
python aws_setup.py
```

## ⚙️ Configuration

### Environment Variables (.env)
```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Parking Configuration
PARKING_LOT_ID=1
HOURLY_RATE=50.0
MINIMUM_CHARGE=20.0

# Camera Configuration
CAMERA_INDEX=0
EXIT_CAMERA_INDEX=1

# GPIO Pin Configuration (Raspberry Pi)
BOOM_BARRIER_PIN=18
LED_GREEN_PIN=20
LED_RED_PIN=21
BUZZER_PIN=22

# Payment Configuration
UPI_MERCHANT_ID=parkwise@upi
PAYMENT_TIMEOUT=300
```

### Hardware Wiring (Raspberry Pi)
```
Boom Barrier Motor → GPIO Pin 18
Green LED → GPIO Pin 20
Red LED → GPIO Pin 21
Buzzer → GPIO Pin 22
```

## 🚀 Usage

### Start the System
```bash
python main_parking_system.py
```

### System Modes

#### 1. Dual Camera System
- Separate cameras for entry and exit
- Automatic processing based on camera location
- Press SPACE to capture in each camera window

#### 2. Single Camera System
- One camera with mode switching
- Press 'e' for entry mode, 'x' for exit mode
- Press SPACE to capture

#### 3. Test Mode
- Single detection test
- Useful for debugging and calibration

### Controls
- **SPACE/Enter**: Capture and process license plate
- **'e'**: Switch to entry mode (single camera)
- **'x'**: Switch to exit mode (single camera)
- **'q'**: Quit system

## 🔧 System Components

### 1. ANPR System (`anpr_system.py`)
- License plate detection using OpenCV
- Multiple detection methods for accuracy
- Integration with Tesseract OCR
- Permanent parking database checks

### 2. Payment System (`payment_system.py`)
- UPI QR code generation
- Payment verification (simulated)
- Boom barrier control
- Hardware status indicators

### 3. AWS Integration (`aws_setup.py`)
- DynamoDB table creation
- Session management
- Payment logging
- Permanent parking management

### 4. Main Controller (`main_parking_system.py`)
- System orchestration
- Multi-threading for dual cameras
- User interface
- Error handling and recovery

## 📊 Database Schema

### Parking Sessions Table
```json
{
  "session_id": "1_KA01AB1234_1234567890",
  "vehicle_number": "KA01AB1234",
  "parking_lot_id": "1",
  "entry_time": "2024-01-01T10:00:00",
  "exit_time": "2024-01-01T12:00:00",
  "status": "completed",
  "total_charge": 100.0,
  "duration_hours": 2.0,
  "payment_status": "paid"
}
```

### Permanent Parking Table
```json
{
  "vehicle_number": "KA01AB1234",
  "owner_name": "John Doe",
  "parking_lot_id": "1",
  "valid_from": "2024-01-01",
  "valid_until": "2024-12-31",
  "vehicle_type": "car",
  "contact_number": "+919876543210"
}
```

## 🔒 Security Features

- **Environment Variable Protection**: Sensitive data in .env files
- **Input Validation**: License plate format validation
- **Error Handling**: Comprehensive error catching and logging
- **Hardware Safety**: Barrier area clearance checks
- **Payment Verification**: Transaction validation (when integrated)

## 🐛 Troubleshooting

### Common Issues

#### Camera Not Detected
```bash
# Check camera devices
ls /dev/video*
# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Error')"
```

#### GPIO Permission Denied
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
# Reboot required
sudo reboot
```

#### Tesseract Not Found
```bash
# Install tesseract
sudo apt install tesseract-ocr
# Check installation
tesseract --version
```

#### AWS Connection Issues
- Verify AWS credentials in .env
- Check AWS region configuration
- Ensure DynamoDB permissions

### Debug Mode
```bash
# Enable debug logging
export DEBUG=1
python main_parking_system.py
```

## 📈 Performance Optimization

### Camera Settings
- Use appropriate resolution (1280x720 recommended)
- Ensure good lighting conditions
- Position camera at optimal angle (45-60 degrees)

### Detection Accuracy
- Clean license plates for better recognition
- Use high-contrast backgrounds
- Ensure proper camera focus

### System Performance
- Use SSD storage for better I/O performance
- Ensure adequate cooling for Raspberry Pi
- Monitor system resources

## 🔄 Maintenance

### Regular Tasks
- Clean camera lenses
- Check boom barrier mechanism
- Verify AWS connectivity
- Update system packages

### Log Monitoring
```bash
# Check system logs
tail -f logs/system.log
```

### Database Cleanup
```bash
# Archive old sessions (implement as needed)
python cleanup_old_sessions.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the documentation

## 🔮 Future Enhancements

- [ ] Mobile app integration
- [ ] Real-time payment gateway integration
- [ ] Machine learning for better plate recognition
- [ ] Multi-language support
- [ ] Cloud-based monitoring dashboard
- [ ] SMS notifications
- [ ] Integration with parking management software

---

**⚠️ Important Notes:**
- This system is designed for educational and development purposes
- Ensure proper testing before production deployment
- Follow local regulations for parking management
- Implement proper security measures for production use



