# 📱 Volunteer Shift Management System - Phone QR Code Setup Guide

## Quick Start: Using QR Codes on Your Phone

### Prerequisites
- Python 3.13+ 
- Virtual environment
- Flask running on localhost:5000 (or deployed server)

### Installation

```bash
# Clone the repository
git clone https://github.com/geki97/Volunteer-Shift-Management-System.git
cd Volunteer-Shift-Management-System

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows
# or: source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Starting the Web Server

```bash
# Navigate to project directory
cd volunteer-management-system

# Run the Flask web server
python web/check_in_app.py
```

Server will start on `http://localhost:5000`

---

## 📞 Using QR Codes on Your Phone

### Option 1: Local Network Access (Recommended for Development)

**On Your Computer:**
```bash
# Find your computer's local IP address
# Windows: ipconfig
# macOS/Linux: ifconfig
```

**On Your Phone:**
1. Connect to the same WiFi network as your computer
2. Open your phone's native camera or QR scanner app
3. Point camera at the QR code (from `qr_codes/` folder or printed QR)
4. Tap the notification that appears
5. Your phone will navigate to the check-in page

**URL Format:** `http://<YOUR-COMPUTER-IP>:5000/check-in/token/<TOKEN>`

---

### Option 2: Deploy to GitHub Pages / Vercel (Production)

For long-term use, deploy to a public server:

#### Deploy to Vercel (Free)
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy Flask app
vercel
```

#### Deploy to Heroku
```bash
# Install Heroku CLI
# Create Procfile with: web: python web/check_in_app.py

# Deploy
heroku create
git push heroku master
```

---

## 🔧 QR Code Details

### Generate QR Code for a Shift

```python
from scripts.security.qr_secure import SecureQRCode

# Generate QR code with secure token
qr_path, token = SecureQRCode.generate_shift_qr_code(
    shift_id="food_distribution_-_city_centre",
    shift_name="Food Distribution - City Centre",
    user_id="sarah_murphy"  # Optional: for individual check-in
)

# QR code saved to: qr_codes/[shift_name]_[timestamp]_[user].png
```

### QR Code Contents (Secured)

The QR code contains an encrypted token with:
- Shift ID
- User ID (volunteer)
- Timestamp
- HMAC-SHA256 signature (prevents tampering)
- Expiration (24 hours by default)

**Security Features:**
✅ Token signed with HMAC-SHA256
✅ Cannot be forged without signing key
✅ Automatic expiration
✅ Base64 encoded for QR compatibility

---

## 📋 Available Shifts

The system includes 4 shifts with assigned volunteers:

| Shift Name | Date | Location | Volunteers |
|-----------|------|----------|-----------|
| Food Distribution - City Centre | Jan 30, 2026 | O'Connell Street | 5 volunteers |
| Evening Delivery Run - Northside | Jan 31, 2026 | Various Northside | 3 volunteers |
| Weekend Food Prep | Jan 2, 2026 | Main Kitchen | 6 volunteers |
| Morning Stock Check & Inventory | Mar 23, 2026 | Main Warehouse | 4 volunteers |

---

## ✍️ How to Use: Step-by-Step

### For Coordinators (Desktop)

1. Generate QR codes for each shift:
   ```bash
   python scripts/security/qr_secure.py
   ```

2. Print or display QR codes to volunteers

3. Monitor check-ins:
   ```bash
   python scripts/check_status.py
   ```

### For Volunteers (Phone)

1. **Receive QR Code** (printed or via email)
2. **Open Camera** on your phone
3. **Scan QR Code** 
4. **Tap Link** when prompted
5. **Select Your Name** from the list
6. **Confirm Check-In** ✅

---

## 📧 Email Integration with QR Codes

Send shift reminders with QR codes embedded:

```bash
python test_email_with_qr.py
```

Emails include:
- Shift details (date, time, location)
- Embedded QR code (image)
- Check-in link

---

## 🌐 Network Configuration

### For Phone Access on Local WiFi

**Edit `config/settings.py`:**
```python
APP_BASE_URL = "http://YOUR-COMPUTER-IP:5000"  # For local network
# or
APP_BASE_URL = "https://your-deployment-url.com"  # For production
```

### Port Forwarding (Optional)

If you want external access:
1. Forward port 5000 on your router to your computer
2. Use your public IP: `http://YOUR-PUBLIC-IP:5000`
3. ⚠️ **Security Note**: Use HTTPS and strong authentication in production

---

## 🔐 Security

### Disable Debug Mode in Production
```python
# config/settings.py
FLASK_DEBUG = False  # Always False in production
```

### Use Environment Variables
```bash
# Create .env file
SENDGRID_API_KEY=your_api_key
QR_SIGNING_KEY=your_secure_key
FLASK_SECRET_KEY=your_secret_key
```

---

## 📊 Data Files

The system uses local JSON files for volunteers and shifts:

- **Volunteers**: `appflowy_exports/volunteers.json`
- **Shifts**: `appflowy_exports/shifts.json`

These files can be synced from AppFlowy:
```bash
python scripts/appflowy_sync_manager.py
```

---

## ✅ Testing

### Test QR Check-In Flow
```bash
python test_qr_fresh.py
```

### Verify All Systems
```bash
python verify_iteration3_fixes.py
```

### Test Email with QR
```bash
python test_email_with_qr.py
```

---

## 🐛 Troubleshooting

### QR Code Won't Scan on Phone

**Solution 1:** Increase phone brightness and stable positioning
**Solution 2:** Check QR file exists: `qr_codes/` folder
**Solution 3:** Regenerate QR code with fresh token

### Check-In Page Doesn't Load

**Solution 1:** Verify server is running on `localhost:5000`
**Solution 2:** Check network connectivity between phone and computer
**Solution 3:** Use correct IP address for remote access

### Shift Information Not Loading

**Solution 1:** Verify `shifts.json` exists and has correct data
**Solution 2:** Check shift ID matches exactly (case-sensitive)
**Solution 3:** Run health check: `python scripts/check_status.py`

---

## 📱 Browser Compatibility

✅ Works on:
- Chrome/Chromium
- Safari
- Firefox
- Edge
- Mobile Chrome/Safari

✅ Tested on:
- iOS 15+
- Android 10+

---

## 📚 Files Structure

```
volunteer-management-system/
├── web/                          # Flask web app
│   ├── check_in_app.py          # Main Flask app
│   └── templates/               # HTML templates
│       ├── check_in_token.html  # QR scan result page
│       ├── check_in.html        # Volunteer selection
│       └── error.html           # Error pages
├── scripts/
│   ├── security/
│   │   └── qr_secure.py         # QR generation & validation
│   └── utils/
│       ├── email_service_enhanced.py  # Email with QR
│       └── database.py          # DB operations
├── appflowy_exports/
│   ├── volunteers.json          # Volunteer data
│   └── shifts.json              # Shift data
└── qr_codes/                    # Generated QR codes
```

---

## 🚀 Next Steps

1. **Clone the repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Start server**: `python web/check_in_app.py`
4. **Generate QR codes**: Run the test script or generate manually
5. **Test on phone**: Connect to local WiFi and scan QR code
6. **Deploy to production** (optional): Follow Vercel/Heroku guide above

---

## 📞 Support

For issues or questions:
1. Check system health: `python scripts/check_status.py`
2. View logs: `logs/volunteer_system_*.log`
3. Run verification suite: `python verify_iteration3_fixes.py`

---

**Last Updated:** April 17, 2026  
**Repository:** https://github.com/geki97/Volunteer-Shift-Management-System.git
