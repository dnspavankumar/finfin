# 🚀 Finand Deployment Guide

## Overview
This guide covers multiple deployment options for your Finand email assistant, from simple cloud hosting to enterprise solutions.

---

## 🌟 **Option 1: Streamlit Cloud (Recommended - Free & Easy)**

### **Pros:**
- ✅ **Free hosting**
- ✅ **Easy deployment**
- ✅ **Automatic updates from GitHub**
- ✅ **Built-in SSL**
- ✅ **No server management**

### **Steps:**

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial Finand deployment"
   git branch -M main
   git remote add origin https://github.com/yourusername/finand.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file: `streamlit_app_v2.py`
   - Click "Deploy"

3. **Add Secrets:**
   - In Streamlit Cloud dashboard, go to your app
   - Click "Settings" → "Secrets"
   - Add your environment variables:
   ```toml
   AWS_ACCESS_KEY_ID = "your_access_key"
   AWS_SECRET_ACCESS_KEY = "your_secret_key"
   AWS_REGION = "us-east-1"
   ```

### **Important Notes:**
- Gmail credentials (`credentials.json`, `token.json`) need special handling
- Consider using OAuth flow or service account for production

---

## 🐳 **Option 2: Docker + Cloud Platforms**

### **Create Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the application
CMD ["streamlit", "run", "streamlit_app_v2.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### **Deploy to Various Platforms:**

#### **Heroku:**
```bash
# Install Heroku CLI
heroku create your-finand-app
heroku container:push web
heroku container:release web
heroku config:set AWS_ACCESS_KEY_ID=your_key
heroku config:set AWS_SECRET_ACCESS_KEY=your_secret
```

#### **Google Cloud Run:**
```bash
gcloud run deploy finand \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### **AWS ECS/Fargate:**
```bash
# Build and push to ECR
aws ecr create-repository --repository-name finand
docker build -t finand .
docker tag finand:latest your-account.dkr.ecr.region.amazonaws.com/finand:latest
docker push your-account.dkr.ecr.region.amazonaws.com/finand:latest
```

---

## ☁️ **Option 3: Traditional VPS (DigitalOcean, Linode, etc.)**

### **Server Setup:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip nginx -y

# Clone your repository
git clone https://github.com/yourusername/finand.git
cd finand

# Install dependencies
pip3 install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/finand.service
```

### **Systemd Service File:**
```ini
[Unit]
Description=Finand Email Assistant
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/finand
Environment=PATH=/home/ubuntu/.local/bin
ExecStart=/usr/bin/python3 -m streamlit run streamlit_app_v2.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
```

### **Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 🔒 **Security Considerations**

### **Environment Variables:**
Create a `.env` file (never commit this):
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### **Gmail Authentication:**
For production, consider:
1. **Service Account:** Use Google Service Account instead of personal OAuth
2. **Domain-wide Delegation:** For organization-wide access
3. **Secure Storage:** Store credentials in cloud secret managers

### **AWS Security:**
1. **IAM Roles:** Use minimal permissions
2. **VPC:** Deploy in private subnets
3. **Secrets Manager:** Store credentials securely

---

## 📱 **Option 4: Mobile-Friendly PWA**

### **Add PWA Support:**
Create `streamlit_config.toml`:
```toml
[server]
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#000000"
```

---

## 🚀 **Quick Deploy Commands**

### **Streamlit Cloud (Easiest):**
```bash
# 1. Push to GitHub
git add . && git commit -m "Deploy Finand" && git push

# 2. Go to share.streamlit.io and deploy
```

### **Docker Local Test:**
```bash
docker build -t finand .
docker run -p 8501:8501 --env-file .env finand
```

### **Heroku:**
```bash
heroku create finand-app
git push heroku main
```

---

## 🔧 **Troubleshooting**

### **Common Issues:**
1. **Gmail Auth:** Use service account for production
2. **AWS Permissions:** Ensure Bedrock access is enabled
3. **Memory:** Increase container memory for large email processing
4. **Timeout:** Set appropriate timeout values for email loading

### **Performance Tips:**
1. **Caching:** Use `@st.cache_data` for email loading
2. **Pagination:** Limit email processing batches
3. **CDN:** Use CloudFlare for static assets
4. **Database:** Consider PostgreSQL for larger datasets

---

## 📊 **Monitoring & Analytics**

### **Add Monitoring:**
```python
# Add to your Streamlit app
import logging
logging.basicConfig(level=logging.INFO)

# Track usage
st.session_state.analytics = {
    'questions_asked': 0,
    'emails_processed': 0,
    'deployment_time': datetime.now()
}
```

---

## 💰 **Cost Estimates**

| Platform | Cost | Pros | Cons |
|----------|------|------|------|
| Streamlit Cloud | **Free** | Easy, no setup | Limited resources |
| Heroku | **$7/month** | Simple deployment | Can be slow |
| DigitalOcean | **$5-20/month** | Full control | Requires setup |
| AWS/GCP | **$10-50/month** | Scalable | Complex setup |

---

## 🎯 **Recommended Deployment Path**

1. **Start:** Streamlit Cloud (free, easy)
2. **Scale:** Docker + Cloud Run/Heroku
3. **Enterprise:** AWS ECS + RDS + CloudFront

Choose based on your needs, budget, and technical expertise!