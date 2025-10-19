"""
Database module for SEO Audit Tool
Handles SQLite operations for reports and OAuth tokens
"""
import aiosqlite
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet


class Database:
    def __init__(self, db_path: str, encryption_key: str):
        self.db_path = db_path
        self.cipher = Fernet(encryption_key.encode() if len(encryption_key) == 44 else Fernet.generate_key())
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def initialize(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Reports table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    email TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    report_type TEXT DEFAULT 'free',
                    status TEXT DEFAULT 'pending',
                    pdf_path TEXT,
                    audit_data TEXT,
                    score INTEGER,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)

            # OAuth tokens table (for paid tier)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS oauth_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id INTEGER NOT NULL,
                    service TEXT NOT NULL,
                    encrypted_token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (report_id) REFERENCES reports (id)
                )
            """)

            # Audit log table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_uuid TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.commit()

    async def create_report(
        self,
        uuid: str,
        url: str,
        email: str,
        first_name: str,
        last_name: str,
        report_type: str = 'free'
    ) -> int:
        """Create a new report entry"""
        expires_at = datetime.now() + timedelta(days=3)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO reports (uuid, url, email, first_name, last_name, report_type, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (uuid, url, email, first_name, last_name, report_type, expires_at))

            await db.commit()
            return cursor.lastrowid

    async def update_report_status(
        self,
        uuid: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update report status"""
        async with aiosqlite.connect(self.db_path) as db:
            if error_message:
                await db.execute("""
                    UPDATE reports
                    SET status = ?, error_message = ?
                    WHERE uuid = ?
                """, (status, error_message, uuid))
            else:
                await db.execute("""
                    UPDATE reports
                    SET status = ?
                    WHERE uuid = ?
                """, (status, uuid))

            await db.commit()

    async def complete_report(
        self,
        uuid: str,
        pdf_path: str,
        audit_data: Dict[Any, Any],
        score: int
    ):
        """Mark report as completed with results"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE reports
                SET status = 'completed',
                    pdf_path = ?,
                    audit_data = ?,
                    score = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE uuid = ?
            """, (pdf_path, json.dumps(audit_data), score, uuid))

            await db.commit()

    async def get_report(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Get report by UUID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM reports WHERE uuid = ?
            """, (uuid,))

            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def log_event(self, report_uuid: str, event_type: str, message: str = None):
        """Log an audit event"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO audit_log (report_uuid, event_type, message)
                VALUES (?, ?, ?)
            """, (report_uuid, event_type, message))

            await db.commit()

    async def cleanup_expired_reports(self):
        """Delete expired reports and their PDFs"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get expired report PDFs
            cursor = await db.execute("""
                SELECT pdf_path FROM reports
                WHERE expires_at < CURRENT_TIMESTAMP AND pdf_path IS NOT NULL
            """)

            rows = await cursor.fetchall()

            # Delete PDF files
            for row in rows:
                pdf_path = row[0]
                if os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                    except Exception as e:
                        print(f"Error deleting PDF {pdf_path}: {e}")

            # Delete database records
            await db.execute("""
                DELETE FROM reports WHERE expires_at < CURRENT_TIMESTAMP
            """)

            await db.commit()

    # OAuth Token Management (for paid tier)

    def encrypt_token(self, token: str) -> str:
        """Encrypt OAuth token"""
        return self.cipher.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt OAuth token"""
        return self.cipher.decrypt(encrypted_token.encode()).decode()

    async def store_oauth_token(self, report_id: int, service: str, token: str):
        """Store encrypted OAuth token"""
        encrypted = self.encrypt_token(token)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO oauth_tokens (report_id, service, encrypted_token)
                VALUES (?, ?, ?)
            """, (report_id, service, encrypted))

            await db.commit()

    async def get_oauth_token(self, report_id: int, service: str) -> Optional[str]:
        """Get decrypted OAuth token"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT encrypted_token FROM oauth_tokens
                WHERE report_id = ? AND service = ?
                ORDER BY created_at DESC LIMIT 1
            """, (report_id, service))

            row = await cursor.fetchone()
            if row:
                return self.decrypt_token(row[0])
            return None


# Singleton instance
_db_instance: Optional[Database] = None


def get_database(db_path: str = None, encryption_key: str = None) -> Database:
    """Get or create database instance"""
    global _db_instance

    if _db_instance is None:
        if db_path is None or encryption_key is None:
            raise ValueError("Database path and encryption key required for first initialization")
        _db_instance = Database(db_path, encryption_key)

    return _db_instance
