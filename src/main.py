from extract import gmail_login, get_latest_emails
from classifier import classify_email
from db import init_db, save_job

def main():
    print("🔐 Logging into Gmail...")
    service = gmail_login()

    print("📥 Fetching latest emails...")
    emails = get_latest_emails(service, max_results=10)

    init_db()

    for email in emails:
        email_text = email["subject"] + "\n" + email["body"]
        print("\n📝 Classifying:", email["subject"])

        result = classify_email(email_text)

        if result.get("is_relevant"):
            print("✅ Relevant job email found — saving...")
            save_job(result)
        else:
            print("❌ Not job-related.")

    print("\n🎉 DONE → Check data/output.db")

if __name__ == "__main__":
    main()
