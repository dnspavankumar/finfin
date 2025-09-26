#!/usr/bin/env python3
"""
Quick test script to verify AWS Bedrock connection
"""
import boto3
import json
from dotenv import load_dotenv
import os

def test_bedrock_connection():
    """Test AWS Bedrock connection with current credentials"""
    
    # Load environment variables
    load_dotenv()
    
    # Get AWS credentials
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_session_token = os.getenv('AWS_SESSION_TOKEN')
    aws_region = os.getenv('AWS_REGION', 'sa-east-1')
    
    print("🔍 Testing AWS Bedrock Connection...")
    print(f"Region: {aws_region}")
    print(f"Access Key ID: {aws_access_key_id[:10]}..." if aws_access_key_id else "Access Key ID: Not set")
    print(f"Secret Key: {'Set' if aws_secret_access_key else 'Not set'}")
    print(f"Session Token: {'Set' if aws_session_token else 'Not set'}")
    print("-" * 50)
    
    try:
        # Create Bedrock client
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )
        
        # Test with a simple message
        test_message = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! Please respond with 'AWS Bedrock is working correctly!'"
                }
            ]
        }
        
        print("📡 Calling AWS Bedrock...")
        
        # Try Titan first (you have access), then Claude models
        try:
            print("   Trying Amazon Titan Text Express...")
            titan_message = {
                "inputText": "Hello! Please respond with 'AWS Bedrock is working correctly!'",
                "textGenerationConfig": {
                    "maxTokenCount": 100,
                    "temperature": 0.3
                }
            }
            
            response = bedrock_client.invoke_model(
                modelId="amazon.titan-text-express-v1",
                body=json.dumps(titan_message),
                contentType="application/json"
            )
            model_used = "amazon.titan-text-express-v1"
            
            # Parse Titan response
            response_body = json.loads(response['body'].read())
            if 'results' in response_body and response_body['results']:
                result = response_body['results'][0]['outputText']
                print("✅ SUCCESS! Bedrock Response:")
                print(f"   Model used: {model_used}")
                print(f"   Response: {result}")
                return True
            
        except Exception as titan_error:
            print(f"   ❌ Titan failed: {str(titan_error)}")
            
            # Fallback to Claude models
            models_to_try = [
                "anthropic.claude-3-haiku-20240307-v1:0",
                "anthropic.claude-3-sonnet-20240229-v1:0",
                "anthropic.claude-instant-v1"
            ]
            
            for model_id in models_to_try:
                try:
                    print(f"   Trying model: {model_id}")
                    response = bedrock_client.invoke_model(
                        modelId=model_id,
                        body=json.dumps(test_message),
                        contentType="application/json"
                    )
                    model_used = model_id
                    break
                except Exception as model_error:
                    if "You don't have access to the model" in str(model_error):
                        print(f"   ❌ No access to {model_id}")
                        continue
                    else:
                        raise model_error
            
            if not response:
                raise Exception("No accessible models found.")
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and response_body['content']:
            result = response_body['content'][0]['text']
            print("✅ SUCCESS! Bedrock Response:")
            print(f"   Model used: {model_used}")
            print(f"   Response: {result}")
            return True
        else:
            print("❌ ERROR: Empty response from Bedrock")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        
        # Provide helpful error messages
        if "InvalidSignatureException" in str(e):
            print("\n💡 SOLUTION: Your AWS Secret Access Key is incorrect or missing.")
            print("   Please check your AWS credentials in the .env file.")
        elif "UnauthorizedOperation" in str(e) or "AccessDenied" in str(e):
            print("\n💡 SOLUTION: Your AWS credentials don't have permission to access Bedrock.")
            print("   Make sure your AWS user/role has 'bedrock:InvokeModel' permission.")
        elif "ExpiredToken" in str(e):
            print("\n💡 SOLUTION: Your AWS session token has expired.")
            print("   Please generate new temporary credentials from AWS Console.")
        elif "NoCredentialsError" in str(e):
            print("\n💡 SOLUTION: AWS credentials are not properly configured.")
            print("   Please update your .env file with valid AWS credentials.")
        
        return False

if __name__ == "__main__":
    success = test_bedrock_connection()
    
    if success:
        print("\n🎉 Your AWS Bedrock integration is working perfectly!")
        print("   You can now run your Gmail Assistant application.")
    else:
        print("\n🔧 Please fix the credentials issue and try again.")
        print("\n📋 To get your AWS credentials:")
        print("   1. Go to AWS Console → IAM → Users → Your User → Security Credentials")
        print("   2. Create Access Key if you don't have one")
        print("   3. Copy Access Key ID and Secret Access Key to your .env file")
        print("   4. Make sure your user has Bedrock permissions")