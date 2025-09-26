import streamlit as st
import sys
import os
from datetime import datetime
import time

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our existing RAG_Gmail functions
from RAG_Gmail import load_emails, ask_question

# Configure Streamlit page
st.set_page_config(
    page_title="Finand - Email Assistant",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'emails_loaded' not in st.session_state:
        st.session_state.emails_loaded = False
    if 'loading' not in st.session_state:
        st.session_state.loading = False

def load_emails_if_needed():
    """Load emails if not already loaded"""
    if not st.session_state.emails_loaded and not st.session_state.loading:
        with st.spinner("Loading emails... This may take a moment."):
            try:
                load_emails()
                st.session_state.emails_loaded = True
                st.success("✅ Emails loaded successfully!")
                return True
            except Exception as e:
                st.error(f"❌ Error loading emails: {str(e)}")
                return False
    return st.session_state.emails_loaded

def display_chat_message(message, is_user=True):
    """Display a chat message using Streamlit native components for better readability"""
    if is_user:
        with st.container():
            st.markdown("**🧑 You:**")
            st.info(message)
    else:
        with st.container():
            st.markdown("**🤖 Finand:**")
            st.success(message)

def main():
    """Main Streamlit app with improved readability"""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("📧 Finand")
    st.subheader("Your Personal Email Assistant")
    st.divider()
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Dashboard")
        
        # Email loading status
        st.subheader("📧 Email Status")
        if st.session_state.emails_loaded:
            st.success("✅ Emails Loaded")
        else:
            st.info("⏳ Ready to Load")
        
        # Load emails button
        if st.button("🔄 Reload Emails", help="Refresh email database"):
            st.session_state.emails_loaded = False
            st.session_state.messages = None
            st.rerun()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", help="Clear conversation history"):
            st.session_state.chat_history = []
            st.session_state.messages = None
            st.rerun()
        
        st.divider()
        
        # App info
        st.subheader("ℹ️ About Finand")
        st.markdown("""
        **Finand** helps you:
        
        • 📧 Search through emails
        • 💬 Ask questions about content  
        • 📊 Get inbox insights
        • 🔍 Find information quickly
        """)
        
        # Statistics
        if st.session_state.chat_history:
            st.divider()
            st.subheader("📈 Session Stats")
            questions = len([msg for msg in st.session_state.chat_history if msg['is_user']])
            responses = len([msg for msg in st.session_state.chat_history if not msg['is_user']])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Questions", questions)
            with col2:
                st.metric("Responses", responses)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Load emails on first run
        if not st.session_state.emails_loaded:
            st.info("👋 Welcome to Finand! Let's start by loading your emails.")
            if st.button("📧 Load Emails", type="primary", use_container_width=True):
                load_emails_if_needed()
                st.rerun()
        else:
            # Chat interface
            st.subheader("💬 Chat with Finand")
            
            # Display chat history
            if st.session_state.chat_history:
                st.markdown("### Conversation History")
                
                # Create a container for chat messages
                chat_container = st.container()
                
                with chat_container:
                    for i, msg in enumerate(st.session_state.chat_history):
                        if msg['is_user']:
                            st.markdown("**🧑 You:**")
                            st.info(msg['content'])
                        else:
                            st.markdown("**🤖 Finand:**")
                            st.success(msg['content'])
                        
                        if i < len(st.session_state.chat_history) - 1:
                            st.markdown("---")
            
            st.divider()
            
            # Chat input
            st.markdown("### Ask Finand")
            user_input = st.text_area(
                "Type your question here:",
                placeholder="e.g., 'What are my recent important emails?' or 'Any updates about my portfolio?'",
                height=100,
                key="user_input"
            )
            
            col_send, col_clear = st.columns([3, 1])
            
            with col_send:
                send_button = st.button("Send Message 📤", type="primary", use_container_width=True)
            
            with col_clear:
                if st.button("Clear Input", use_container_width=True):
                    st.session_state.user_input = ""
                    st.rerun()
            
            # Example questions
            st.markdown("**💡 Example questions:**")
            st.caption("• 'Show me recent emails' • 'Any financial updates?' • 'What's in my inbox?'")
            
            # Process user input
            if send_button and user_input.strip():
                # Add user message to history
                st.session_state.chat_history.append({
                    'content': user_input,
                    'is_user': True,
                    'timestamp': datetime.now()
                })
                
                # Get AI response
                with st.spinner("🤖 Finand is thinking..."):
                    try:
                        messages, response = ask_question(user_input, st.session_state.messages)
                        st.session_state.messages = messages
                        
                        # Add assistant response to history
                        st.session_state.chat_history.append({
                            'content': response,
                            'is_user': False,
                            'timestamp': datetime.now()
                        })
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.session_state.chat_history.append({
                            'content': f"Sorry, I encountered an error: {str(e)}",
                            'is_user': False,
                            'timestamp': datetime.now()
                        })
    
    with col2:
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        quick_questions = [
            ("📧", "Show me recent emails"),
            ("💰", "Any financial updates?"), 
            ("📊", "Portfolio notifications?"),
            ("🔔", "Important alerts?"),
            ("📅", "Recent communications?")
        ]
        
        for emoji, question in quick_questions:
            if st.button(f"{emoji} {question}", key=f"quick_{question}", use_container_width=True):
                # Add question to chat
                st.session_state.chat_history.append({
                    'content': question,
                    'is_user': True,
                    'timestamp': datetime.now()
                })
                
                # Get AI response
                try:
                    messages, response = ask_question(question, st.session_state.messages)
                    st.session_state.messages = messages
                    
                    st.session_state.chat_history.append({
                        'content': response,
                        'is_user': False,
                        'timestamp': datetime.now()
                    })
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        st.divider()
        
        # Tips
        st.subheader("💡 Tips")
        st.markdown("""
        **Ask Finand about:**
        - Recent email summaries
        - Specific senders or topics  
        - Financial notifications
        - Important updates
        - Email search queries
        """)
        
        with st.expander("📖 More Examples"):
            st.markdown("""
            - "What emails did I get today?"
            - "Any updates from banks?"
            - "Show me important emails"
            - "What's new in my inbox?"
            - "Find emails about investments"
            """)

if __name__ == "__main__":
    main()