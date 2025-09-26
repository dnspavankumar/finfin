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

# Force light theme for better readability
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Custom CSS for better styling and readability
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
        color: #000000 !important;
        font-size: 1rem;
        line-height: 1.5;
    }
    
    .user-message {
        background-color: #f8f9fa !important;
        border-left-color: #ff6b6b !important;
        color: #212529 !important;
    }
    
    .assistant-message {
        background-color: #e3f2fd !important;
        border-left-color: #1f77b4 !important;
        color: #1565c0 !important;
    }
    
    .chat-message strong {
        color: inherit !important;
        font-weight: bold;
    }
    
    .status-success {
        color: #28a745 !important;
        font-weight: bold;
    }
    
    .status-error {
        color: #dc3545 !important;
        font-weight: bold;
    }
    
    .status-info {
        color: #17a2b8 !important;
        font-weight: bold;
    }
    
    /* Force dark text in light mode */
    .stApp {
        color: #000000;
    }
    
    /* Ensure text areas have proper contrast */
    .stTextArea textarea {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Fix sidebar text */
    .css-1d391kg {
        color: #000000 !important;
    }
    
    /* Ensure all text is readable */
    p, div, span, h1, h2, h3, h4, h5, h6 {
        color: inherit;
    }
</style>
""", unsafe_allow_html=True)

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
    """Display a chat message with proper styling and contrast"""
    if is_user:
        st.markdown(f"""
        <div class="chat-message user-message" style="background-color: #f8f9fa !important; color: #212529 !important; border: 1px solid #dee2e6;">
            <strong style="color: #dc3545 !important;">🧑 You:</strong><br>
            <span style="color: #212529 !important;">{message}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message" style="background-color: #e3f2fd !important; color: #1565c0 !important; border: 1px solid #bbdefb;">
            <strong style="color: #1565c0 !important;">🤖 Finand:</strong><br>
            <span style="color: #1565c0 !important;">{message}</span>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main Streamlit app"""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">📧 Finand</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Your Personal Email Assistant</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Dashboard")
        
        # Email loading status
        st.subheader("📧 Email Status")
        if st.session_state.emails_loaded:
            st.markdown('<p class="status-success">✅ Emails Loaded</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-info">⏳ Ready to Load</p>', unsafe_allow_html=True)
        
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
        
        # App info
        st.subheader("ℹ️ About")
        st.info("""
        **Finand** is your AI-powered email assistant that helps you:
        
        • 📧 Search through your emails
        • 💬 Ask questions about email content
        • 📊 Get insights from your inbox
        • 🔍 Find specific information quickly
        """)
        
        # Statistics
        if st.session_state.chat_history:
            st.subheader("📈 Session Stats")
            st.metric("Questions Asked", len([msg for msg in st.session_state.chat_history if msg['is_user']]))
            st.metric("Responses Given", len([msg for msg in st.session_state.chat_history if not msg['is_user']]))
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Load emails on first run
        if not st.session_state.emails_loaded:
            st.info("👋 Welcome to Finand! Let's start by loading your emails.")
            if st.button("📧 Load Emails", type="primary"):
                load_emails_if_needed()
                st.rerun()
        else:
            # Chat interface
            st.subheader("💬 Chat with Finand")
            
            # Display chat history
            if st.session_state.chat_history:
                st.markdown("### Conversation History")
                for msg in st.session_state.chat_history:
                    display_chat_message(msg['content'], msg['is_user'])
            
            # Chat input
            with st.form("chat_form", clear_on_submit=True):
                user_input = st.text_area(
                    "Ask me anything about your emails:",
                    placeholder="e.g., 'What are my recent important emails?' or 'Any updates about my portfolio?'",
                    height=100
                )
                
                col_submit, col_examples = st.columns([1, 2])
                
                with col_submit:
                    submit_button = st.form_submit_button("Send 📤", type="primary")
                
                with col_examples:
                    st.caption("💡 Try: 'Show me recent emails', 'Any financial updates?', 'What's in my inbox?'")
            
            # Process user input
            if submit_button and user_input.strip():
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
            "📧 Show me recent emails",
            "💰 Any financial updates?", 
            "📊 Portfolio notifications?",
            "🔔 Important alerts?",
            "📅 Recent communications?"
        ]
        
        for question in quick_questions:
            if st.button(question, key=f"quick_{question}"):
                # Simulate clicking with this question
                st.session_state.chat_history.append({
                    'content': question.split(' ', 1)[1],  # Remove emoji
                    'is_user': True,
                    'timestamp': datetime.now()
                })
                
                # Get AI response
                try:
                    messages, response = ask_question(question.split(' ', 1)[1], st.session_state.messages)
                    st.session_state.messages = messages
                    
                    st.session_state.chat_history.append({
                        'content': response,
                        'is_user': False,
                        'timestamp': datetime.now()
                    })
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Tips
        st.subheader("💡 Tips")
        st.markdown("""
        **Ask Finand about:**
        - Recent email summaries
        - Specific senders or topics
        - Financial notifications
        - Important updates
        - Email search queries
        
        **Example questions:**
        - "What emails did I get today?"
        - "Any updates from banks?"
        - "Show me important emails"
        - "What's new in my inbox?"
        """)

if __name__ == "__main__":
    main()