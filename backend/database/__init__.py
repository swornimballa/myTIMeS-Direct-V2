from .db import init_db, get_db
from .queries import (
    get_student_attendance,
    get_attendance_percentage,
    get_at_risk_students,
    update_attendance_record
)
from .analytics import (
    get_total_sessions_per_class,
    get_average_attendance_per_class,
    get_students_with_most_absences,
    get_attendance_trends,
    get_overall_summary
)
from .export import (
    export_attendance_csv,
    export_summary_csv,
    export_attendance_pdf
)
from .maintenance import (
    backup_database,
    cleanup_old_sessions,
    verify_foreign_keys,
    get_database_stats,
    cleanup_old_notifications
)

__all__ = [
    'init_db', 'get_db',
    'get_student_attendance', 'get_attendance_percentage',
    'get_at_risk_students', 'update_attendance_record',
    'get_total_sessions_per_class', 'get_average_attendance_per_class',
    'get_students_with_most_absences', 'get_attendance_trends',
    'get_overall_summary',
    'export_attendance_csv', 'export_summary_csv', 'export_attendance_pdf',
    'backup_database', 'cleanup_old_sessions', 'verify_foreign_keys',
    'get_database_stats', 'cleanup_old_notifications'
]