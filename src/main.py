# main.py
from extract import gmail_login, get_latest_emails
from db import init_db, save_job
from field_extractor import extract_fields_from_email, OPTIONAL_FIELDS
from classifier import classify_email

MIN_REQUIRED_FIELDS = ["title", "company", "location"]

def main():
    print("🔐 Logging into Gmail...")
    service = gmail_login()

    print("📥 Fetching latest emails...")
    emails = get_latest_emails(service, max_results=50)

    init_db()

    for email in emails:
        email_text = email["subject"] + "\n" + email["body"]
        print("\n📝 Processing:", email["subject"])

        # Step 1: AI-based relevance check
        result = classify_email(email_text)
        if not result["is_relevant"]:
            print(f"❌ Skipped: {email['subject']}")
            continue

        # Step 2: Extract structured fields if AI didn't extract them
        if "title" not in result or "company" not in result or "location" not in result:
            extracted = extract_fields_from_email(email["subject"], email["body"])
            result.update(extracted)

        # Step 3: Ensure optional fields exist
        for field in OPTIONAL_FIELDS:
            if field not in result:
                result[field] = None

        # Step 4: Save if minimum required fields exist
        if all(result.get(f) for f in MIN_REQUIRED_FIELDS):
            save_job(result)
            print(f"✅ Saved: {result['title']} at {result['company']}")
        else:
            print(f"❌ Skipped (missing required fields): {email['subject']}")

    print("\n🎉 DONE → Check MongoDB collection 'jobs'")

if __name__ == "__main__":
    main()
