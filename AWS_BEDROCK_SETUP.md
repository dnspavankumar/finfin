# AWS Bedrock Setup Guide

## 🚀 Quick Setup Instructions

Your Gmail Assistant has been successfully migrated from Groq to AWS Bedrock! Here's how to complete the setup:

### 1. Update Your .env File

Replace the placeholder values in your `.env` file with your actual AWS credentials:

```env
# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_actual_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_actual_aws_secret_access_key
AWS_REGION=us-east-1
```

### 2. AWS Bedrock Model Access

Make sure you have access to Claude 3 Sonnet in your AWS account:

1. Go to AWS Bedrock Console
2. Navigate to "Model access" in the left sidebar
3. Request access to "Anthropic Claude 3 Sonnet" if not already enabled
4. Wait for approval (usually instant for most accounts)

### 3. AWS Credentials Options

You can set up AWS credentials in several ways:

#### Option A: Environment Variables (Recommended)
Update your `.env` file as shown above.

#### Option B: AWS CLI Configuration
```bash
aws configure
```

#### Option C: IAM Role (for EC2 instances)
If running on EC2, attach an IAM role with Bedrock permissions.

### 4. Required AWS Permissions

Your AWS user/role needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        }
    ]
}
```

### 5. Test Your Setup

Run your application and ask a question to test the Bedrock integration!

## 🔧 What Changed

- ✅ Replaced Groq API with AWS Bedrock
- ✅ Updated to use Claude 3 Sonnet model
- ✅ Maintained all existing functionality
- ✅ Added proper error handling for AWS calls
- ✅ Updated requirements.txt

## 🎯 Benefits of AWS Bedrock

- **Enterprise-grade**: Built for production workloads
- **Better Privacy**: Your data stays in your AWS account
- **Multiple Models**: Easy to switch between different AI models
- **Cost Effective**: Pay only for what you use
- **Integration**: Seamless integration with other AWS services

## 🚨 Troubleshooting

If you encounter issues:

1. **Check AWS Credentials**: Ensure your credentials are correct
2. **Verify Region**: Make sure Bedrock is available in your region
3. **Model Access**: Confirm Claude 3 Sonnet access is enabled
4. **Permissions**: Verify your IAM permissions include `bedrock:InvokeModel`

Your Gmail Assistant is now powered by AWS Bedrock! 🎉