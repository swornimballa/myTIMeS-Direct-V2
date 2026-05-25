import csv
import os
from io import StringIO, BytesIO
from datetime import datetime
from .db import get_db

# ─────────────────────────────────────────
# 1. Export attendance data as CSV
# ─────────────────────────────────────────
def export_attendance_csv(class_id=None):
    with get_db() as conn:
        cursor = conn.cursor()

        query = '''
            SELECT 
                u.full_name as student_name,
                st.student_id as student_code,
                c.class_name,
                c.class_code,
                s.session_date,
                s.start_time,
                al.status,
                al.marked_at
            FROM attendance_logs al
            JOIN students st ON al.student_id = st.id
            JOIN users u ON st.user_id = u.id
            JOIN sessions s ON al.session_id = s.id
            JOIN classes c ON s.class_id = c.id
        '''

        if class_id:
            query += ' WHERE c.id = ?'
            cursor.execute(query + ' ORDER BY s.session_date DESC', (class_id,))
        else:
            cursor.execute(query + ' ORDER BY s.session_date DESC')

        rows = cursor.fetchall()

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Student Name',
            'Student ID',
            'Class Name',
            'Class Code',
            'Session Date',
            'Start Time',
            'Status',
            'Marked At'
        ])

        # Write data rows
        for row in rows:
            writer.writerow([
                row['student_name'],
                row['student_code'],
                row['class_name'],
                row['class_code'],
                row['session_date'],
                row['start_time'],
                row['status'],
                row['marked_at']
            ])

        return output.getvalue()


# ─────────────────────────────────────────
# 2. Export attendance summary as CSV
# ─────────────────────────────────────────
def export_summary_csv(class_id=None):
    with get_db() as conn:
        cursor = conn.cursor()

        query = '''
            SELECT 
                u.full_name as student_name,
                st.student_id as student_code,
                c.class_name,
                c.class_code,
                ar.total_sessions,
                ar.attended_sessions,
                ar.attendance_percentage,
                CASE 
                    WHEN ar.attendance_percentage >= 75 THEN 'Safe'
                    ELSE 'At Risk'
                END as status
            FROM attendance_records ar
            JOIN students st ON ar.student_id = st.id
            JOIN users u ON st.user_id = u.id
            JOIN classes c ON ar.class_id = c.id
        '''

        if class_id:
            query += ' WHERE c.id = ?'
            cursor.execute(query + ' ORDER BY ar.attendance_percentage ASC', (class_id,))
        else:
            cursor.execute(query + ' ORDER BY ar.attendance_percentage ASC')

        rows = cursor.fetchall()

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Student Name',
            'Student ID',
            'Class Name',
            'Class Code',
            'Total Sessions',
            'Attended Sessions',
            'Attendance %',
            'Status'
        ])

        # Write data rows
        for row in rows:
            writer.writerow([
                row['student_name'],
                row['student_code'],
                row['class_name'],
                row['class_code'],
                row['total_sessions'],
                row['attended_sessions'],
                f"{row['attendance_percentage']:.2f}%",
                row['status']
            ])

        return output.getvalue()


# ─────────────────────────────────────────
# 3. Export attendance as PDF
# ─────────────────────────────────────────
def export_attendance_pdf(class_id=None):
    try:
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        with get_db() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT 
                    u.full_name as student_name,
                    st.student_id as student_code,
                    c.class_name,
                    c.class_code,
                    ar.total_sessions,
                    ar.attended_sessions,
                    ar.attendance_percentage
                FROM attendance_records ar
                JOIN students st ON ar.student_id = st.id
                JOIN users u ON st.user_id = u.id
                JOIN classes c ON ar.class_id = c.id
            '''

            if class_id:
                query += ' WHERE c.id = ?'
                cursor.execute(query + ' ORDER BY ar.attendance_percentage ASC', (class_id,))
            else:
                cursor.execute(query + ' ORDER BY ar.attendance_percentage ASC')

            rows = cursor.fetchall()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title = Paragraph(
            f"Attendance Report — Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles['Title']
        )
        elements.append(title)
        elements.append(Spacer(1, 20))

        # Table header
        data = [['Student Name', 'Student ID', 'Class', 'Code',
                 'Total Sessions', 'Attended', 'Attendance %']]

        # Table rows
        for row in rows:
            data.append([
                row['student_name'],
                row['student_code'],
                row['class_name'],
                row['class_code'],
                str(row['total_sessions']),
                str(row['attended_sessions']),
                f"{row['attendance_percentage']:.2f}%"
            ])

        # Build table
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))

        elements.append(table)
        doc.build(elements)

        return buffer.getvalue()

    except ImportError:
        return None