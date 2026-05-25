from .db import get_db

# ─────────────────────────────────────────
# 1. Get all attendance records for a student
# ─────────────────────────────────────────
def get_student_attendance(student_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                al.id,
                al.status,
                al.marked_at,
                s.session_date,
                s.start_time,
                s.end_time,
                c.class_name,
                c.class_code
            FROM attendance_logs al
            JOIN sessions s ON al.session_id = s.id
            JOIN classes c ON s.class_id = c.id
            WHERE al.student_id = ?
            ORDER BY s.session_date DESC
        ''', (student_id,))
        return [dict(row) for row in cursor.fetchall()]


# ─────────────────────────────────────────
# 2. Get attendance percentage per student per class
# ─────────────────────────────────────────
def get_attendance_percentage(student_id, class_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                attendance_percentage,
                total_sessions,
                attended_sessions
            FROM attendance_records
            WHERE student_id = ? AND class_id = ?
        ''', (student_id, class_id))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {
            "attendance_percentage": 0.0,
            "total_sessions": 0,
            "attended_sessions": 0
        }


# ─────────────────────────────────────────
# 3. Find at-risk students (below 75% attendance)
# ─────────────────────────────────────────
def get_at_risk_students():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                u.full_name,
                u.email,
                st.student_id,
                c.class_name,
                c.class_code,
                ar.attendance_percentage,
                ar.total_sessions,
                ar.attended_sessions
            FROM attendance_records ar
            JOIN students st ON ar.student_id = st.id
            JOIN users u ON st.user_id = u.id
            JOIN classes c ON ar.class_id = c.id
            WHERE ar.attendance_percentage < 75.0
            ORDER BY ar.attendance_percentage ASC
        ''')
        return [dict(row) for row in cursor.fetchall()]


# ─────────────────────────────────────────
# 4. Update attendance record after each session
# ─────────────────────────────────────────
def update_attendance_record(student_id, class_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN al.status IN ('present', 'late') THEN 1 ELSE 0 END) as attended
            FROM attendance_logs al
            JOIN sessions s ON al.session_id = s.id
            WHERE al.student_id = ? AND s.class_id = ?
        ''', (student_id, class_id))
        row = cursor.fetchone()
        total = row['total'] or 0
        attended = row['attended'] or 0
        percentage = (attended / total * 100) if total > 0 else 0.0

        cursor.execute('''
            INSERT INTO attendance_records 
                (student_id, class_id, total_sessions, attended_sessions, attendance_percentage)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(student_id, class_id) DO UPDATE SET
                total_sessions = ?,
                attended_sessions = ?,
                attendance_percentage = ?,
                last_updated = CURRENT_TIMESTAMP
        ''', (student_id, class_id, total, attended, percentage,
              total, attended, percentage))