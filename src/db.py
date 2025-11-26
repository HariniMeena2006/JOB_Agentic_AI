# db.py
from pymongo import MongoClient

collection = None

def init_db():
    """Initialize MongoDB Atlas connection"""
    global collection
    # Replace with your Atlas connection string
    client = MongoClient(
        "mongodb+srv://harinimeena235_db_user:LKduLS6xWlo79efz@cluster0.ywkcim9.mongodb.net/job_emails_db?retryWrites=true&w=majority"
    )
    db = client["job_emails_db"]
    collection = db["jobs"]
    print("✅ MongoDB Atlas initialized!")

def save_job(job_data):
    """Save job data to MongoDB"""
    global collection
    # Use update_one with upsert=True to prevent duplicates if running main multiple times
    collection.update_one(
        {'job_id': job_data['job_id']},
        {'$set': job_data},
        upsert=True
    )
    print(f"💾 Saved/Updated job → {job_data.get('title')} at {job_data.get('company')}")

# 🚀 NEW FUNCTION TO SUPPORT FLASK API 🚀
def get_jobs_by_status(status):
    """Fetch jobs from MongoDB based on their status."""
    global collection
    if collection is None:
        init_db()
    
    # MongoDB returns BSON objects, we convert to list of dicts for JSON serialization
    jobs = list(collection.find({"status": status}, {'_id': 0})) 
    return jobs

# 🚀 NEW FUNCTION TO HANDLE JOB ACTIONS 🚀
def update_job_status(job_id, new_status, reason=None, tracking_status=None):
    """Update the status of a specific job."""
    global collection
    if collection is None:
        init_db()

    update_fields = {"status": new_status}
    if reason is not None:
        update_fields["deny_reason"] = reason
    if tracking_status is not None:
        update_fields["tracking_status"] = tracking_status
    
    # Support job_id stored as either string or integer
    try:
        int_id = int(job_id)
    except (ValueError, TypeError):
        int_id = None

    id_filter = {"job_id": {"$in": [job_id] + ([int_id] if int_id is not None else [])}}

    result = collection.update_one(
        id_filter,
        {"$set": update_fields}
    )
    # Fetch the updated document to return to the frontend
    updated_job = collection.find_one(id_filter, {'_id': 0})
    return updated_job

# 🚀 NEW: Fetch all jobs (used by frontend loadInitialData /data)
def get_all_jobs():
    """Return all jobs from MongoDB as a list of dicts without _id field."""
    global collection
    if collection is None:
        init_db()
    return list(collection.find({}, {'_id': 0}))

# 🚀 NEW: Delete a job by job_id
def delete_job(job_id):
    """Delete a job from MongoDB by job_id. Returns True if deleted."""
    global collection
    if collection is None:
        init_db()

    # Support job_id stored as either string or integer
    try:
        int_id = int(job_id)
    except (ValueError, TypeError):
        int_id = None

    id_filter = {"job_id": {"$in": [job_id] + ([int_id] if int_id is not None else [])}}
    res = collection.delete_one(id_filter)
    return res.deleted_count > 0