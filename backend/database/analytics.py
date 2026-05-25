from .db import get_db

# ─────────────────────────────────────────
# 1. Total sessions per class
# ─────────────────────────────────────────
def get_total_sessions_per_class():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                c.class_code,
                c.class_name,
                COUNT(s.id) as total_sessions
            FROM classes c
            LEFT JOIN sessions s ON c.id = s.class_id
            GROUP BY c.id
            ORDER BY total_sessions DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]


# ─────────────────────────────────────────
# 2. Average attendance rate per class
# ─────────────────────────────────────────
def get_average_attendance_per_class():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                c.class_code,
                c.class_name,
                ROUND(AVG(ar.attendance_percentage), 2) as avg_attendance,
                COUNT(ar.student_id) as total_students
            FROM classes c
            LEFT JOIN attendance_records ar ON c.id = ar.class_id
            GROUP BY c.id
            ORDER BY avg_attendance DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]


# ─────────────────────────────────────────
# 3. Students with most absences
# ─────────────────────────────────────────
def get_students_with_most_absences():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                u.full_name,
                st.student_id,
                COUNT(al.id) as total_absences
            FROM attendance_logs al
            JOIN students st ON al.student_id = st.id
            JOIN users u ON st.user_id = u.id
            WHERE al.status = 'absent'
            GROUP BY al.student_id
            ORDER BY total_absences DESC
            LIMIT 10
        ''')
        return [dict(row) for row in cursor.fetchall()]


# ─────────────────────────────────────────
# 4. Attendance trends over time
# ─────────────────────────────────────────
def get_attendance_trends(class_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                s.session_date,
                COUNT(al.id) as total_marked,
                SUM(CASE WHEN al.status IN ('present', 'late') THEN 1 ELSE 0 END) as present_count,
                SUM(CASE WHEN al.status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                ROUND(
                    SUM(CASE WHEN al.status IN ('present', 'late') THEN 1 ELSE 0 END) * 100.0 / 
                    COUNT(al.id), 2
                ) as attendance_rate
            FROM sessions s
            LEFT JOIN attendance_logs al ON s.id = al.session_id
            WHERE s.class_id = ?
            GROUP BY s.session_date
            ORDER BY s.session_date ASC
        ''', (class_id,))
        return [dict(row) for row in cursor.fetchall()]


# ─────────────────────────────────────────
# 5. Overall summary statistics
# ─────────────────────────────────────────
def get_overall_summary():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='student'")
        total_students = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM classes")
        total_classes = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM sessions")
        total_sessions = cursor.fetchone()['total']

        cursor.execute('''
            SELECT ROUND(AVG(attendance_percentage), 2) as avg
            FROM attendance_records
        ''')
        avg_attendance = cursor.fetchone()['avg'] or 0.0

        return {
            "total_students": total_students,
            "total_classes": total_classes,
            "total_sessions": total_sessions,
            "overall_avg_attendance": avg_attendance
        }