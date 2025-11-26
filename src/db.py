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
    collection.insert_one(job_data)
    print(f"💾 Saved job → {job_data.get('title')} at {job_data.get('company')}")
