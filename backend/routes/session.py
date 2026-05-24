"""Session routes — start, end, status, class sessions."""

import logging
import uuid
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from database import db
from models.attendance import AttendanceRecord
from models.class_model import Class, Enrollment
from models.session import Session
from models.user import User
from middleware.auth_middleware import require_role
from services import attendance_engine, firebase_sync, notifications

logger = logging.getLogger(__name__)

session_bp = Blueprint("session", __name__)


@session_bp.route("/start", methods=["POST"])
@require_role("teacher")
def start_session():
    """Start a new attendance session for a class.

    Generates UUID, creates attendance_records for all enrolled students,
    and syncs to Firebase.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required", "status": 400}), 400

    class_id = data.get("class_id")
    mode = data.get("mode", "").strip()
    start_time_str = data.get("start_time")

    if not class_id or not mode:
        return (
            jsonify({"error": "class_id and mode are required", "status": 400}),
            400,
        )

    if mode not in ("Strict", "Activity"):
        return (
            jsonify(
                {"error": "mode must be 'Strict' or 'Activity'", "status": 422}
            ),
            422,
        )

    # Validate class exists and teacher owns it
    cls = Class.query.get(class_id)
    if not cls:
        return jsonify({"error": "Class not found", "status": 404}), 404

    teacher_id = g.current_user["user_id"]
    if cls.teacher_id != teacher_id:
        return (
            jsonify({"error": "You are not the teacher of this class", "status": 403}),
            403,
        )

    # Parse start time
    if start_time_str:
        try:
            start_time = datetime.fromisoformat(start_time_str)
        except ValueError:
            return (
                jsonify(
                    {"error": "start_time must be a valid ISO 8601 datetime", "status": 422}
                ),
                422,
            )
    else:
        start_time = datetime.now(timezone.utc)

    # Determine threshold
    from flask import current_app

    if mode == "Strict":
        threshold = current_app.config.get("STRICT_MODE_THRESHOLD", 0.80)
    else:
        threshold = current_app.config.get("ACTIVITY_MODE_THRESHOLD", 0.55)

    # Create session
    session_id = str(uuid.uuid4())
    session = Session(
        session_id=session_id,
        class_id=class_id,
        teacher_id=teacher_id,
        mode=mode,
        start_time=start_time,
        status="ACTIVE",
        threshold_percent=threshold,
    )
    db.session.add(session)

    # Create attendance_records for all enrolled students (default Absent)
    enrollments = Enrollment.query.filter_by(class_id=class_id).all()
    for enrollment in enrollments:
        record = AttendanceRecord(
            student_id=enrollment.student_id,
            session_id=session_id,
            total_duration_seconds=0,
            threshold_required=None,
            status="Absent",
        )
        db.session.add(record)

    db.session.commit()

    # Sync to Firebase (best-effort)
    firebase_sync.sync_session_start(
        session_id,
        {"status": "ACTIVE", "class_id": class_id, "mode": mode},
    )

    return (
        jsonify(
            {
                "session_id": session_id,
                "threshold_percent": threshold,
                "enrolled_count": len(enrollments),
            }
        ),
        200,
    )


@session_bp.route("/end", methods=["POST"])
@require_role("teacher")
def end_session():
    """End an active session — finalize attendance and notify absent students."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required", "status": 400}), 400

    session_id = data.get("session_id", "").strip()
    if not session_id:
        return jsonify({"error": "session_id is required", "status": 400}), 400

    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found", "status": 404}), 404

    teacher_id = g.current_user["user_id"]
    if session.teacher_id != teacher_id:
        return (
            jsonify({"error": "You are not the teacher of this session", "status": 403}),
            403,
        )

    if session.status != "ACTIVE":
        return (
            jsonify({"error": "Session is not active", "status": 400}),
            400,
        )

    # Set end time
    session.end_time = datetime.now(timezone.utc)

    # Calculate attendance for all students
    summary = attendance_engine.calculate_all(session_id)

    # Close session
    session.status = "CLOSED"
    db.session.commit()

    # Sync to Firebase (best-effort)
    firebase_sync.sync_session_end(session_id, summary)
    firebase_sync.sync_attendance_summary(session_id, summary.get("details", []))

    # Send FCM absence notifications to absent students
    absent_records = AttendanceRecord.query.filter_by(
        session_id=session_id, status="Absent"
    ).all()

    class_name = session.class_.class_name if session.class_ else "Unknown"

    for record in absent_records:
        student = record.student
        if student and student.user:
            device_token = student.user.device_token
            student_name = student.user.fullname
            notifications.send_absence_notification(
                device_token=device_token,
                student_name=student_name,
                session_id=session_id,
                class_name=class_name,
            )

    return (
        jsonify(
            {
                "session_id": session_id,
                "summary": {
                    "present": summary["present"],
                    "absent": summary["absent"],
                    "total": summary["total"],
                },
            }
        ),
        200,
    )


@session_bp.route("/status/<session_id>", methods=["GET"])
@require_role("teacher", "admin")
def session_status(session_id):
    """Return session details and current attendance summary."""
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found", "status": 404}), 404

    summary = attendance_engine.get_session_summary(session_id)

    return (
        jsonify(
            {
                "session_id": session.session_id,
                "status": session.status,
                "mode": session.mode,
                "class_id": session.class_id,
                "class_name": session.class_.class_name if session.class_ else None,
                "start_time": (
                    session.start_time.isoformat() if session.start_time else None
                ),
                "end_time": (
                    session.end_time.isoformat() if session.end_time else None
                ),
                "liveCount": summary["present"],
                "present_count": summary["present"],
                "absent_count": summary["absent"],
                "total": summary["total"],
            }
        ),
        200,
    )


@session_bp.route("/class/<int:class_id>", methods=["GET"])
@require_role("teacher", "admin")
def sessions_by_class(class_id):
    """Return all sessions for a class with summaries."""
    cls = Class.query.get(class_id)
    if not cls:
        return jsonify({"error": "Class not found", "status": 404}), 404

    sessions = (
        Session.query.filter_by(class_id=class_id)
        .order_by(Session.start_time.desc())
        .all()
    )

    results = []
    for s in sessions:
        summary = attendance_engine.get_session_summary(s.session_id)
        session_data = s.to_dict()
        session_data["summary"] = {
            "present": summary["present"],
            "absent": summary["absent"],
            "total": summary["total"],
        }
        results.append(session_data)

    return jsonify({"class_id": class_id, "class_name": cls.class_name, "sessions": results}), 200
