"""
Production-ready version of RAG_Gmail with proper database storage
"""
# Standard library imports
import base64
from datetime import datetime, timedelta, timezone
from email import utils
import os
import json
import traceback
import pickle
from typing import List, Dict, Any, Optional

# Third-party library imports
from bs4 import BeautifulSoup
import dateutil.parser
from dotenv import load_dotenv
import numpy as np
import pyttsx3
import speech_recognition as sr
from tzlocal import get_localzone
import boto3
from sqlalchemy import create_engine, text
import streamlit as st

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# Local imports
from database_config import db_config

# Parameters
EMBEDDING_DIM = 1536
K = 25  # Number of Fetched Emails for Vector Search

# Setting up AWS Bedrock client
load_dotenv(override=True)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize Bedrock client with optional session token support
bedrock_kwargs = {
    'service_name': 'bedrock-runtime',
    'region_name': AWS_REGION,
    'aws_access_key_id': AWS_ACCESS_KEY_ID,
    'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
}

# Add session token only if it exists (for temporary credentials)
if AWS_SESSION_TOKEN:
    bedrock_kwargs['aws_session_token'] = AWS_SESSION_TOKEN

bedrock_client = boto3.client(**bedrock_kwargs)

def call_bedrock_claude(messages, max_tokens=1000, temperature=0.3):
    """Call AWS Bedrock Claude model with conversation messages"""
    try:
        # Convert messages to Claude format
        system_message = ""
        conversation = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Prepare the request body for Claude
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": conversation
        }
        
        # Add system message if present
        if system_message:
            body["system"] = system_message
        
        # Call Bedrock - try Claude 3 Haiku first (often pre-approved)
        try:
            response = bedrock_client.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",  # Using Claude 3 Haiku
                body=json.dumps(body),
                contentType="application/json"
            )
        except Exception as e:
            if "You don't have access to the model" in str(e):
                # Fallback to Claude 3 Sonnet if Haiku fails
                response = bedrock_client.invoke_model(
                    modelId="anthropic.claude-3-sonnet-20240229-v1:0",  # Using Claude 3 Sonnet
                    body=json.dumps(body),
                    contentType="application/json"
                )
            else:
                raise e
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and response_body['content']:
            return response_body['content'][0]['text']
        else:
            return "I apologize, but I received an empty response from the AI model."
            
    except Exception as e:
        print(f"Error calling Bedrock: {str(e)}")
        return f"I apologize, but there was an error connecting to AWS Bedrock: {str(e)}"

