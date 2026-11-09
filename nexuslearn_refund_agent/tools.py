import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from google.adk.tools import ToolContext

DB_PATH = Path(__file__).resolve().parent / "nexuslearn.db"
REFUND_WINDOW_DAYS = 7
MAX_COMPLETION_PERCENT = 20

@contextmanager
def database():
    if not DB_PATH.exists():
        raise FileNotFoundError("nexuslearn.db not found. Run setup_database.py first.")
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def find_enrollment(conn, enrollment_id, student_id):
    return conn.execute(
        """
        SELECT e.*, c.course_name
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        WHERE e.enrollment_id = ? AND e.student_id = ?
        """,
        (enrollment_id, student_id),
    ).fetchone()

def email_required():
    return {
        "status": "email_required",
        "message": "Please ask the user for the email address used to purchase their NexusLearn course.",
    }

def enrollment_not_found():
    return {
        "status": "not_found",
        "message": "This enrollment was not found for the selected student.",
    }

def evaluate_eligibility(enrollment):
    purchased_at = datetime.fromisoformat(enrollment["purchased_at"])
    age = datetime.now(timezone.utc) - purchased_at
    reasons = []
    if enrollment["status"] != "active":
        reasons.append(f"Enrollment status is already {enrollment['status']}.")
    if age < timedelta(0):
        reasons.append("Purchase date is in the future. Review required.")
    elif age > timedelta(days=REFUND_WINDOW_DAYS):
        reasons.append("Purchase is outside the 7-day refund window.")
    if enrollment["completion_percent"] > MAX_COMPLETION_PERCENT:
        reasons.append("Course completion exceeds 20%.")
    eligible = not reasons
    return {
        "enrollment_id": enrollment["enrollment_id"],
        "course_name": enrollment["course_name"],
        "eligible": eligible,
        "reasons": reasons or ["Purchase is within 7 days and completion is at most 20%."],
        "refund_amount": enrollment["amount_paid"] if eligible else 0,
        "currency": "INR",
    }

def get_refund_policy() -> dict:
    """Return NexusLearn's refund policy."""
    return {
        "refund_window_days": REFUND_WINDOW_DAYS,
        "maximum_completion_percent": MAX_COMPLETION_PERCENT,
        "refund_amount": "Full actual amount paid",
        "reason_required": True,
        "reason_affects_eligibility": False,
        "boundaries_inclusive": True,
    }

def identify_student(email: str, tool_context: ToolContext) -> dict:
    """Look up a student by their registered NexusLearn email.

    Args:
        email: Email explicitly provided by the user.
    """
    tool_context.state["student_id"] = None
    tool_context.state["student_email"] = None
    email = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return {"status": "invalid_email", "message": "Please ask the user for a valid email address."}
    with database() as conn:
        student = conn.execute(
            "SELECT student_id, name, email FROM students WHERE email = ? COLLATE NOCASE",
            (email,),
        ).fetchone()
    if student is None:
        return {"status": "not_found", "message": "No student found with this email. Ask the user to check their registered email."}
    tool_context.state["student_id"] = student["student_id"]
    tool_context.state["student_email"] = student["email"]
    return {"status": "success", "name": student["name"], "email": student["email"]}

def get_my_enrollments(tool_context: ToolContext) -> dict:
    """Return all enrollments for the currently identified student."""
    student_id = tool_context.state.get("student_id")
    if not student_id:
        return email_required()
    with database() as conn:
        rows = conn.execute(
            """
            SELECT e.enrollment_id, c.course_name, e.purchased_at,
                   e.amount_paid, e.completion_percent, e.status
            FROM enrollments e
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.student_id = ?
            ORDER BY e.enrollment_id
            """,
            (student_id,),
        ).fetchall()
    return {"status": "success", "currency": "INR", "enrollments": [dict(r) for r in rows]}

def check_refund_eligibility(enrollment_id: str, tool_context: ToolContext) -> dict:
    """Check if an enrollment qualifies for a refund.

    Args:
        enrollment_id: Enrollment ID from get_my_enrollments.
    """
    student_id = tool_context.state.get("student_id")
    if not student_id:
        return email_required()
    with database() as conn:
        enrollment = find_enrollment(conn, enrollment_id, student_id)
        if enrollment is None:
            return enrollment_not_found()
        return {"status": "success", **evaluate_eligibility(enrollment)}

def request_refund(enrollment_id: str, reason: str, tool_context: ToolContext) -> dict:
    """Submit a refund request after user confirmation.

    Args:
        enrollment_id: Enrollment ID from get_my_enrollments.
        reason: Refund reason provided by the user. Never invent one.
    """
    student_id = tool_context.state.get("student_id")
    if not student_id:
        return email_required()
    reason = reason.strip()
    if not reason:
        return {"status": "reason_required", "message": "Ask the user for their refund reason."}
    decision = check_refund_eligibility(enrollment_id, tool_context)
    if decision["status"] != "success":
        return decision
    if not decision["eligible"]:
        return {**decision, "status": "ineligible"}
    confirmation = tool_context.tool_confirmation
    if confirmation is None:
        tool_context.request_confirmation(
            hint=(
                f"Submit a full refund for {decision['course_name']} ({enrollment_id}) "
                f"of INR {decision['refund_amount']}? Reason: {reason}. "
                "This demo does not transfer money."
            ),
        )
        return {"status": "awaiting_confirmation"}
    if not confirmation.confirmed:
        return {"status": "cancelled", "message": "No refund request was saved."}
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        enrollment = find_enrollment(conn, enrollment_id, student_id)
        if enrollment is None:
            return enrollment_not_found()
        decision = evaluate_eligibility(enrollment)
        if not decision["eligible"]:
            return {"status": "ineligible", **decision}
        conn.execute(
            """
            UPDATE enrollments
            SET status = 'refund_requested', refund_reason = ?
            WHERE enrollment_id = ? AND student_id = ? AND status = 'active'
            """,
            (reason, enrollment_id, student_id),
        )
        return {
            "status": "refund_requested",
            "enrollment_id": enrollment_id,
            "course_name": enrollment["course_name"],
            "refund_amount": enrollment["amount_paid"],
            "currency": "INR",
            "reason": reason,
            "message": "Refund request saved. No money has been transferred (demo only).",
        }

def get_refund_status(enrollment_id: str, tool_context: ToolContext) -> dict:
    """Get the current refund status for a given enrollment.

    Args:
        enrollment_id: Enrollment ID belonging to the selected student.
    """
    student_id = tool_context.state.get("student_id")
    if not student_id:
        return email_required()
    with database() as conn:
        enrollment = find_enrollment(conn, enrollment_id, student_id)
        if enrollment is None:
            return enrollment_not_found()
        return {
            "status": enrollment["status"],
            "enrollment_id": enrollment_id,
            "course_name": enrollment["course_name"],
            "refund_reason": enrollment["refund_reason"],
            "amount_paid": enrollment["amount_paid"],
            "currency": "INR",
            "simulation": True,
        }