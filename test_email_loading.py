#!/usr/bin/env python3
"""
Test script to verify email loading from Pavan's account
"""
from RAG_Gmail import authenticate_gmail, list_messages
from datetime import datetime, timezone

def test_pavan_emails():
    """Test loading emails from Pavan's account"""
    
    print("🔍 Testing Email Loading from Pavan's Account...")
    print("=" * 60)
    
    try:
        # Authenticate Gmail
        service = authenticate_gmail()
        print("✅ Gmail authentication successful")
        
        # Get current month's start date
        current_date = datetime.now(timezone.utc)
        first_day_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Test different search queries
        queries = [
            f'after:{first_day_of_month.strftime("%Y/%m/%d")} from:dnspavankumar2006@gmail.com',
            f'after:{first_day_of_month.strftime("%Y/%m/%d")} from:pavan',
            f'after:{first_day_of_month.strftime("%Y/%m/%d")} (from:pavan OR subject:pavan)',
            f'from:dnspavankumar2006@gmail.com',  # All time
            f'from:pavan',  # All time
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n📧 Query {i}: {query}")
            messages = list_messages(service, 'me', query)
            
            if messages:
                print(f"   ✅ Found {len(messages)} emails")
                # Show first few email IDs
                for j, msg in enumerate(messages[:3]):
                    print(f"      Email {j+1}: ID {msg['id']}")
            else:
                print(f"   ❌ No emails found")
        
        # Test broader search
        print(f"\n🔍 Broader search (last 30 days):")
        thirty_days_ago = (current_date - timezone.timedelta(days=30)).strftime("%Y/%m/%d")
        broad_query = f'after:{thirty_days_ago}'
        all_messages = list_messages(service, 'me', broad_query)
        
        if all_messages:
            print(f"   📊 Total emails in last 30 days: {len(all_messages)}")
            print("   📝 Sample sender addresses:")
            
            # Get details of first 5 emails to see sender patterns
            from RAG_Gmail import get_message_details
            
            for i, msg in enumerate(all_messages[:10]):
                details = get_message_details(service, 'me', msg['id'])
                if details:
                    sender = details.get('From', 'Unknown')
                    subject = details.get('Subject', 'No Subject')
                    print(f"      {i+1}. From: {sender[:50]}...")
                    print(f"         Subject: {subject[:40]}...")
        else:
            print("   ❌ No emails found in last 30 days")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("💡 Tips:")
    print("   - If no emails from dnspavankumar2006@gmail.com are found,")
    print("     make sure you're searching the correct Gmail account")
    print("   - The app will now load emails from Pavan instead of Canara Bank")
    print("   - You can modify the search criteria in RAG_Gmail.py if needed")
    
    return True

if __name__ == "__main__":
    test_pavan_emails()