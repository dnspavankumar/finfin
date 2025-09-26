# Standard library imports
import base64
from datetime import datetime, timedelta, timezone
from email import utils
import chime
import os
import os.path
import sqlite3
import time
import traceback

# Third-party library imports
from bs4 import BeautifulSoup
import dateutil.parser
from dotenv import load_dotenv
import faiss
import numpy as np
import pyttsx3
import speech_recognition as sr
from tzlocal import get_localzone
import boto3
import json

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# Parameters
INDEX_NAME = "index_email.index"
DB_FILE = "index_email_metadata.db"
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

def call_bedrock_titan(messages, max_tokens=1000, temperature=0.3):
    """
    Call AWS Bedrock Titan model with conversation messages
    """
    try:
        # Convert messages to a simple prompt for Titan
        system_content = ""
        user_content = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg['content']
            elif msg["role"] == "user":
                user_content = msg['content']
        
        # Create a simple, clean prompt
        if system_content:
            prompt = f"{system_content}\n\nQuestion: {user_content}\n\nAnswer:"
        else:
            prompt = f"Question: {user_content}\n\nAnswer:"
        
        # Prepare the request body for Titan (simplified format)
        body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": 0.9
            }
        }
        
        # Call Bedrock with Titan Text Express
        response = bedrock_client.invoke_model(
            modelId="amazon.titan-text-express-v1",
            body=json.dumps(body),
            contentType="application/json"
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        if 'results' in response_body and response_body['results']:
            return response_body['results'][0]['outputText'].strip()
        else:
            return "I apologize, but I received an empty response from the AI model."
            
    except Exception as e:
        print(f"Error calling Bedrock Titan: {str(e)}")
        return f"I apologize, but there was an error connecting to AWS Bedrock: {str(e)}"

def summerize_email(mail_from, mail_cc, mail_subject, mail_date, mail_body):
    try:
        system_content = '''
Summerize the given Email in the following format, keep it brief but don't lose much information:

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
        
        response = call_bedrock_titan(messages, max_tokens=1000, temperature=0.3)
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

def clean_html(html_content):
    """ Clean HTML content and extract plain text. """
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
    """ Recursively extract plain text from MIME parts, with fallback to cleaned HTML if necessary. """
    plain_text = None
    html_text = None
    
    for part in parts:
        mime_type = part['mimeType']
        if 'parts' in part:
            # Recursively process nested parts
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

def get_last_checked_time():
    try:
        with open('last_checked.txt', 'r') as file:
            return dateutil.parser.parse(file.read().strip())
    except FileNotFoundError:
        return datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

def update_last_checked_time(timestamp):
    with open('last_checked.txt', 'w') as file:
        file.write(str(timestamp))

# Vector Store Operations
def get_embedding(text):
    # For now, we'll use a simple text embedding approach
    # In a production environment, you might want to use a dedicated embedding model
    return np.random.rand(1, EMBEDDING_DIM)

def get_index():
    if os.path.exists(INDEX_NAME):
        return faiss.read_index(INDEX_NAME)
    else:
        return faiss.IndexFlatL2(EMBEDDING_DIM)

def initiate_meta_store():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL
        )
        ''')
    return (conn, cursor)

def terminate_meta_store(conn):
    conn.commit()
    conn.close()

def insert_email_record(full_email, index, cursor):
    embedding = get_embedding(full_email)
    index.add(embedding)
    cursor.execute("INSERT INTO Metadata (text) VALUES (?)", (full_email,))

def Vector_Search(query, demo=False, k=K):
    try:
        print(f"DEBUG: Starting Vector_Search with query: {query}")
        index = get_index()
        conn, cursor = initiate_meta_store()
        query_embedding = get_embedding(query)
        distances, indices = index.search(query_embedding, k)
        decoded_texts = []
        
        print(f"DEBUG: Found {len(indices[0])} indices")
        for idx in indices[0]:
            try:
                cursor.execute(f"SELECT text FROM Metadata WHERE id={idx + 1}")
                result = cursor.fetchone()
                if result:
                    decoded_texts.append(result[0])
                else:
                    print(f"DEBUG: No text found for index {idx + 1}")
            except Exception as e:
                print(f"DEBUG: Error fetching text for index {idx + 1}: {str(e)}")
        
        conn.close()
        
        if demo:
            print("Decoded texts of nearest neighbors:")
            for text in decoded_texts:
                print("*********************************************")
                print("########", text[31:56])
                print(text)
            print("*********************************************")
            print("Distances to nearest neighbors:", distances)
        
        print(f"DEBUG: Returning {len(decoded_texts)} decoded texts")
        return decoded_texts if decoded_texts else ["No relevant emails found."]
        
    except Exception as e:
        print(f"DEBUG: Error in Vector_Search: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return ["No relevant emails found due to an error in the search process."]

def load_emails():
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
    else:
        index = get_index()
        conn, cursor = initiate_meta_store()
        
        # Increase limit to 20 emails for personal emails (more variety)
        emails_processed = 0
        max_emails = 20
        
        for msg in messages:
            # Stop if we've already processed max emails
            if emails_processed >= max_emails:
                break
                
            msg_id = msg['id']
            details = get_message_details(service, 'me', msg_id)
            if details:
                message_datetime = utils.parsedate_to_datetime(details['Date'])
                # Ensure message_datetime is timezone-aware
                if message_datetime.tzinfo is None:
                    message_datetime = message_datetime.replace(tzinfo=timezone.utc)
                
                # Skip if email is from before this month
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
                    insert_email_record(full_email, index, cursor)
                    
                    print(f"(EMAILS LOADER): Pavan's Email # {i} is detected and inserted: ({message_datetime}), ({mail_subject}).")
                    i += 1
                    emails_processed += 1

        terminate_meta_store(conn)
        faiss.write_index(index, INDEX_NAME)
        print(f"(EMAILS LOADER): Vector store and metadata saved. Processed {emails_processed} emails from Pavan (max: {max_emails}).")
        
        # Update last checked time to current time
        update_last_checked_time(datetime.now(timezone.utc))

def ask_question(question, messages=None):
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
                related_emails = Vector_Search(question)
                print(f"DEBUG: Found {len(related_emails)} related emails")
            except Exception as e:
                print(f"DEBUG: Error in Vector_Search: {str(e)}")
                raise
                
            system_content = (
                "You are Finand, an AI assistant with access to the user's email collection. "
                "Below, you'll find the most relevant emails retrieved for the user's question. "
                "Your job is to answer the question based on the provided emails. "
                "If you cannot find the answer in the available emails, please politely inform the user. "
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
            
            print("DEBUG: Preparing to call Groq API for new conversation")
        else:
            print("DEBUG: Follow-up question in existing conversation")
            print(f"DEBUG: Message history length: {len(messages)}")
            # Just add the new user question to existing messages
            messages_to_send = messages + [{"role": "user", "content": question}]
            print("DEBUG: Preparing to call Groq API with conversation history")
        
        # Make the API call
        try:
            print("DEBUG: Calling AWS Bedrock...")
            
            # For new conversation
            if messages and len(messages) > 1 and "user" in messages[-1]["role"]:
                # If last message is from user, we need to append the new question
                api_messages = messages
            elif messages is None:
                # First question in conversation
                api_messages = messages
            else:
                # Follow-up question
                api_messages = messages + [{"role": "user", "content": question}]
            
            print(f"DEBUG: API messages structure: {[m['role'] for m in api_messages]}")
            
            assistant_reply = call_bedrock_titan(api_messages, max_tokens=1000, temperature=0.3)
            
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