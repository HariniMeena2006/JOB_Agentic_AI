# backend/server.py
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sys
import os
import json

# Add the parent directory (where 'src' is) to the path
# This allows us to import modules from the 'src' folder
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the MongoDB functions from src/db.py
from src.db import init_db, get_jobs_by_status, update_job_status, get_all_jobs, delete_job

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

# Serve static frontend from Flask so we can run without npm
# Use '/static' to ensure API endpoints like '/jobs' are not shadowed by the static route
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='/static')
CORS(app)  # Enable CORS for all routes (CRITICAL for frontend connection)

# Initialize the database connection when the server starts
init_db()

# ======================================================================
# API ENDPOINTS MATCHING frontend/api.js
# ======================================================================

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/app.js')
def serve_app_js():
    return send_from_directory(FRONTEND_DIR, 'app.js')

@app.route('/api.js')
def serve_api_js():
    return send_from_directory(FRONTEND_DIR, 'api.js')

@app.route('/styles.css')
def serve_styles_css():
    return send_from_directory(FRONTEND_DIR, 'styles.css')

# =============================
# Helpers: transform DB -> UI
# =============================
def _map_status(raw_stage: str):
    stage = (raw_stage or '').lower()
    if stage in ('applied', 'application_submitted', 'submitted'):  
        return 'applied'
    if stage in ('waiting', 'saved', 'later'):
        return 'waiting'
    if stage in ('denied', 'rejected', 'archived'):
        return 'denied'
    # default bucket
    return 'new'

def _ensure_array(val):
    if not val:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        # split comma-separated skills if needed
        return [s.strip() for s in val.split(',') if s.strip()]
    return []

def transform_job(doc: dict) -> dict:
    """Convert a raw DB document into the shape the frontend expects."""
    # job id
    job_id = doc.get('job_id') or doc.get('id') or doc.get('uid')

    # title and company
    title = doc.get('job_title') or doc.get('title') or doc.get('role') or doc.get('position') or doc.get('subject') or doc.get('company') or 'Opportunity'
    company = doc.get('company') or doc.get('org') or doc.get('organization') or 'Unknown'

    # dates
    posted = doc.get('posted_date') or doc.get('email_date') or doc.get('date') or doc.get('created_at')
    if not posted:
        from datetime import datetime
        posted = datetime.utcnow().strftime('%Y-%m-%d')

    # details
    snippet = doc.get('snippet') or doc.get('summary') or doc.get('description') or doc.get('text') or ''
    link = doc.get('link') or doc.get('url') or doc.get('application_link') or '#'
    location = doc.get('location') or 'Remote'
    skills = _ensure_array(doc.get('skills'))

    # additional optional fields for details modal
    duration = doc.get('duration')
    start_date = doc.get('start_date')
    end_date = doc.get('end_date')
    stipend = doc.get('stipend')
    short_description = doc.get('short_description') or (snippet[:200] + '...' if snippet and len(snippet) > 200 else snippet)

    # status
    status = doc.get('status') or _map_status(doc.get('application_stage'))
    tracking_status = doc.get('tracking_status')

    return {
        'job_id': str(job_id) if job_id is not None else None,
        'job_title': title,
        'company': company,
        'posted_date': posted,
        'snippet': snippet,
        'link': link,
        'location': location,
        'skills': skills,
        'status': status,
        'tracking_status': tracking_status,
        # extras for details modal
        'duration': duration,
        'start_date': start_date,
        'end_date': end_date,
        'stipend': stipend,
        'short_description': short_description
    }

@app.route("/data", methods=["GET"])
def get_all_jobs_route():
    """Used by frontend loadInitialData(): returns transformed array of jobs."""
    try:
        jobs = get_all_jobs()
        out = [transform_job(j) for j in jobs]
        return jsonify(out)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/jobs", methods=["GET"])
def get_jobs():
    """Matches api.js: getJobs(status = "new")"""
    try:
        status = request.args.get("status", "new")
        # Use all jobs and filter by mapped status to support heterogeneous DB docs
        docs = get_all_jobs()
        mapped = [transform_job(j) for j in docs]
        filtered = [j for j in mapped if j.get('status') == status]
        return jsonify({"success": True, "data": filtered})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/apply/<string:job_id>", methods=["POST"])
def apply_to_job(job_id):
    """Matches api.js: applyToJob(jobId)"""
    # The initial tracking status for an applied job is 'pending'
    updated_job = update_job_status(job_id, new_status="applied", tracking_status="pending")
    
    if updated_job:
        return jsonify({"success": True, "data": updated_job})
    return jsonify({"success": False, "error": "Job not found"}), 404

# Permanently delete a job
@app.route("/delete/<string:job_id>", methods=["DELETE"])
def delete_job_route(job_id):
    try:
        ok = delete_job(job_id)
        if ok:
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Job not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/save/<string:job_id>", methods=["POST"])
def save_job_route(job_id):
    """Matches api.js: saveJob(jobId)"""
    # 'Waiting List' status is 'waiting'
    updated_job = update_job_status(job_id, new_status="waiting")
    
    if updated_job:
        return jsonify({"success": True, "data": updated_job})
    return jsonify({"success": False, "error": "Job not found"}), 404

@app.route("/deny/<string:job_id>", methods=["POST"])
def deny_job_route(job_id):
    """Matches api.js: denyJob(jobId, reason)"""
    data = request.get_json()
    reason = data.get("reason")
    
    updated_job = update_job_status(job_id, new_status="denied", reason=reason)
    
    if updated_job:
        return jsonify({"success": True, "data": updated_job})
    return jsonify({"success": False, "error": "Job not found"}), 404

# Update tracking status for an already-applied job
@app.route("/tracking/<string:job_id>", methods=["POST"])
def tracking_job_route(job_id):
    data = request.get_json()
    tracking_status = data.get("trackingStatus")
    updated_job = update_job_status(job_id, new_status="applied", tracking_status=tracking_status)

    if updated_job:
        return jsonify({"success": True, "data": updated_job})
    return jsonify({"success": False, "error": "Job not found"}), 404

# Move job between columns (new/applied/waiting/denied)
@app.route("/move/<string:job_id>", methods=["POST"])
def move_job_route(job_id):
    data = request.get_json()
    new_status = data.get("newStatus")
    updated_job = update_job_status(job_id, new_status=new_status)

    if updated_job:
        return jsonify({"success": True, "data": updated_job})
    return jsonify({"success": False, "error": "Job not found"}), 404

if __name__ == "__main__":
    # Ensure frontend uses this port: http://127.0.0.1:5000 (which is in api.js)
    app.run(port=5000, debug=True)