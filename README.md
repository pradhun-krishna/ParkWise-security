# ParkWise Security - ANPR Systems

A comprehensive collection of Automated Number Plate Recognition (ANPR) systems for parking management and security.

## 🚗 ANPR System Types

### 1. **Standalone OpenCV ANPR** (`opencv_anpr_system.py`)
- **Pure OpenCV implementation** - no external dependencies
- **Local processing** - works offline
- **Good for basic detection** - suitable for simple use cases
- **Free** - no API costs

**Usage:**
```bash
python opencv_anpr_system.py
```

### 2. **Standalone Plate Recognizer API** (`plate_recognizer_api.py`)
- **High accuracy** - cloud-based OCR
- **Professional grade** - commercial API
- **Requires API key** - from Plate Recognizer
- **Cost per detection** - pay per use

**Usage:**
```bash
# Set API key
set PLATE_RECOGNIZER_API_KEY=your_key_here
python plate_recognizer_api.py
```

### 3. **Smart Hybrid ANPR** (`smart_hybrid_anpr.py`)
- **Best of both worlds** - OpenCV + API
- **Efficient** - only sends to API when plate detected
- **Cost-effective** - 95% fewer API calls
- **High accuracy** - uses API for final OCR

**Usage:**
```bash
python smart_hybrid_anpr.py
```

### 4. **Shobha Apartment System** (`shobha_anpr_dashboard.py`)
- **Shobha-specific** - integrated with apartment database
- **Web dashboard** - real-time monitoring
- **Boom barrier control** - automatic gate opening
- **Session management** - tracks entry/exit

**Usage:**
```bash
python start_shobha_system.py
```

### 5. **Smart Shobha System** (`shobha_smart_dashboard.py`)
- **Smart hybrid** - OpenCV + API for Shobha
- **Efficient API usage** - only when needed
- **High accuracy** - best detection results
- **Cost-effective** - minimal API calls

**Usage:**
```bash
python start_smart_system.py
```

## 🏗️ Project Structure

```
ParkWise-security-1/
├── opencv_anpr_system.py          # Standalone OpenCV ANPR
├── plate_recognizer_api.py         # Standalone Plate Recognizer API
├── smart_hybrid_anpr.py           # Smart Hybrid ANPR
├── shobha_anpr_dashboard.py       # Shobha OpenCV System
├── shobha_smart_dashboard.py      # Shobha Smart System
├── secure_database_connection.py  # Database connection
├── start_shobha_system.py         # Start Shobha system
├── start_smart_system.py          # Start Smart system
├── requirements.txt               # Dependencies
├── config.env.example            # Configuration template
├── templates/                     # Web dashboard templates
│   ├── dashboard.html
│   └── shodha_dashboard.html
└── logs/                         # System logs
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy and edit configuration
copy config.env.example .env

# Set your API key (optional)
set PLATE_RECOGNIZER_API_KEY=your_key_here
```

### 3. Choose Your System

#### For Basic Detection (Free):
```bash
python opencv_anpr_system.py
```

#### For High Accuracy (API Required):
```bash
python plate_recognizer_api.py
```

#### For Smart Detection (Recommended):
```bash
python smart_hybrid_anpr.py
```

#### For Shobha Apartment:
```bash
python start_shobha_system.py
```

#### For Smart Shobha Apartment:
```bash
python start_smart_system.py
```

## 🔧 Configuration

### Environment Variables
- `PLATE_RECOGNIZER_API_KEY` - Your Plate Recognizer API key
- `DATABASE_URL` - PostgreSQL database connection
- `CAMERA_INDEX` - Camera device index (default: 0)

### Database Tables (Shobha)
- `shobha_permanent_parking` - Registered vehicles
- `shobha_permanent_parking_sessions` - Entry/exit sessions

## 📊 System Comparison

| System | Accuracy | Cost | Speed | Offline | API Required |
|--------|----------|------|-------|---------|--------------|
| OpenCV | Medium | Free | Fast | Yes | No |
| Plate Recognizer | High | Paid | Medium | No | Yes |
| Smart Hybrid | High | Low | Fast | Yes | Optional |
| Shobha System | Medium | Free | Fast | Yes | No |
| Smart Shobha | High | Low | Fast | Yes | Optional |

## 🎯 Use Cases

- **OpenCV**: Basic detection, offline use, cost-sensitive
- **Plate Recognizer**: High accuracy, commercial use, API budget available
- **Smart Hybrid**: Best balance, efficient API usage, production ready
- **Shobha Systems**: Apartment-specific, integrated with database

## 📝 Notes

- All systems support real-time camera feed
- Web dashboards available for monitoring
- Database integration for vehicle management
- Boom barrier control for automated gates
- Session tracking for entry/exit management

## 🔗 API Keys

Get your free Plate Recognizer API key at: https://app.platerecognizer.com/

## 📞 Support

For issues or questions, check the system logs in the `logs/` directory.