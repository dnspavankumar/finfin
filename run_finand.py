#!/usr/bin/env python3
"""
Finand Launcher - Choose between Desktop or Web interface
"""
import subprocess
import sys
import os

def run_desktop():
    """Run the desktop (CustomTkinter) version"""
    print("🖥️  Starting Finand Desktop App...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Desktop app closed.")
    except Exception as e:
        print(f"❌ Error running desktop app: {e}")

def run_web():
    """Run the web (Streamlit) version"""
    print("🌐 Starting Finand Web App...")
    print("📱 Your browser will open automatically...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app_production.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Web app closed.")
    except Exception as e:
        print(f"❌ Error running web app: {e}")

def run_web_dev():
    """Run the development web version"""
    print("🖥️ Starting Finand Web App (Development)...")
    print("📱 Your browser will open automatically...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app_v2.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Web app closed.")
    except Exception as e:
        print(f"❌ Error running web app: {e}")

def main():
    """Main launcher menu"""
    print("=" * 50)
    print("📧 FINAND - Your Personal Email Assistant")
    print("=" * 50)
    print()
    print("Choose your interface:")
    print("1. 🖥️  Desktop App (CustomTkinter)")
    print("2. 🌐 Web App - Smart (Auto-detects environment)")
    print("3. 🔧 Web App - Development (Files only)")
    print("4. ❌ Exit")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == "1":
                run_desktop()
                break
            elif choice == "2":
                run_web()
                break
            elif choice == "3":
                run_web_dev()
                break
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()