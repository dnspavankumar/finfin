import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import speech_recognition as sr
import pyttsx3
from RAG_Gmail import load_emails, ask_question
import time
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from PIL import Image, ImageTk
import io
import numpy as np

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

print("Starting application...")  # Debug print

# CustomTkinter handles modern styling automatically, so we can remove the AnimatedButton class

class VoiceThread(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.daemon = True

    def run(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                audio = recognizer.listen(source)
                query = recognizer.recognize_google(audio)
                self.callback(query)
        except sr.UnknownValueError:
            messagebox.showerror("Error", "Could not understand audio")
        except sr.RequestError:
            messagebox.showerror("Error", "Could not request results; check your internet connection")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")



class MessageBubble(ctk.CTkFrame):
    def __init__(self, parent, text, is_user=True, **kwargs):
        # Get color palette from parent
        colors = parent.master.master.colors if hasattr(parent.master.master, 'colors') else {
            'primary': '#89B4FA', 'secondary': '#313244', 'background': '#1E1E2E', 
            'text': '#CDD6F4', 'accent': '#F38BA8'
        }
        
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        # Create main container that fills width
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill='x', pady=5, padx=15)
        
        if is_user:
            # User message - RIGHT aligned with accent color (red/pink)
            # Create right-aligned container
            right_container = ctk.CTkFrame(main_container, fg_color="transparent")
            right_container.pack(fill='x')
            
            msg_frame = ctk.CTkFrame(right_container, fg_color=colors['accent'], corner_radius=15)
            msg_frame.pack(side='right', padx=(80, 0), pady=5)
            
            text_color = colors['background']
            font_config = ("JetBrains Mono", 12, "normal")
            wrap_length = 350
        else:
            # Assistant message - LEFT aligned with primary color (blue)
            # Create left-aligned container
            left_container = ctk.CTkFrame(main_container, fg_color="transparent")
            left_container.pack(fill='x')
            
            msg_frame = ctk.CTkFrame(left_container, fg_color=colors['primary'], corner_radius=15)
            msg_frame.pack(side='left', padx=(0, 80), pady=5)
            
            text_color = colors['background']
            font_config = ("JetBrains Mono", 13, "normal")
            wrap_length = 400
        
        # Message text with proper wrapping
        msg_label = ctk.CTkLabel(msg_frame, text=text, text_color=text_color, 
                               font=font_config, wraplength=wrap_length, 
                               justify='left', anchor='nw')
        msg_label.pack(padx=18, pady=12, anchor='nw')

class GmailAssistantUI:
    def __init__(self, root):
        print("Initializing GmailAssistantUI...")  # Debug print
        self.root = root
        self.root.title("Finand")
        self.root.geometry("1400x800")  # Increased width for sidebar
        
        # Define consistent color palette
        self.colors = {
            # Primary colors
            'background': '#1E1E2E',      # Main background
            'primary': '#89B4FA',         # Primary blue
            'secondary': '#313244',       # Secondary dark
            'accent': '#F38BA8',          # Accent pink
            
            # Text colors
            'text': '#CDD6F4',           # Primary text
            'text_muted': '#6C7086',     # Muted text
            'text_success': '#A6E3A1',   # Success green
            'text_warning': '#F9E2AF',   # Warning yellow
            'text_error': '#F38BA8',     # Error (same as accent)
            
            # Surface colors
            'surface': '#45475A',        # Cards/containers
            'surface_variant': '#585B70', # Hover states
            'surface_dim': '#313244',    # Dimmed surfaces
            
            # Interactive states
            'hover': '#7AA3F0',          # Primary hover
            'active': '#6C96ED',         # Primary active
            'disabled': '#6C7086',       # Disabled state
        }
        
        # Initialize variables
        self.messages = None
        self.new_conversation = True
        self.engine = pyttsx3.init()
        self.is_listening = False
        self.sidebar_collapsed = False
        self.sidebar_width = 350
        self.collapsed_width = 60
        
        # Configure style
        self.setup_styles()
        
        # Create header
        self.create_header()
        
        # Create main container with sidebar
        self.create_main_container()
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main layout
        self.create_main_layout()
        
        # Create input area
        self.create_input_area()
        
        # Load initial emails
        self.load_initial_emails()
        
        print("GmailAssistantUI initialized successfully")  # Debug print
        
        # Bind Enter key to send message
        self.input_field.bind("<Return>", self.handle_enter_key)
        
        # No entrance animation needed
    
    def setup_styles(self):
        # Configure modern fonts with better sizing and spacing
        self.title_font = ("JetBrains Mono", 22, "bold")  # Larger title
        self.subtitle_font = ("JetBrains Mono", 14, "normal")  # Better subtitle
        self.header_font = ("JetBrains Mono", 16, "bold")  # Section headers
        self.chat_font_user = ("JetBrains Mono", 14, "normal")  # User messages
        self.chat_font_ai = ("JetBrains Mono", 15, "normal")  # AI responses
        self.input_font = ("JetBrains Mono", 14, "normal")  # Input field
        self.balance_font = ("JetBrains Mono", 18, "bold")  # Balance display
        self.task_font = ("JetBrains Mono", 12, "normal")  # Task items
    
    def create_header(self):
        # Modern header with consistent color palette
        header_frame = ctk.CTkFrame(self.root, fg_color=self.colors['secondary'], height=80)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)
        
        # Header content with generous padding
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(expand=True, fill='both')
        
        # Title with consistent colors
        title_label = ctk.CTkLabel(header_content, text="Finand", 
                                  text_color=self.colors['text'], font=self.title_font)
        title_label.pack(side='left', padx=30, pady=20)
        
        # Status indicator with success color
        self.status_label = ctk.CTkLabel(header_content, text="● Ready", 
                                        text_color=self.colors['text_success'], font=self.subtitle_font)
        self.status_label.pack(side='left', padx=(0, 30), pady=20)
        
        # Modern new chat button with consistent palette
        new_chat_btn = ctk.CTkButton(header_content, text="+ New Chat", 
                                    fg_color=self.colors['surface'], text_color=self.colors['text'],
                                    font=("JetBrains Mono", 12, "bold"),
                                    corner_radius=10, width=130, height=42,
                                    hover_color=self.colors['surface_variant'],
                                    command=self.start_new_chat)
        new_chat_btn.pack(side='right', padx=30, pady=20)
    
    def create_main_container(self):
        # Main container that holds sidebar and chat area
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(expand=True, fill='both')
        
        # Create right side container for chat + input
        self.right_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.right_container.pack(side='right', expand=True, fill='both')
    
    def create_sidebar(self):
        # Modern sidebar frame with consistent colors
        self.sidebar = ctk.CTkFrame(self.main_container, fg_color=self.colors['secondary'], width=self.sidebar_width, corner_radius=0)
        self.sidebar.pack(side='left', fill='y', padx=(0, 2))
        self.sidebar.pack_propagate(False)
        
        # Sidebar header with consistent palette
        sidebar_header = ctk.CTkFrame(self.sidebar, fg_color=self.colors['surface'], corner_radius=0, height=50)
        sidebar_header.pack(fill='x', pady=(0, 1))
        sidebar_header.pack_propagate(False)
        
        # Toggle button with consistent colors
        self.toggle_btn = ctk.CTkButton(sidebar_header, text="☰", width=40, height=30,
                                       fg_color="transparent", text_color=self.colors['text'],
                                       font=("JetBrains Mono", 16, "bold"),
                                       hover_color=self.colors['surface_variant'], corner_radius=8,
                                       command=self.toggle_sidebar)
        self.toggle_btn.pack(side='left', padx=10, pady=10)
        
        # Sidebar title with consistent text color
        self.sidebar_title = ctk.CTkLabel(sidebar_header, text="Dashboard", 
                                         text_color=self.colors['text'], font=("JetBrains Mono", 14, "bold"))
        self.sidebar_title.pack(side='left', padx=(10, 0), pady=10)
        
        # Sidebar content with proper scrolling
        self.sidebar_canvas = tk.Canvas(self.sidebar, bg=self.colors['secondary'], highlightthickness=0)
        self.sidebar_frame = ctk.CTkFrame(self.sidebar_canvas, fg_color="transparent")
        
        # Pack canvas to fill remaining space after header
        self.sidebar_canvas.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Create window in canvas
        self.sidebar_window = self.sidebar_canvas.create_window((0, 0), window=self.sidebar_frame, anchor="nw")
        
        # Financial Overview Section (make it more compact)
        self.create_financial_section(self.sidebar_frame)
        
        # Task Checklist Section (make it more compact)
        self.create_task_section(self.sidebar_frame)
        
        # Bind events for proper scrolling
        self.sidebar_frame.bind('<Configure>', self.on_sidebar_frame_configure)
        self.sidebar_canvas.bind('<Configure>', self.on_sidebar_canvas_configure)
        self.sidebar_canvas.bind("<MouseWheel>", self.on_sidebar_mousewheel)
    
    def on_sidebar_frame_configure(self, event):
        self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))
    
    def on_sidebar_canvas_configure(self, event):
        canvas_width = event.width
        self.sidebar_canvas.itemconfig(self.sidebar_window, width=canvas_width)
    
    def on_sidebar_mousewheel(self, event):
        # Only scroll sidebar if mouse is over it
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if widget and str(widget).startswith(str(self.sidebar_canvas)):
            # Get current scroll position for boundary checking
            top, bottom = self.sidebar_canvas.yview()
            scroll_direction = int(-1*(event.delta/120))
            
            # Prevent scrolling beyond boundaries
            if scroll_direction < 0 and top <= 0:
                return
            if scroll_direction > 0 and bottom >= 1:
                return
                
            self.sidebar_canvas.yview_scroll(scroll_direction, "units")
    
    def create_modern_chart(self, parent, credits, debits, days):
        """Create a modern Seaborn chart and embed it in the sidebar"""
        try:
            # Set up matplotlib/seaborn styling
            plt.style.use('dark_background')
            sns.set_palette([self.colors['text_success'], self.colors['accent']])
            
            # Create compact figure with dark theme
            fig, ax = plt.subplots(figsize=(4.2, 2.2), facecolor=self.colors['surface'])
            ax.set_facecolor(self.colors['surface'])
            
            # Prepare data for seaborn
            data = pd.DataFrame({
                'Day': days * 2,
                'Amount': credits + debits,
                'Type': ['Credits'] * len(days) + ['Debits'] * len(days)
            })
            
            # Create modern bar plot with seaborn
            sns.barplot(data=data, x='Day', y='Amount', hue='Type', ax=ax,
                       palette=[self.colors['text_success'], self.colors['accent']],
                       alpha=0.9, edgecolor='white', linewidth=0.5)
            
            # Customize the plot with consistent colors (more compact)
            ax.set_title('Weekly Overview', 
                        color=self.colors['text'], fontsize=10, 
                        fontfamily='monospace', pad=8)
            
            ax.set_xlabel('', color=self.colors['text'])
            ax.set_ylabel('Amount (₹)', color=self.colors['text'], fontsize=9, fontfamily='monospace')
            
            # Style the axes
            ax.tick_params(colors=self.colors['text_muted'], labelsize=8)
            ax.grid(True, alpha=0.3, color=self.colors['text_muted'], linewidth=0.5)
            
            # Format y-axis to show rupees
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x/1000:.0f}K'))
            
            # Style the legend
            legend = ax.legend(frameon=True, facecolor=self.colors['surface_variant'], 
                             edgecolor=self.colors['text_muted'], fontsize=8)
            legend.get_frame().set_alpha(0.9)
            for text in legend.get_texts():
                text.set_color(self.colors['text'])
            
            # Remove top and right spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(self.colors['text_muted'])
            ax.spines['bottom'].set_color(self.colors['text_muted'])
            
            # Tight layout
            plt.tight_layout()
            
            # Convert to image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor=self.colors['surface'], 
                       dpi=100, bbox_inches='tight', pad_inches=0.1)
            buf.seek(0)
            
            # Close the figure to free memory
            plt.close(fig)
            
            # Load image and display
            img = Image.open(buf)
            
            # Convert PIL image to PhotoImage and display directly in section
            photo = ImageTk.PhotoImage(img)
            
            # Create label to hold the chart image (more compact)
            chart_label = ctk.CTkLabel(parent, image=photo, text="")
            chart_label.image = photo  # Keep a reference
            chart_label.pack(pady=(5, 10), padx=10)
            
        except Exception as e:
            print(f"Error creating modern chart: {e}")
            # Fallback to simple text display
            fallback_container = ctk.CTkFrame(parent, fg_color=self.colors['surface'], corner_radius=12)
            fallback_container.pack(fill='x', pady=(0, 25))
            
            ctk.CTkLabel(fallback_container, 
                        text="📊 Financial Chart\n(Install matplotlib, seaborn & pandas for enhanced view)",
                        text_color=self.colors['text'],
                        font=("JetBrains Mono", 10)).pack(pady=20)
    
    def toggle_sidebar(self):
        """Toggle sidebar collapse/expand instantly"""
        if self.sidebar_collapsed:
            # Expand sidebar
            self.sidebar_collapsed = False
            self.sidebar.configure(width=self.sidebar_width)
            self.toggle_btn.configure(text="☰")
            # Show sidebar content
            self.sidebar_title.pack(side='left', padx=(10, 0), pady=10)
            self.show_sidebar_content()
        else:
            # Collapse sidebar
            self.sidebar_collapsed = True
            self.hide_sidebar_content()
            self.sidebar_title.pack_forget()
            self.sidebar.configure(width=self.collapsed_width)
            self.toggle_btn.configure(text="→")
    

    
    def hide_sidebar_content(self):
        """Hide sidebar content when collapsed"""
        # Hide all content except toggle button
        for widget in self.sidebar_frame.winfo_children():
            widget.pack_forget()
    
    def show_sidebar_content(self):
        """Show sidebar content when expanded"""
        # Recreate sidebar content
        self.create_financial_section(self.sidebar_frame)
        self.create_task_section(self.sidebar_frame)
        
        # Update scroll region
        self.sidebar_frame.update_idletasks()
        self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))
    

    
    def create_financial_section(self, parent):
        # Compact financial section with consistent colors
        fin_section = ctk.CTkFrame(parent, fg_color=self.colors['surface'], corner_radius=12)
        fin_section.pack(fill='x', pady=(0, 15), padx=5)
        
        # Compact header with consistent palette
        header_frame = ctk.CTkFrame(fin_section, fg_color="transparent")
        header_frame.pack(fill='x', padx=15, pady=(10, 5))
        
        # Financial icon
        fin_icon = ctk.CTkLabel(header_frame, text="💰", font=("JetBrains Mono", 16))
        fin_icon.pack(side='left')
        
        fin_header = ctk.CTkLabel(header_frame, text="Financial Overview", text_color=self.colors['text'],
                                 font=("JetBrains Mono", 14, "bold"))
        fin_header.pack(side='left', padx=(8, 0))
        
        # Mock financial data (in rupees)
        credits = [25000, 32000, 28000, 41000, 35000, 29000, 38000]
        debits = [18000, 21000, 24000, 22000, 26000, 23000, 25000]
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        # Create modern Plotly chart
        self.create_modern_chart(fin_section, credits, debits, days)
        
        # Balance summary with enhanced styling
        total_credits = sum(credits)
        total_debits = sum(debits)
        balance = total_credits - total_debits
        
        # Compact balance frame with consistent colors
        balance_frame = ctk.CTkFrame(parent, fg_color=self.colors['surface_variant'], corner_radius=10)
        balance_frame.pack(fill='x', pady=(5, 15), padx=15)
        
        # Balance icon and text (more compact)
        balance_container = ctk.CTkFrame(balance_frame, fg_color="transparent")
        balance_container.pack(fill='x', padx=12, pady=10)
        
        # Balance icon
        balance_icon = ctk.CTkLabel(balance_container, text="💳", font=("JetBrains Mono", 14))
        balance_icon.pack(side='left')
        
        # Balance text with consistent color palette (smaller font)
        balance_text = ctk.CTkLabel(balance_container, text=f"Balance: ₹{balance:,}", 
                                   text_color=self.colors['text_success'] if balance > 0 else self.colors['accent'],
                                   font=("JetBrains Mono", 14, "bold"))
        balance_text.pack(side='left', padx=(8, 0))
    
    def create_task_section(self, parent):
        # Compact task section with consistent colors
        task_section = ctk.CTkFrame(parent, fg_color=self.colors['surface'], corner_radius=12)
        task_section.pack(fill='x', pady=(0, 15), padx=5)
        
        # Compact task header with consistent palette
        header_frame = ctk.CTkFrame(task_section, fg_color="transparent")
        header_frame.pack(fill='x', padx=15, pady=(10, 5))
        
        # Task icon
        task_icon = ctk.CTkLabel(header_frame, text="✅", font=("JetBrains Mono", 16))
        task_icon.pack(side='left')
        
        task_header = ctk.CTkLabel(header_frame, text="Tasks & Updates", text_color=self.colors['text'],
                                  font=("JetBrains Mono", 14, "bold"))
        task_header.pack(side='left', padx=(8, 0))
        
        # Compact task list frame
        task_frame = ctk.CTkFrame(task_section, fg_color="transparent")
        task_frame.pack(fill='x', padx=12, pady=(0, 10))
        
        # Mock tasks (reduced to 4 for better spacing)
        tasks = [
            ("Portfolio Review", True),
            ("Investment Strategy", False),
            ("Bank Statements", True),
            ("Budget Analysis", False)
        ]
        
        # Task icons mapping (updated for reduced tasks)
        task_icons = {
            "Portfolio Review": "📊",
            "Investment Strategy": "📈", 
            "Bank Statements": "🏦",
            "Budget Analysis": "💰"
        }
        
        for task, completed in tasks:
            # Larger task row with better spacing
            task_row = ctk.CTkFrame(task_frame, 
                                   fg_color=self.colors['surface_variant'] if not completed else self.colors['surface'], 
                                   corner_radius=8, height=45)
            task_row.pack(fill='x', padx=8, pady=5)
            task_row.pack_propagate(False)
            
            # Task icon (larger)
            icon = task_icons.get(task, "📝")
            icon_label = ctk.CTkLabel(task_row, text=icon, font=("JetBrains Mono", 16))
            icon_label.pack(side='left', padx=(12, 8), pady=12)
            
            # Larger status indicator with consistent colors
            def create_status_button():
                btn = ctk.CTkButton(task_row, text="✓" if completed else "○", 
                                   fg_color=self.colors['text_success'] if completed else self.colors['accent'],
                                   text_color=self.colors['background'],
                                   font=("JetBrains Mono", 12, "bold"),
                                   width=28, height=28, corner_radius=14,
                                   hover_color=self.colors['primary'] if completed else self.colors['hover'],
                                   command=lambda: None)
                return btn
            
            status_btn = create_status_button()
            status_btn.pack(side='right', padx=12, pady=12)
            
            # Larger task text with better readability
            task_label = ctk.CTkLabel(task_row, text=task, 
                                     text_color=self.colors['text_success'] if completed else self.colors['text'],
                                     font=("JetBrains Mono", 11, "bold" if completed else "normal"))
            task_label.pack(side='left', anchor='w', padx=(0, 10), pady=12)
    

    
    def create_main_layout(self):
        # Modern chat area with rounded corners
        chat_container = ctk.CTkFrame(self.right_container, fg_color="transparent")
        chat_container.pack(expand=True, fill='both', padx=25, pady=(0, 0))
        
        # Custom chat display using Canvas for smooth scrolling
        self.chat_canvas = tk.Canvas(chat_container, bg="#1e1e2e", highlightthickness=0)
        self.chat_frame = ctk.CTkFrame(self.chat_canvas, fg_color="transparent")
        
        # Pack canvas without scrollbar
        self.chat_canvas.pack(fill="both", expand=True)
        
        # Create window in canvas
        self.canvas_window = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        
        # Bind events for scrolling
        self.chat_frame.bind('<Configure>', self.on_frame_configure)
        self.chat_canvas.bind('<Configure>', self.on_canvas_configure)
        self.chat_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
    
    def create_input_area(self):
        # Input container with consistent colors
        input_container = ctk.CTkFrame(self.right_container, fg_color="transparent", height=100)
        input_container.pack(fill='x', side='bottom', padx=30, pady=25)
        input_container.pack_propagate(False)
        
        # Input row with consistent palette
        input_row = ctk.CTkFrame(input_container, fg_color=self.colors['secondary'], corner_radius=12)
        input_row.pack(fill='both', expand=True)
        
        # Input field with consistent colors
        self.input_field = ctk.CTkEntry(input_row, fg_color="transparent", 
                                       text_color=self.colors['text'], font=self.input_font,
                                       border_width=0, placeholder_text="Type your message here...",
                                       placeholder_text_color=self.colors['text_muted'])
        self.input_field.pack(side='left', fill='both', expand=True, padx=25, pady=20)
        
        # Bind enter key
        self.input_field.bind('<Return>', self.handle_enter_key)
        
        # Voice button with consistent colors
        voice_btn = ctk.CTkButton(input_row, text="🎤", fg_color="transparent", 
                                 text_color=self.colors['text_muted'], font=("JetBrains Mono", 16),
                                 width=50, height=40, corner_radius=10,
                                 hover_color=self.colors['surface'],
                                 command=self.start_voice_input)
        voice_btn.pack(side='right', padx=(0, 15), pady=20)
        
        # Send button with primary color
        send_btn = ctk.CTkButton(input_row, text="➤", fg_color=self.colors['primary'], 
                                text_color=self.colors['background'], font=("JetBrains Mono", 16, "bold"),
                                width=60, height=40, corner_radius=10,
                                hover_color=self.colors['hover'],
                                command=self.send_message)
        send_btn.pack(side='right', padx=15, pady=20)
        

    
    # CustomTkinter Entry handles placeholder automatically, so we can remove these methods
    
    def handle_enter_key(self, event):
        if event.state & 4:  # Ctrl key is pressed
            return 'break'  # Let the default behavior happen (new line)
        else:
            self.send_message()
            return 'break'  # Prevent default behavior
    
    def on_frame_configure(self, event):
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        canvas_width = event.width
        self.chat_canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def on_mousewheel(self, event):
        # Get current scroll position
        top, bottom = self.chat_canvas.yview()
        
        # Calculate scroll direction
        scroll_direction = int(-1*(event.delta/120))
        
        # Prevent scrolling above the top (top should not go below 0)
        if scroll_direction < 0 and top <= 0:
            return
        
        # Prevent scrolling below the bottom (bottom should not go above 1)
        if scroll_direction > 0 and bottom >= 1:
            return
            
        # Apply the scroll
        self.chat_canvas.yview_scroll(scroll_direction, "units")
    
    def add_message_bubble(self, text, is_user=True):
        bubble = MessageBubble(self.chat_frame, text, is_user)
        bubble.pack(fill='x', padx=10, pady=2)
        
        # Simple scroll to bottom
        self.root.after(10, lambda: self.chat_canvas.yview_moveto(1.0))
    
    def update_status(self, status, color="#a6e3a1"):  # Catppuccin Green
        # Map common status colors to Catppuccin equivalents
        color_map = {
            "#4ade80": self.colors['text_success'],  # Green
            "#fbbf24": self.colors['text_warning'],  # Yellow  
            "#ef4444": self.colors['text_error']     # Red
        }
        catppuccin_color = color_map.get(color, color)
        # Use text_color instead of fg for CustomTkinter compatibility
        self.status_label.configure(text=f"● {status}", text_color=catppuccin_color)
        self.root.update()
    
    def load_initial_emails(self):
        try:
            print("Loading initial emails...")  # Debug print
            self.update_status("Loading emails...", "#fbbf24")
            load_emails()
            self.add_message_bubble("Emails loaded successfully! You can now ask questions about your emails.", False)
            self.update_status("Ready")
            print("Emails loaded successfully")  # Debug print
        except Exception as e:
            print(f"Error loading emails: {str(e)}")  # Debug print
            self.add_message_bubble(f"Failed to load emails: {str(e)}", False)
            self.update_status("Error loading emails", "#ef4444")
    
    def send_message(self):
        query = self.input_field.get().strip()
        if not query:
            return
        
        # Add message immediately
        self.add_message_bubble(query, True)
        
        # Clear input field immediately
        self.input_field.delete(0, 'end')
        
        # Update status in title
        self.root.title("Gmail Assistant - Thinking...")
        
        # Process query in thread to avoid blocking UI
        threading.Thread(target=self.process_query, args=(query,), daemon=True).start()
    
    def process_query(self, query):
        try:
            if self.new_conversation:
                self.messages, response = ask_question(query)
                self.new_conversation = False
            else:
                self.messages, response = ask_question(query, messages=self.messages)
            
            # Add response immediately
            self.root.after(0, lambda: self.add_message_bubble(response, False))
            
            # Reset title immediately
            self.root.after(0, lambda: self.root.title("Gmail Assistant"))
            
            # Use a thread for text-to-speech to avoid blocking
            threading.Thread(target=self.speak_text, args=(response,), daemon=True).start()
            
        except Exception as e:
            print(f"Error processing query: {str(e)}")  # Debug print
            
            # Add error message immediately
            self.root.after(0, lambda: self.add_message_bubble(f"Error: {str(e)}", False))
            self.root.after(0, lambda: self.root.title("Gmail Assistant - Error"))
    
    def speak_text(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except:
            pass  # Ignore TTS errors
    
    def start_voice_input(self):
        if self.is_listening:
            return
            
        self.is_listening = True
        # Update title to show listening status
        self.root.title("Gmail Assistant - Listening...")
        
        def voice_callback(query):
            self.is_listening = False
            self.root.title("Gmail Assistant")  # Reset title
            
            if query:
                self.input_field.delete(0, 'end')
                self.input_field.insert(0, query)
                self.send_message()
        
        VoiceThread(voice_callback).start()
    

    
    def start_new_chat(self):
        self.new_conversation = True
        self.messages = None
        
        # Clear chat display
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        
        # Add welcome message
        self.add_message_bubble("New conversation started! How can I help you with your emails?", False)
        self.update_status("Ready")

def main():
    print("Starting main function...")  # Debug print
    root = ctk.CTk()
    
    print("CustomTkinter root created")  # Debug print
    app = GmailAssistantUI(root)
    print("Window created")  # Debug print
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()
    print("Window shown")  # Debug print

if __name__ == "__main__":
    print("Script started")  # Debug print
    main()