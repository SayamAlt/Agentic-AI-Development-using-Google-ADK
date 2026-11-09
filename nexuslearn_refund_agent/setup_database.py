import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "nexuslearn.db"

def setup_database():
    if DB_PATH.exists():
        raise SystemExit(f"NexusLearn database already exists: {DB_PATH}\nNo changes were made.")

    now = datetime.now(timezone.utc)

    def days_ago(days):
        return (now - timedelta(days=days)).isoformat()

    conn = sqlite3.connect(DB_PATH)

    try:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")

            conn.executescript("""
                CREATE TABLE students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL COLLATE NOCASE UNIQUE
                );
                CREATE TABLE courses (
                    course_id TEXT PRIMARY KEY,
                    course_name TEXT NOT NULL,
                    price INTEGER NOT NULL CHECK (price >= 0)
                );
                CREATE TABLE enrollments (
                    enrollment_id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL REFERENCES students(student_id),
                    course_id TEXT NOT NULL REFERENCES courses(course_id),
                    purchased_at TEXT NOT NULL,
                    amount_paid INTEGER NOT NULL CHECK (amount_paid >= 0),
                    completion_percent REAL NOT NULL CHECK (completion_percent BETWEEN 0 AND 100),
                    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'refund_requested', 'refunded')),
                    refund_reason TEXT
                );
            """)

            courses = [
                ("C001", "Google ADK Fundamentals", 1999),
                ("C002", "LLMOps in Production", 2499),
                ("C003", "Advanced RAG Systems", 1999),
            ]
            conn.executemany("INSERT INTO courses VALUES (?, ?, ?)", courses)

            students = [
                ("STU001", "Rahul Sharma", "rahul@example.com"),
                ("STU002", "Priya Singh", "priya@example.com"),
                ("STU003", "Aman Gupta", "aman@example.com"),
                ("STU004", "Neha Verma", "neha@example.com"),
                ("STU005", "Vikram Mehta", "vikram@example.com"),
            ]
            conn.executemany("INSERT INTO students VALUES (?, ?, ?)", students)

            enrollments = [
                # Rahul: eligible, discounted purchase
                ("ENR001", "STU001", "C001", days_ago(2), 1499, 15, "active", None),
                # Rahul: outside 7-day window
                ("ENR002", "STU001", "C002", days_ago(10), 2499, 5, "active", None),
                # Priya: eligible
                ("ENR003", "STU002", "C001", days_ago(1), 1999, 10, "active", None),
                # Priya: completion over 20%
                ("ENR004", "STU002", "C003", days_ago(3), 1999, 45, "active", None),
                # Aman: refund already requested
                ("ENR005", "STU003", "C002", days_ago(2), 2499, 10, "refund_requested", "Purchased the wrong course"),
                # Aman: already refunded
                ("ENR006", "STU003", "C003", days_ago(4), 1999, 5, "refunded", "Changed my learning plans"),
                # Neha: exactly 20% completion, eligible
                ("ENR007", "STU004", "C001", days_ago(6), 1999, 20, "active", None),
                # Neha: both limits exceeded
                ("ENR008", "STU004", "C002", days_ago(12), 2499, 60, "active", None),
                # Vikram: eligible, no content consumed
                ("ENR009", "STU005", "C003", days_ago(1), 1999, 0, "active", None),
                # Vikram: recent purchase but too much completion
                ("ENR010", "STU005", "C002", days_ago(2), 2499, 80, "active", None),
            ]
            conn.executemany(
                "INSERT INTO enrollments VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                enrollments
            )

        print(f"NexusLearn database created: {DB_PATH}")
        for table in ("courses", "students", "enrollments"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {count} records")

    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()
