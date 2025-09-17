# Hardware Setup Guide for ANPR Parking System

Complete hardware requirements and connection guide for the real-time ANPR parking system with CCTV cameras.

## 🔌 **HARDWARE REQUIREMENTS**

### **Core System Components:**

#### **1. Main Control Unit**
- **Raspberry Pi 4B** (4GB RAM minimum, 8GB recommended)
- **MicroSD Card** (64GB+, Class 10, A2 rating)
- **Power Supply** (5V, 3A, USB-C with official adapter)
- **Heat Sinks** (for CPU and RAM)
- **Cooling Fan** (40mm, 5V)

#### **2. Camera System**
- **IP CCTV Cameras** (2 units) - 1080p minimum, 4K recommended
  - Entry camera with night vision
  - Exit camera with night vision
  - Weatherproof housing (IP66 rating)
  - RTSP streaming support
  - Power over Ethernet (PoE) capability
- **USB Cameras** (2 units) - Backup/fallback cameras
  - 1080p resolution minimum
  - USB 3.0 interface
  - Auto-focus capability
- **Camera Mounts** (2 units)
  - Adjustable mounting brackets
  - Weatherproof enclosures
  - Cable management

#### **3. Network Infrastructure**
- **Network Switch** (8-port, Gigabit)
- **Ethernet Cables** (Cat6, outdoor rated)
- **WiFi Router** (Dual-band, 802.11ac)
- **Power over Ethernet (PoE) Injector** (if using PoE cameras)

#### **4. Boom Barrier System**
- **Boom Barriers** (2 units)
  - Entry barrier (3-4 meters length)
  - Exit barrier (3-4 meters length)
  - 24V DC motor operation
  - Safety sensors (optional)
- **Relay Modules** (2 units, 4-channel, 5V)
- **Barrier Power Supply** (24V DC, 10A)
- **Barrier Control Box** (Weatherproof)

#### **5. Visual and Audio Indicators**
- **LED Strips** (2 sets)
  - Green LED strip (Entry)
  - Red LED strip (Exit)
  - 12V DC operation
- **Buzzer** (2 units, 12V DC)
- **Status Display** (Optional)
  - 7-inch HDMI display
  - Weatherproof enclosure

#### **6. Power System**
- **Main Power Supply** (12V DC, 20A)
- **Power Distribution Box**
- **UPS Battery Backup** (12V, 7Ah minimum)
- **Fuses and Circuit Breakers**
- **Power Cables** (12V, 24V)

#### **7. Enclosure and Protection**
- **Main Control Box** (Weatherproof, IP65)
- **Camera Enclosures** (Weatherproof, IP66)
- **Cable Conduits** (PVC, outdoor rated)
- **Grounding System**

## 🔧 **GPIO PIN CONNECTIONS**

### **Raspberry Pi GPIO Layout:**
```
Pin 18 (GPIO 24) -> Entry Barrier Relay IN1
Pin 19 (GPIO 10) -> Exit Barrier Relay IN1
Pin 20 (GPIO 21) -> Entry LED Strip (Green)
Pin 21 (GPIO 20) -> Exit LED Strip (Red)
Pin 22 (GPIO 25) -> Entry Buzzer
Pin 23 (GPIO 11) -> Exit Buzzer
Pin 24 (GPIO 8)  -> Status LED
Pin 25 (GPIO 7)  -> Emergency Stop
GND (Pin 6)      -> All Negative connections
5V (Pin 2)       -> Relay Module VCC
3.3V (Pin 1)     -> LED Resistors
```

### **Detailed Connections:**

#### **Entry Barrier Control:**
```
Raspberry Pi Pin 18 (GPIO 24) -> Entry Relay Module IN1
Entry Relay NO1 -> Entry Barrier Motor Positive
Entry Relay COM1 -> Entry Barrier Motor Negative
Entry Relay VCC -> Raspberry Pi 5V (Pin 2)
Entry Relay GND -> Raspberry Pi GND (Pin 6)
```

