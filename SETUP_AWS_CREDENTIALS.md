# 🔑 AWS Credentials Setup Guide

## Quick Fix for Connection Error

Your connection error is due to invalid/expired AWS credentials. Here's how to fix it:

### Option 1: Get Permanent AWS Credentials (Recommended)

1. **Go to AWS Console**: https://console.aws.amazon.com/
2. **Navigate to IAM**: Services → IAM → Users
3. **Select your user** (or create one if needed)
4. **Go to Security Credentials tab**
5. **Create Access Key**:
   - Click "Create access key"
   - Choose "Application running outside AWS"
   - Copy both Access Key ID and Secret Access Key

6. **Update your .env file**:
```env
AWS_ACCESS_KEY_ID=AKIA...your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_REGION=us-east-1
```

### Option 2: Use AWS CLI (Alternative)

If you have AWS CLI installed:
```bash
aws configure
```
Then remove the AWS credentials from .env file (it will use CLI credentials automatically).

### Option 3: Get Fresh Temporary Credentials

If you prefer temporary credentials:
1. Go to AWS Console
2. Click your username (top right) → Security Credentials
3. Create temporary credentials
4. Update .env with all three values:
```env
AWS_ACCESS_KEY_ID=ASIA...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
AWS_REGION=us-east-1
```

## Required Permissions

Make sure your AWS user has these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
```

## Enable Bedrock Models

1. Go to AWS Bedrock Console
2. Click "Model access" in left sidebar
3. Request access to "Anthropic Claude 3 Sonnet"
4. Wait for approval (usually instant)

## Test Your Setup

Run this command to test:
```bash
python test_bedrock.py
```

You should see: ✅ SUCCESS! Bedrock Response

## Troubleshooting

- **Invalid token**: Your credentials are wrong/expired
- **Access denied**: You need Bedrock permissions
- **Model not found**: Enable Claude 3 Sonnet in Bedrock console
- **Region error**: Make sure Bedrock is available in your region

Once you update your credentials, your Gmail Assistant will work perfectly with AWS Bedrock! 🚀