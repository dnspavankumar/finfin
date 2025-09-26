# 🚀 Quick Deploy to Streamlit Cloud

## Step-by-Step Instructions

### 1. **Prepare Your Repository**
```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit your changes
git commit -m "Initial Finand deployment"

# Create main branch
git branch -M main
```

### 2. **Push to GitHub**
```bash
# Add your GitHub repository (replace with your username)
git remote add origin https://github.com/YOUR_USERNAME/finand.git

# Push to GitHub
git push -u origin main
```

### 3. **Deploy on Streamlit Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select your repository: `YOUR_USERNAME/finand`
5. Set **Main file path**: `streamlit_app_v2.py`
6. Click **"Deploy!"**

### 4. **Add Your Secrets**

In your Streamlit Cloud app dashboard:

1. Click on your app name
2. Go to **"Settings"** → **"Secrets"**
3. Add the following secrets:

```toml
# AWS Configuration
AWS_ACCESS_KEY_ID = "your_aws_access_key_id_here"
AWS_SECRET_ACCESS_KEY = "your_aws_secret_access_key_here"
AWS_REGION = "us-east-1"
```

### 5. **Handle Gmail Authentication**

Since Gmail requires `credentials.json` and `token.json`, you have two options:

#### **Option A: Upload Files (Simple)**
1. In Streamlit Cloud, go to **"Settings"** → **"Secrets"**
2. Add your credentials as base64 encoded strings:

```bash
# On your local machine, encode the files
base64 credentials.json
base64 token.json
```

Then add to secrets:
```toml
GMAIL_CREDENTIALS_B64 = "your_base64_encoded_credentials_json"
GMAIL_TOKEN_B64 = "your_base64_encoded_token_json"
```

#### **Option B: Use Service Account (Recommended)**
1. Create a Google Service Account
2. Download the service account key
3. Add it to secrets as base64 encoded string

### 6. **Update Your Code for Deployment**

Add this to the top of `streamlit_app_v2.py`:

```python
import base64
import json
import os

# Handle Gmail credentials in cloud deployment
def setup_gmail_credentials():
    """Setup Gmail credentials for cloud deployment"""
    
    # Check if running in Streamlit Cloud
    if "GMAIL_CREDENTIALS_B64" in st.secrets:
        # Decode and save credentials
        creds_b64 = st.secrets["GMAIL_CREDENTIALS_B64"]
        creds_json = base64.b64decode(creds_b64).decode('utf-8')
        
        with open('credentials.json', 'w') as f:
            f.write(creds_json)
    
    if "GMAIL_TOKEN_B64" in st.secrets:
        # Decode and save token
        token_b64 = st.secrets["GMAIL_TOKEN_B64"]
        token_json = base64.b64decode(token_b64).decode('utf-8')
        
        with open('token.json', 'w') as f:
            f.write(token_json)

# Call this function at the start of your app
setup_gmail_credentials()
```

### 7. **Your App is Live! 🎉**

Your Finand app will be available at:
`https://YOUR_USERNAME-finand-streamlit-app-v2-HASH.streamlit.app`

### 8. **Custom Domain (Optional)**

To use a custom domain:
1. Upgrade to Streamlit Cloud Pro
2. Add your domain in settings
3. Update DNS records

---

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **Import Errors:**
   - Make sure all dependencies are in `requirements.txt`
   - Check Python version compatibility

2. **Gmail Authentication:**
   - Verify credentials are properly base64 encoded
   - Check file permissions and paths

3. **AWS Bedrock Access:**
   - Ensure your AWS credentials have Bedrock permissions
   - Verify the model access is enabled

4. **Memory Issues:**
   - Reduce email processing batch size
   - Use `@st.cache_data` for expensive operations

### **Logs and Debugging:**
- Check logs in Streamlit Cloud dashboard
- Use `st.write()` for debugging
- Add error handling with try/catch blocks

---

## 🎯 **Next Steps**

1. **Monitor Usage:** Check Streamlit Cloud analytics
2. **Custom Domain:** Set up your own domain
3. **Performance:** Optimize for faster loading
4. **Features:** Add more email analysis capabilities

Your Finand app is now deployed and accessible worldwide! 🌍