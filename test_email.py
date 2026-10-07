import os
from app import create_app
from app.services.ses_service import ses_service

def test_ses():
    print("Initializing Flask App Context...")
    app = create_app()
    
    with app.app_context():
        email = "karan2k212@gmail.com"
        print(f"Sending test email to {email}...")
        
        success = ses_service.send_email(
            to_addresses=[email],
            subject="AWS Project - SES Test Email",
            body_text="Hello! If you are reading this, your Amazon SES integration is working perfectly for your project.",
            sender_email=email
        )
        
        if success:
            print(f"\n✅ Success! An email has been successfully dispatched to {email}.")
        else:
            print("\n❌ Failed to send email. Ensure the email is verified in the SES Sandbox.")

if __name__ == "__main__":
    test_ses()
