import os
import shutil
from datetime import datetime, timedelta
from .db import get_db, DATABASE_PATH

# ─────────────────────────────────────────
# 1. Backup the SQLite database
# ─────────────────────────────────────────
def backup_database():
    try:
        backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"attendance_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        shutil.copy2(DATABASE_PATH, backup_path)

        return {
            "status": "success",
            "backup_file": backup_filename,
            "backup_path": backup_path,
            "created_at": timestamp
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ─────────────────────────────────────────
# 2. Clean up old session data
# ─────────────────────────────────────────
def cleanup_old_sessions(days=90):
    with get_db() as conn:
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # Delete old attendance logs first (foreign key order)
        cursor.execute('''
            DELETE FROM attendance_logs
            WHERE session_id IN (
                SELECT id FROM sessions
                WHERE session_date < ?
            )
        ''', (cutoff_date,))
        logs_deleted = cursor.rowcount

        # Delete old sessions
        cursor.execute('''
            DELETE FROM sessions
            WHERE session_date < ?
        ''', (cutoff_date,))
        sessions_deleted = cursor.rowcount

        return {
            "status": "success",
            "cutoff_date": cutoff_date,
            "sessions_deleted": sessions_deleted,
            "logs_deleted": logs_deleted
        }


# ─────────────────────────────────────────
# 3. Verify all foreign keys are working
# ─────────────────────────────────────────
def verify_foreign_keys():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()

        if violations:
            return {
                "status": "violations found",
                "violations": [dict(row) for row in violations]
            }

        return {
            "status": "ok",
            "message": "All foreign keys are valid"
        }


# ─────────────────────────────────────────
# 4. Get database statistics
# ─────────────────────────────────────────
def get_database_stats():
    with get_db() as conn:
        cursor = conn.cursor()

        tables = [
            'users', 'students', 'classes', 'enrollments',
            'sessions', 'attendance_logs', 'attendance_records',
            'face_data', 'waiver_requests', 'notifications'
        ]

        stats = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cursor.fetchone()['count']

        # Get database file size
        db_size = os.path.getsize(DATABASE_PATH)

        return {
            "status": "ok",
            "table_counts": stats,
            "database_size_bytes": db_size,
            "database_size_kb": round(db_size / 1024, 2)
        }


# ─────────────────────────────────────────
# 5. Clean up unread old notifications
# ─────────────────────────────────────────
def cleanup_old_notifications(days=30):
    with get_db() as conn:
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            DELETE FROM notifications
            WHERE is_read = 1
            AND created_at < ?
        ''', (cutoff_date,))

        deleted = cursor.rowcount

        return {
            "status": "success",
            "notifications_deleted": deleted,
            "cutoff_date": cutoff_date
        }