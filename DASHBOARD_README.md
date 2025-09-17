# ANPR Parking System Dashboard

A comprehensive web-based dashboard for monitoring and controlling the ANPR parking system.

## 🌐 Dashboard Features

### **Real-time Monitoring**
- **System Statistics**: Total sessions, active sessions, revenue tracking
- **Live Data Updates**: Auto-refresh every 30 seconds
- **Barrier Status**: Real-time boom barrier status monitoring

### **Manual Controls**
- **Boom Barrier Control**: Open/close barrier manually
- **Session Management**: Complete active sessions manually
- **Permanent Vehicle Management**: Add/remove permanent parking vehicles

### **Data Views**
- **Active Sessions**: Currently parked vehicles with duration
- **Recent Sessions**: Historical parking data
- **Permanent Vehicles**: Authorized vehicles database
- **Payment Logs**: Transaction history and status

## 🚀 Quick Start

### **1. Start the Dashboard**
```bash
# Start dashboard only
python system_dashboard.py

# Or use the startup script
python start_system.py
# Choose option 1 for dashboard only
```

### **2. Access the Dashboard**
- **Desktop Version**: http://localhost:5000
- **Mobile Version**: http://localhost:5000/mobile

### **3. System Requirements**
- Python 3.8+
- Flask and dependencies (see requirements.txt)
- AWS DynamoDB access
- GPIO access (for barrier control)

## 📱 Dashboard Versions

### **Desktop Dashboard** (`/`)
- Full-featured interface
- Large data tables
- Comprehensive controls
- Best for desktop/laptop use

### **Mobile Dashboard** (`/mobile`)
- Touch-optimized interface
- Tabbed navigation
- Compact data display
- Best for mobile devices

## 🎛️ Control Panel Features

### **Boom Barrier Control**
- **Open Barrier**: Manually open the boom barrier
- **Close Barrier**: Manually close the boom barrier
- **Auto-close**: Barrier automatically closes after 15 seconds
- **Status Indicator**: Visual status display

### **Session Management**
- **View Active Sessions**: See currently parked vehicles
- **Complete Sessions**: Manually end parking sessions
- **Duration Tracking**: Real-time duration calculation
- **Revenue Tracking**: Automatic charge calculation

### **Permanent Vehicle Management**
- **Add Vehicles**: Add new permanent parking vehicles
- **Remove Vehicles**: Remove vehicles from permanent access
- **View Database**: See all authorized vehicles
- **Lot Assignment**: Assign vehicles to specific parking lots

## 📊 Data Monitoring

### **System Statistics**
- **Total Sessions**: All-time parking sessions
- **Active Sessions**: Currently parked vehicles
- **Completed Sessions**: Finished sessions today
- **Total Revenue**: Revenue generated
- **Permanent Vehicles**: Authorized vehicles count

### **Real-time Updates**
- Statistics refresh every 30 seconds
- Barrier status updates immediately
- Session data updates on demand
- Payment status tracking

## 🔧 API Endpoints

### **Statistics**
- `GET /api/stats` - Get system statistics
- `GET /api/barrier/status` - Get barrier status

### **Data Retrieval**
- `GET /api/sessions` - Get recent sessions
- `GET /api/active-sessions` - Get active sessions
- `GET /api/permanent-vehicles` - Get permanent vehicles
- `GET /api/payments` - Get payment logs

### **Controls**
- `POST /api/barrier/open` - Open barrier
- `POST /api/barrier/close` - Close barrier
- `POST /api/session/<id>/complete` - Complete session
- `POST /api/vehicle/<id>/add-permanent` - Add permanent vehicle
- `DELETE /api/vehicle/<id>/remove-permanent` - Remove permanent vehicle

## 🛠️ Configuration

### **Environment Variables**
```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Table Names
PARKING_SESSIONS_TABLE=your_sessions_table
PERMANENT_PARKING_TABLE=your_permanent_table
PAYMENT_LOGS_TABLE=your_payments_table

# GPIO Configuration
BOOM_BARRIER_PIN=18
LED_GREEN_PIN=20
LED_RED_PIN=21
BUZZER_PIN=22
```

### **GPIO Pin Configuration**
- **Boom Barrier**: Pin 18 (Output)
- **Green LED**: Pin 20 (Status indicator)
- **Red LED**: Pin 21 (Status indicator)
- **Buzzer**: Pin 22 (Audio feedback)

## 📱 Mobile Optimization

### **Responsive Design**
- Touch-friendly buttons
- Swipe navigation
- Optimized for small screens
- Fast loading

### **Mobile Features**
- Tabbed interface for easy navigation
- Compact data tables
- Touch-optimized controls
- Auto-refresh functionality

## 🔒 Security Features

### **Access Control**
- Local network access only
- No authentication (configure as needed)
- GPIO safety checks
- Error handling and logging

### **Safety Features**
- Barrier auto-close timer
- Status verification
- Error recovery
- Hardware protection

## 🚨 Troubleshooting

### **Common Issues**

#### Dashboard Not Loading
```bash
# Check if Flask is installed
pip install Flask

# Check if port 5000 is available
netstat -an | grep 5000

# Check for errors in console
python system_dashboard.py
```

#### Barrier Not Responding
```bash
# Check GPIO permissions
sudo usermod -a -G gpio $USER

# Check pin configuration
# Verify GPIO pins in .env file

# Test GPIO manually
python -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(18, GPIO.OUT); GPIO.output(18, GPIO.HIGH)"
```

#### Database Connection Issues
```bash
# Test database connection
python test_database_connection.py

# Check AWS credentials
# Verify table names in .env file
```

### **Debug Mode**
```bash
# Enable debug mode
export FLASK_DEBUG=1
python system_dashboard.py
```

## 📈 Performance Optimization

### **Database Optimization**
- Use indexes for frequent queries
- Limit scan operations
- Implement pagination for large datasets
- Cache frequently accessed data

### **Frontend Optimization**
- Minimize API calls
- Use efficient data structures
- Implement lazy loading
- Optimize images and assets

## 🔄 Integration with ANPR System

### **Running Both Systems**
```bash
# Start both dashboard and ANPR system
python start_system.py
# Choose option 3 for both systems
```

### **Data Synchronization**
- Dashboard reads from same database
- Real-time updates via API
- Automatic refresh intervals
- Error handling and recovery

## 📋 Usage Examples

### **Daily Operations**
1. **Morning Setup**: Check barrier status, review overnight sessions
2. **Active Monitoring**: Watch for new vehicles, monitor active sessions
3. **Manual Control**: Open/close barrier as needed
4. **End of Day**: Review daily statistics, complete remaining sessions

### **Emergency Procedures**
1. **Barrier Stuck Open**: Use manual close button
2. **System Error**: Check logs, restart if needed
3. **Database Issues**: Verify connection, check credentials
4. **Hardware Problems**: Check GPIO connections, test manually

## 🎯 Future Enhancements

- [ ] User authentication and roles
- [ ] Real-time notifications
- [ ] Advanced reporting
- [ ] Mobile app integration
- [ ] Multi-location support
- [ ] Automated alerts
- [ ] Data export features
- [ ] Backup and recovery

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review error logs
3. Test individual components
4. Verify configuration settings

---

**🎉 The dashboard provides complete control and monitoring of your ANPR parking system!**



