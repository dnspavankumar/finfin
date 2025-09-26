"""
Database configuration for production deployment
Supports multiple database backends for different deployment scenarios
"""
import os
import sqlite3
import psycopg2
from sqlalchemy import create_engine, text
import streamlit as st
from typing import Optional, Dict, Any

class DatabaseConfig:
    """Database configuration manager for different environments"""
    
    def __init__(self):
        self.db_type = os.getenv('DATABASE_TYPE', 'sqlite')
        self.connection = None
        
    def get_database_url(self) -> str:
        """Get database URL based on environment"""
        
        if self.db_type == 'postgresql':
            # For production deployments
            return os.getenv('DATABASE_URL') or self._get_postgres_url()
        
        elif self.db_type == 'sqlite_memory':
            # For testing/demo (data lost on restart)
            return 'sqlite:///:memory:'
        
        else:
            # Default SQLite (local development only)
            return 'sqlite:///finand_emails.db'
    
    def _get_postgres_url(self) -> str:
        """Construct PostgreSQL URL from environment variables"""
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        name = os.getenv('DB_NAME', 'finand')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', '')
        
        return f'postgresql://{user}:{password}@{host}:{port}/{name}'
    
    def get_engine(self):
        """Get SQLAlchemy engine"""
        url = self.get_database_url()
        return create_engine(url, echo=False)
    
    def init_tables(self):
        """Initialize database tables"""
        engine = self.get_engine()
        
        with engine.connect() as conn:
            # Create emails table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS emails (
                    id SERIAL PRIMARY KEY,
                    email_id VARCHAR(255) UNIQUE,
                    sender VARCHAR(255),
                    subject TEXT,
                    date_sent TIMESTAMP,
                    body_text TEXT,
                    summary TEXT,
                    embedding BYTEA,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create user sessions table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255),
                    messages JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create app metadata table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS app_metadata (
                    key VARCHAR(255) PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.commit()

# Global database config instance
db_config = DatabaseConfig()