#### **Exit Barrier Control:**
```
Raspberry Pi Pin 19 (GPIO 10) -> Exit Relay Module IN1
Exit Relay NO1 -> Exit Barrier Motor Positive
Exit Relay COM1 -> Exit Barrier Motor Negative
Exit Relay VCC -> Raspberry Pi 5V (Pin 2)
Exit Relay GND -> Raspberry Pi GND (Pin 6)
```

#### **LED Indicators:**
```
Entry LED Strip:
- Positive -> Raspberry Pi Pin 20 (GPIO 21) via 220Ω resistor
- Negative -> Raspberry Pi GND (Pin 6)

Exit LED Strip:
- Positive -> Raspberry Pi Pin 21 (GPIO 20) via 220Ω resistor
- Negative -> Raspberry Pi GND (Pin 6)
```

#### **Buzzer System:**
```
Entry Buzzer:
- Positive -> Raspberry Pi Pin 22 (GPIO 25)
- Negative -> Raspberry Pi GND (Pin 6)

Exit Buzzer:
- Positive -> Raspberry Pi Pin 23 (GPIO 11)
- Negative -> Raspberry Pi GND (Pin 6)
```

## 📹 **CAMERA SETUP**

### **IP CCTV Camera Configuration:**
```
Entry Camera:
- IP Address: 192.168.1.100
- RTSP URL: rtsp://admin:password@192.168.1.100:554/stream1
- Resolution: 1920x1080
- Frame Rate: 15-30 FPS
- Night Vision: Yes
- Weatherproof: IP66

Exit Camera:
- IP Address: 192.168.1.101
- RTSP URL: rtsp://admin:password@192.168.1.101:554/stream1
- Resolution: 1920x1080
- Frame Rate: 15-30 FPS
- Night Vision: Yes
- Weatherproof: IP66
```

### **Camera Positioning:**
- **Height**: 3-4 meters above ground
- **Angle**: 15-30 degrees downward
- **Distance**: 5-10 meters from license plate area
- **Lighting**: Ensure good lighting for plate detection
- **Weather Protection**: Use weatherproof enclosures

## 🔌 **NETWORK CONFIGURATION**

### **Network Topology:**
```
Internet Router
    │
    ├── WiFi Network (for mobile access)
    │
    └── Network Switch
        ├── Raspberry Pi (192.168.1.10)
        ├── Entry Camera (192.168.1.100)
        ├── Exit Camera (192.168.1.101)
        └── Display (192.168.1.102)
```

### **Network Requirements:**
- **Bandwidth**: 100 Mbps minimum
- **Latency**: <50ms for real-time processing
- **Reliability**: 99.9% uptime
- **Security**: WPA3 encryption

## ⚡ **POWER REQUIREMENTS**

### **Power Consumption:**
- **Raspberry Pi 4**: 3A @ 5V = 15W
- **Entry Camera**: 2A @ 12V = 24W
- **Exit Camera**: 2A @ 12V = 24W
- **Entry Barrier**: 5A @ 24V = 120W
- **Exit Barrier**: 5A @ 24V = 120W
- **LEDs & Buzzer**: 1A @ 12V = 12W
- **Total**: ~315W maximum

### **Power Supply Requirements:**
- **Main Supply**: 24V DC, 15A (360W)
- **Raspberry Pi Supply**: 5V DC, 3A (15W)
- **UPS Backup**: 12V, 20Ah (240Wh)
- **Runtime**: 2-3 hours on battery

## 🛠️ **INSTALLATION STEPS**

### **Phase 1: Preparation**
1. **Site Survey**: Identify camera and barrier positions
2. **Power Planning**: Plan power distribution and UPS placement
3. **Network Planning**: Plan network infrastructure and cable routing
4. **Safety Planning**: Plan safety measures and emergency stops

### **Phase 2: Hardware Installation**
1. **Install Raspberry Pi**: Mount in weatherproof enclosure
2. **Install Cameras**: Mount and connect IP cameras
3. **Install Barriers**: Mount boom barriers and connect motors
4. **Install LEDs**: Mount LED strips and connect to GPIO
5. **Install Buzzer**: Mount buzzers and connect to GPIO

