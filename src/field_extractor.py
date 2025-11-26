# field_extractor.py
import re
import uuid

OPTIONAL_FIELDS = ["skills", "duration", "start_date", "end_date", "stipend", "short_description"]

def extract_fields_from_email(subject, body):
    """Extract structured fields from the email"""
    result = {}

    # Title and company from subject
    parts = subject.split("–")
    result["title"] = parts[0].strip() if len(parts) > 0 else "Unknown"
    result["company"] = parts[1].strip() if len(parts) > 1 else "Unknown"

    # Location
    loc = re.search(r"Location:\s*(.+)", body)
    result["location"] = loc.group(1).strip() if loc else None

    # Duration
    dur = re.search(r"Duration:\s*(.+)", body)
    result["duration"] = dur.group(1).strip() if dur else None

    # Stipend
    stipend = re.search(r"Stipend:\s*(.+)", body)
    result["stipend"] = stipend.group(1).strip() if stipend else None

    # Short description (first 200 characters)
    text = " ".join(body.split())
    result["short_description"] = text[:200] + "..." if len(text) > 200 else text

    # Generate unique job ID
    result["job_id"] = str(uuid.uuid4())

    return result
