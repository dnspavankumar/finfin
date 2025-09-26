#!/usr/bin/env python3
"""
Test AWS Bedrock with Amazon Titan model (often pre-enabled)
"""
import boto3
import json
from dotenv import load_dotenv
import os

def test_titan_model():
    """Test with Amazon Titan Text model"""
    
    load_dotenv()
    
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    print("🔍 Testing Amazon Titan Model...")
    print(f"Region: {aws_region}")
    print("-" * 50)
    
    try:
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Test with Amazon Titan
        test_message = {
            "inputText": "Hello! Please respond with 'AWS Bedrock Titan is working!'",
            "textGenerationConfig": {
                "maxTokenCount": 100,
                "temperature": 0.3
            }
        }
        
        print("📡 Calling Amazon Titan...")
        response = bedrock_client.invoke_model(
            modelId="amazon.titan-text-express-v1",
            body=json.dumps(test_message),
            contentType="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        if 'results' in response_body and response_body['results']:
            result = response_body['results'][0]['outputText']
            print("✅ SUCCESS! Titan Response:")
            print(f"   {result}")
            return True
        else:
            print("❌ ERROR: Empty response from Titan")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_titan_model()
    
    if success:
        print("\n🎉 Amazon Titan is working! You can use this as a fallback.")
        print("   But Claude models are better for your Gmail Assistant.")
        print("   Please still enable Claude access in Bedrock console.")
    else:
        print("\n🔧 Please enable model access in AWS Bedrock console.")