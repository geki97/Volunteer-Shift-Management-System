# 🌐 Deployment Guide - Volunteer Management System

## Quick Deploy Options

### 1. **Heroku (Easiest for Flask)**

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create Procfile in project root
# Content:
# web: gunicorn web.check_in_app:app
# clock: python scripts/reminder_daemon.py

# Create app
heroku create your-app-name

# Add buildpack for Python
heroku buildpacks:add heroku/python

# Deploy
git push heroku master

# View logs
heroku logs --tail
```

### 2. **Vercel + Flask (Serverless)**

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Follow prompts - will auto-detect Python project
```

### 3. **GitHub Pages + Static Site (Read-Only)**

Perfect for displaying upcoming shifts and volunteer info:

```bash
# Build static site from shift data
python scripts/csv_to_json_converter.py

# Deploy to GitHub Pages
git branch -D gh-pages
git checkout --orphan gh-pages
# Commit static files
git push origin gh-pages
```

---

## Environment Setup

### Required Environment Variables

Create `.env` file in project root:

```env
# Flask Configuration
FLASK_SECRET_KEY=your-super-secret-key-min-32-chars
FLASK_PORT=5000
FLASK_DEBUG=False

# Database (Optional - system works with JSON fallback)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Email (SendGrid)
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@foodbank.org

# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890

# QR Code Security
QR_SIGNING_KEY=your-secure-random-key

# Timezone
TIMEZONE=Europe/Dublin

# App URL (for QR code links)
APP_BASE_URL=https://your-deployed-url.com
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "web/check_in_app.py"]
```

### Build and Run

```bash
# Build image
docker build -t volunteer-system .

# Run container
docker run -p 5000:5000 -e APP_BASE_URL=http://localhost:5000 volunteer-system
```

---

## AWS Deployment

### Using AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init

# Create environment
eb create volunteer-system-env

# Deploy
eb deploy

# View app
eb open
```

---

## DigitalOcean App Platform

1. Fork/Clone repository to your GitHub
2. Go to https://cloud.digitalocean.com/apps
3. Click "Create App"
4. Select GitHub repository
5. Configure:
   - **Run Command**: `gunicorn web.check_in_app:app`
   - **HTTP Port**: 5000
6. Add environment variables from `.env`
7. Deploy!

---

## Monitoring & Logs

### Check System Health

```bash
python scripts/check_status.py
```

Output shows:
- ✅ AppFlowy exports status
- 💾 Database connectivity
- 📊 Recent activity
- 🏥 System health status

### View Recent Logs

```bash
# Windows
Get-Content logs\volunteer_system_*.log -Tail 50

# macOS/Linux
tail -50 logs/volunteer_system_*.log
```

---

## Custom Domain Setup

### Using Namecheap / GoDaddy

1. Point DNS to your hosting provider
2. Update `APP_BASE_URL` in environment variables
3. Configure SSL certificate (automatic on most platforms)

Example:
```env
APP_BASE_URL=https://volunteer-checkin.yourorganization.org
```

---

## Performance Tips

### 1. Enable Caching
```python
# In config/settings.py
CACHE_ENABLED = True
CACHE_TIMEOUT = 300  # 5 minutes
```

### 2. Database Indexing
```sql
-- Add indexes for faster lookups
CREATE INDEX idx_volunteer_id ON volunteers(id);
CREATE INDEX idx_shift_id ON shifts(id);
```

### 3. CDN for Static Files
```python
# In settings
STATIC_CDN_URL = "https://cdnjs.cloudflare.com/ajax/libs/"
```

---

## Security Checklist

- [ ] Set `FLASK_DEBUG=False`
- [ ] Use strong `FLASK_SECRET_KEY` (32+ characters)
- [ ] Enable HTTPS on production domain
- [ ] Set `SameSite=Strict` for cookies
- [ ] Add rate limiting (already implemented)
- [ ] Regular security audits
- [ ] Keep dependencies updated: `pip install --upgrade -r requirements.txt`

---

## Backing Up Data

### Backup JSON Files

```bash
# Create backup
cp -r appflowy_exports appflowy_exports.backup.2026-04-17
```

### Backup Database

```python
# Run backup script
python scripts/backup_database.py
```

---

## Scaling for Production

### Load Balancing

For high traffic, use:
- **NGINX** as reverse proxy
- **Gunicorn** with multiple workers: `gunicorn -w 4 web.check_in_app:app`
- **Redis** for session management

### Configuration

```nginx
upstream flask_app {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://flask_app;
    }
}
```

---

## CI/CD Pipeline (GitHub Actions)

### .github/workflows/deploy.yml

```yaml
name: Deploy to Production

on:
  push:
    branches: [master]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.13
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: python verify_iteration3_fixes.py
      
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: "your-app-name"
          heroku_email: "your@email.com"
```

---

## Troubleshooting Deployment

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000
# Kill it
kill -9 <PID>
```

### Module Not Found
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Database Connection Issues
The system automatically falls back to JSON files if database is unavailable. Check:
```bash
python scripts/check_status.py
```

---

## Cost Estimates

| Platform | Cost | Suitable For |
|----------|------|-------------|
| Heroku Free | Free | Development/Testing |
| Vercel | Free tier available | Static + Serverless |
| DigitalOcean | $5/month | Small production |
| AWS | Pay-as-you-go | Enterprise |
| Heroku Paid | ~$50+/month | Production |

---

## Support & Documentation

- **Flask Docs**: https://flask.palletsprojects.com/
- **Heroku Docs**: https://devcenter.heroku.com/
- **Security Guide**: See SECURITY_AUDIT_REPORT.md

---

**Ready to Deploy?** Choose a platform above and follow the steps! 🚀