class EmailDatabase:
    """Database manager for email storage and retrieval"""
    
    def __init__(self):
        self.engine = db_config.get_engine()
        db_config.init_tables()
    
    def store_email(self, email_data: Dict[str, Any]) -> bool:
        """Store email in database"""
        try:
            with self.engine.connect() as conn:
                # Check if email already exists
                result = conn.execute(text("""
                    SELECT id FROM emails WHERE email_id = :email_id
                """), {"email_id": email_data['email_id']})
                
                if result.fetchone():
                    return False  # Email already exists
                
                # Insert new email
                conn.execute(text("""
                    INSERT INTO emails (email_id, sender, subject, date_sent, body_text, summary, embedding)
                    VALUES (:email_id, :sender, :subject, :date_sent, :body_text, :summary, :embedding)
                """), {
                    "email_id": email_data['email_id'],
                    "sender": email_data['sender'],
                    "subject": email_data['subject'],
                    "date_sent": email_data['date_sent'],
                    "body_text": email_data['body_text'],
                    "summary": email_data['summary'],
                    "embedding": pickle.dumps(email_data['embedding'])
                })
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error storing email: {str(e)}")
            return False
    
    def search_emails(self, query_embedding: np.ndarray, k: int = K) -> List[str]:
        """Search for similar emails using vector similarity"""
        try:
            with self.engine.connect() as conn:
                # Get all emails with embeddings
                result = conn.execute(text("""
                    SELECT summary, embedding FROM emails 
                    WHERE embedding IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT 100
                """))
                
                emails = []
                similarities = []
                
                for row in result:
                    summary = row[0]
                    embedding_bytes = row[1]
                    
                    if embedding_bytes:
                        stored_embedding = pickle.loads(embedding_bytes)
                        # Calculate cosine similarity
                        similarity = np.dot(query_embedding.flatten(), stored_embedding.flatten())
                        similarities.append((similarity, summary))
                
                # Sort by similarity and return top k
                similarities.sort(reverse=True, key=lambda x: x[0])
                return [summary for _, summary in similarities[:k]]
                
        except Exception as e:
            print(f"Error searching emails: {str(e)}")
            return ["No relevant emails found due to search error."]
    
    def get_email_count(self) -> int:
        """Get total number of stored emails"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM emails"))
                return result.fetchone()[0]
        except:
            return 0
    
    def get_last_update(self) -> Optional[datetime]:
        """Get timestamp of last email update"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT value FROM app_metadata WHERE key = 'last_email_check'
                """))
                row = result.fetchone()
                if row:
                    return datetime.fromisoformat(row[0])
                return None
        except:
            return None
    
    def update_last_check(self, timestamp: datetime):
        """Update last email check timestamp"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO app_metadata (key, value, updated_at)
                    VALUES ('last_email_check', :timestamp, CURRENT_TIMESTAMP)
                    ON CONFLICT (key) DO UPDATE SET 
                        value = :timestamp, 
                        updated_at = CURRENT_TIMESTAMP
                """), {"timestamp": timestamp.isoformat()})
                conn.commit()
        except Exception as e:
            print(f"Error updating last check: {str(e)}")

# Global database instance
email_db = EmailDatabase()

def summerize_email(mail_from, mail_cc, mail_subject, mail_date, mail_body):
    """Summarize email using AI"""
    try:
        system_content = '''
Summarize the given Email in the following format, keep it brief but don't lose much information:

OUTPUT FORMAT:
<Email Start>
Date and Time:  (format: dd-MMM-yyyy HH h:mmtt [with time zone])
Sender: 
CC:
Subject:
Email Context: 
<Email End>
'''

        prompt = f'''
The email is the following: 

date and time: {mail_date}
from: {mail_from}
cc: {mail_cc}
subject: {mail_subject}
body: {mail_body}

Please summarize this email according to the format above.
'''

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
        
        response = call_bedrock_claude(messages, max_tokens=1000, temperature=0.3)
        return response
            
    except Exception as e:
        print(f"(EMAILS LOADER): Error summarizing email: {e}")
        # Return a basic formatted version of the email
        return f'''<Email Start>
Date and Time: {mail_date}
Sender: {mail_from}
CC: {mail_cc}
Subject: {mail_subject}
Email Context: {mail_body[:500] if mail_body else "No body content available"}...
<Email End>'''

# Gmail API Related Functions
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """Authenticate Gmail API"""
    creds = None
    token_file = 'token.json'
    
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def get_embedding(text):
    """Generate embedding for text (simplified version)"""
    # In production, you might want to use a proper embedding model
    # For now, using a simple hash-based approach
    import hashlib
    hash_obj = hashlib.sha256(text.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Convert to numpy array of fixed size
    embedding = np.array([int(hash_hex[i:i+2], 16) for i in range(0, min(len(hash_hex), EMBEDDING_DIM*2), 2)])
    
    # Pad or truncate to EMBEDDING_DIM
    if len(embedding) < EMBEDDING_DIM:
        embedding = np.pad(embedding, (0, EMBEDDING_DIM - len(embedding)))
    else:
        embedding = embedding[:EMBEDDING_DIM]
    
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    return embedding.reshape(1, -1)

def clean_html(html_content):
    """Clean HTML content and extract plain text"""
    try:
        if not html_content:
            return ""
        if isinstance(html_content, str):
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text("\n", strip=True)
        return str(html_content)
    except Exception as e:
        print(f"(EMAILS LOADER): Error cleaning HTML content: {e}")
        return str(html_content) if html_content else ""

def get_plain_text_body(parts):
    """Recursively extract plain text from MIME parts"""
    plain_text = None
    html_text = None
    
    for part in parts:
        mime_type = part['mimeType']
        if 'parts' in part:
            text = get_plain_text_body(part['parts'])
            if text:
                return text
        elif mime_type == 'text/plain' and 'data' in part['body']:
            plain_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        elif mime_type == 'text/html' and 'data' in part['body']:
            html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            html_text = clean_html(html_body)

    return plain_text if plain_text else html_text

def get_message_details(service, user_id, msg_id):
    """Get email message details"""
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
        headers = message['payload']['headers']
        details = {header['name']: header['value'] for header in headers if header['name'] in ['From', 'Cc', 'Subject', 'Date']}

        payload = message['payload']
        if 'parts' in payload:
            details['Body'] = get_plain_text_body(payload['parts'])
        elif 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            details['Body'] = clean_html(body)
        else:
            details['Body'] = None
        
        return details
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def list_messages(service, user_id, query=''):
    """List Gmail messages"""
    try:
        messages = []
        request = service.users().messages().list(userId=user_id, q=query)
        while request is not None:
            response = request.execute()
            if 'messages' in response:
                messages.extend(response['messages'])
            request = service.users().messages().list_next(request, response)
        return messages
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def load_emails():
    """Load emails into database"""
    i = 1
    service = authenticate_gmail()
    
    # Get current month's start date with timezone awareness
    current_date = datetime.now(timezone.utc)
    first_day_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Create a query for emails from Pavan (dnspavankumar2006@gmail.com) from current month
    query = f'after:{first_day_of_month.strftime("%Y/%m/%d")} from:dnspavankumar2006@gmail.com'
    messages = list_messages(service, 'me', query)
    
    if not messages:
        print('(EMAILS LOADER): No emails from Pavan (dnspavankumar2006@gmail.com) found for this month.')
        # Also try searching for emails with "Pavan" in the sender name
        query_alt = f'after:{first_day_of_month.strftime("%Y/%m/%d")} from:pavan'
        messages = list_messages(service, 'me', query_alt)
        if messages:
            print('(EMAILS LOADER): Found emails from senders with "Pavan" in the name.')
    
    if not messages:
        print('(EMAILS LOADER): No emails from Pavan found. Trying broader search...')
        # Fallback: search for any emails containing "Pavan" in sender or subject
        query_broad = f'after:{first_day_of_month.strftime("%Y/%m/%d")} (from:pavan OR subject:pavan)'
        messages = list_messages(service, 'me', query_broad)
    
    if not messages:
        print('(EMAILS LOADER): No emails from Pavan found with any search method.')
        return False
    
    # Process emails
    emails_processed = 0
    max_emails = 20
    
    for msg in messages:
        if emails_processed >= max_emails:
            break
            
        msg_id = msg['id']
        details = get_message_details(service, 'me', msg_id)
        if details:
            message_datetime = utils.parsedate_to_datetime(details['Date'])
            if message_datetime.tzinfo is None:
                message_datetime = message_datetime.replace(tzinfo=timezone.utc)
            
            if message_datetime < first_day_of_month:
                continue

            mail_from = details.get('From', '').lower()
            mail_cc = details.get('Cc')
            mail_subject = details.get('Subject')
            mail_body = details.get('Body')

            # Check if this email is actually from Pavan or contains Pavan
            if ('dnspavankumar2006@gmail.com' in mail_from or 
                'pavan' in mail_from or 
                (mail_subject and 'pavan' in mail_subject.lower())):
                
                full_email = summerize_email(mail_from, mail_cc, mail_subject, message_datetime, mail_body)
                embedding = get_embedding(full_email)
                
                # Store in database
                email_data = {
                    'email_id': msg_id,
                    'sender': mail_from,
                    'subject': mail_subject or '',
                    'date_sent': message_datetime,
                    'body_text': mail_body or '',
                    'summary': full_email,
                    'embedding': embedding
                }
                
                if email_db.store_email(email_data):
                    print(f"(EMAILS LOADER): Pavan's Email # {i} stored in database: ({message_datetime}), ({mail_subject}).")
                    i += 1
                    emails_processed += 1

    print(f"(EMAILS LOADER): Processed {emails_processed} emails from Pavan (max: {max_emails}).")
    
    # Update last checked time
    email_db.update_last_check(datetime.now(timezone.utc))
    return True

def ask_question(question, messages=None):
    """Ask question about emails using database storage"""
    try:
        print(f"DEBUG: Starting ask_question with question: {question}")
        print(f"DEBUG: AWS credentials set: {'Yes' if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY else 'No'}")
        print(f"DEBUG: Bedrock client initialized: {'Yes' if bedrock_client else 'No'}")
        
        # Check if Bedrock client is properly initialized
        if not bedrock_client or not AWS_ACCESS_KEY_ID:
            raise ValueError("AWS Bedrock client not properly initialized - credentials missing or invalid")
        
        if messages is None:
            print("DEBUG: New conversation started")
            try:
                # Search emails in database
                query_embedding = get_embedding(question)
                related_emails = email_db.search_emails(query_embedding)
                print(f"DEBUG: Found {len(related_emails)} related emails")
            except Exception as e:
                print(f"DEBUG: Error in email search: {str(e)}")
                raise
                
            system_content = (
                "You are Finand, an AI assistant with access to the user's email collection. "
                "Below, you'll find the most relevant emails from Pavan (dnspavankumar2006@gmail.com) retrieved for the user's question. "
                "Your job is to answer the question based on Pavan's emails. "
                "If you cannot find the answer in Pavan's emails, please politely inform the user. "
                "Answer in a conversational, helpful manner as a personal email assistant."
            )

            local_timezone = get_localzone()
            
            context = f"Today's Datetime is {datetime.now(local_timezone)}\n\n"
            for i, email in enumerate(related_emails):
                context += f"Email({i+1}):\n\n{email}\n\n"
            
            messages = [
                {"role": "system", "content": system_content + "\n\n" + context},
                {"role": "user", "content": question}
            ]
            
            print("DEBUG: Preparing to call AWS Bedrock for new conversation")
        else:
            print("DEBUG: Follow-up question in existing conversation")
            print(f"DEBUG: Message history length: {len(messages)}")
            messages_to_send = messages + [{"role": "user", "content": question}]
            print("DEBUG: Preparing to call AWS Bedrock with conversation history")
        
        # Make the API call
        try:
            print("DEBUG: Calling AWS Bedrock...")
            
            if messages and len(messages) > 1 and "user" in messages[-1]["role"]:
                api_messages = messages
            elif messages is None:
                api_messages = messages
            else:
                api_messages = messages + [{"role": "user", "content": question}]
            
            print(f"DEBUG: API messages structure: {[m['role'] for m in api_messages]}")
            
            assistant_reply = call_bedrock_claude(api_messages, max_tokens=1000, temperature=0.3)
            
            print("DEBUG: Bedrock API call completed")
            print(f"DEBUG: Successfully extracted reply: {assistant_reply[:50]}...")
            
        except Exception as api_error:
            print(f"DEBUG: API call error: {str(api_error)}")
            assistant_reply = "I apologize, but there was an error connecting to AWS Bedrock. Please check your AWS credentials and internet connection."
        
        # Update message history
        if messages is None:
            messages = [
                {"role": "system", "content": system_content + "\n\n" + context},
                {"role": "user", "content": question},
                {"role": "assistant", "content": assistant_reply}
            ]
        else:
            messages.append({"role": "user", "content": question})
            messages.append({"role": "assistant", "content": assistant_reply})
        
        print("DEBUG: Returning successful response")
        return messages, assistant_reply
        
    except Exception as e:
        import traceback
        print(f"DEBUG: Critical error in ask_question: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        
        error_message = f"I apologize, but I encountered a system error while processing your request. Error details: {str(e)}"
        
        if messages is None:
            messages = [
                {"role": "system", "content": "Error occurred"},
                {"role": "user", "content": question},
                {"role": "assistant", "content": error_message}
            ]
        else:
            messages.append({"role": "user", "content": question})
            messages.append({"role": "assistant", "content": error_message})
        
        return messages, error_message