### **Phase 3: Network Setup**
1. **Configure Network**: Set up static IP addresses
2. **Test Cameras**: Verify RTSP streams work
3. **Test Connectivity**: Verify all devices can communicate
4. **Configure Security**: Set up firewall and access controls

### **Phase 4: Software Installation**
1. **Install OS**: Flash Raspberry Pi OS to SD card
2. **Install Dependencies**: Install Python packages and libraries
3. **Configure GPIO**: Set up GPIO pins and permissions
4. **Install ANPR System**: Deploy the parking system software

### **Phase 5: Testing and Calibration**
1. **Test Cameras**: Verify plate detection works
2. **Test Barriers**: Verify barrier control works
3. **Test LEDs**: Verify LED indicators work
4. **Test Buzzer**: Verify audio feedback works
5. **Test Database**: Verify database connectivity
6. **Test Dashboard**: Verify web interface works

## 📊 **SYSTEM SPECIFICATIONS**

### **Performance Requirements:**
- **Plate Detection**: 90-95% accuracy
- **Processing Time**: <3 seconds per detection
- **Response Time**: <1 second for barrier control
- **Uptime**: 99.9% availability
- **Temperature**: -20°C to +60°C operation

### **Security Requirements:**
- **Data Encryption**: All data encrypted in transit
- **Access Control**: Role-based access control
- **Audit Logging**: Complete activity logging
- **Network Security**: Firewall and intrusion detection
- **Physical Security**: Tamper-proof enclosures

## 🔧 **MAINTENANCE REQUIREMENTS**

### **Daily Maintenance:**
- Check system status via dashboard
- Verify camera functionality
- Test barrier operation
- Check LED and buzzer operation

### **Weekly Maintenance:**
- Clean camera lenses
- Check network connectivity
- Verify database backups
- Test UPS battery

### **Monthly Maintenance:**
- Update software packages
- Check power connections
- Verify weatherproofing
- Test emergency procedures

### **Quarterly Maintenance:**
- Complete system testing
- Update security patches
- Check hardware wear
- Review audit logs

## 💰 **COST ESTIMATION**

### **Hardware Costs (Approximate):**
- **Raspberry Pi 4B (8GB)**: $75
- **IP CCTV Cameras (2x)**: $200
- **USB Cameras (2x)**: $100
- **Boom Barriers (2x)**: $800
- **Relay Modules (2x)**: $30
- **LED Strips & Buzzers**: $50
- **Network Equipment**: $150
- **Power Supplies**: $100
- **Enclosures & Cables**: $200
- **UPS Battery**: $150
- **Total Hardware**: ~$1,855

### **Installation Costs:**
- **Professional Installation**: $500-1,000
- **Electrical Work**: $300-500
- **Network Setup**: $200-400
- **Total Installation**: ~$1,000-1,900

### **Total Project Cost**: ~$2,855-3,755

## 🚀 **QUICK START CHECKLIST**

### **Before Installation:**
- [ ] Site survey completed
- [ ] Power requirements calculated
- [ ] Network plan created
- [ ] Safety measures planned
- [ ] Hardware ordered and received

### **During Installation:**
- [ ] Raspberry Pi configured
- [ ] Cameras mounted and tested
- [ ] Barriers installed and tested
- [ ] Network configured
- [ ] Software installed and tested

### **After Installation:**
- [ ] System testing completed
- [ ] Staff training completed
- [ ] Documentation provided
- [ ] Maintenance schedule created
- [ ] Support contact established

## 📞 **SUPPORT AND TROUBLESHOOTING**

### **Common Issues:**
1. **Camera Connection**: Check RTSP URLs and network connectivity
2. **Barrier Control**: Check GPIO connections and relay modules
3. **Database Issues**: Check network connectivity and credentials
4. **Performance Issues**: Check system resources and network latency

### **Support Contacts:**
- **Technical Support**: Available 24/7
- **Hardware Support**: Available during business hours
- **Emergency Support**: Available for critical issues

**Your ANPR parking system is ready for professional deployment!** 🎉