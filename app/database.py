import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "humangates.db")


def get_db_path() -> str:
    return DB_PATH


def _column_exists(cursor, table: str, column: str) -> bool:
    """Check if a column exists in a SQLite table"""
    cols = cursor.execute(f"PRAGMA table_info({table})").fetchall()
    return any(c[1] == column for c in cols)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── Existing tables ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending_review',
            params TEXT NOT NULL,
            result TEXT,
            callback_url TEXT,
            api_key_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            action TEXT NOT NULL,
            note TEXT,
            old_status TEXT,
            new_status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            doc_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_generation_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            wechat TEXT,
            city TEXT NOT NULL,
            service_types TEXT NOT NULL,
            id_number TEXT,
            qualification_desc TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── v0.5.0 new tables ──
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            company_name TEXT,
            credits_balance REAL NOT NULL DEFAULT 0,
            total_spent REAL NOT NULL DEFAULT 0,
            total_tasks INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            task_id TEXT,
            amount REAL NOT NULL,
            balance_before REAL NOT NULL,
            balance_after REAL NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)

    # ── v0.5.0: Add columns to existing tables ──
    # tasks: customer_id + price
    if not _column_exists(cursor, "tasks", "customer_id"):
        cursor.execute("ALTER TABLE tasks ADD COLUMN customer_id TEXT")
    if not _column_exists(cursor, "tasks", "price"):
        cursor.execute("ALTER TABLE tasks ADD COLUMN price REAL DEFAULT 0")

    # suppliers: regions, specialties, rating, completed_tasks, verified, available
    if not _column_exists(cursor, "suppliers", "regions"):
        cursor.execute("ALTER TABLE suppliers ADD COLUMN regions TEXT DEFAULT '[]'")
    if not _column_exists(cursor, "suppliers", "specialties"):
        cursor.execute("ALTER TABLE suppliers ADD COLUMN specialties TEXT DEFAULT '[]'")
    if not _column_exists(cursor, "suppliers", "rating"):
        cursor.execute("ALTER TABLE suppliers ADD COLUMN rating REAL DEFAULT 0")
    if not _column_exists(cursor, "suppliers", "completed_tasks"):
        cursor.execute("ALTER TABLE suppliers ADD COLUMN completed_tasks INTEGER DEFAULT 0")
    if not _column_exists(cursor, "suppliers", "verified"):
        cursor.execute("ALTER TABLE suppliers ADD COLUMN verified INTEGER DEFAULT 0")
    if not _column_exists(cursor, "suppliers", "available"):
        cursor.execute("ALTER TABLE suppliers ADD COLUMN available INTEGER DEFAULT 1")

    conn.commit()
    conn.close()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
