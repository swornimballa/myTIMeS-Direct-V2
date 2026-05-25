from flask import Blueprint, jsonify
from database import get_db

health_bp = Blueprint('health', __name__)

@health_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "pong"}), 200

@health_bp.route('/', methods=['GET'])
def health():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            db_status = "ok"
    except Exception as e:
        tables = []
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "ok",
        "message": "backend is running",
        "database_check": {
            "status": db_status,
            "tables_found": tables
        }
    }), 200