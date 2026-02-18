# test_email_manual.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime  # ← ADD THIS LINE

# Your email settings
smtp_server = "smtp.office365.com"
smtp_port = 587
sender_email = "sykuriyavar@gmail.com"
password = "Sk4347@Testing"  # ⚠️ CHANGE THIS PASSWORD AFTER TESTING!
receiver_email = "nhyk@novonordisk.com"

# Create message
msg = MIMEMultipart()
msg['From'] = f"Test Engineer Portal <{sender_email}>"
msg['To'] = receiver_email
msg['Subject'] = "🧪 Test Email from UAT Module"

html_body = """
<html>
<body style="font-family: Arial; padding: 20px;">
    <h2 style="color: #0066cc;">✅ Email Configuration Working!</h2>
    <p>This is a test email from your Test Engineer Portal.</p>
    <p>If you received this, your email setup is correct! 🎉</p>
    <hr>
    <p style="color: gray; font-size: 12px;">
        Sent at: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
    </p>
</body>
</html>
"""

msg.attach(MIMEText(html_body, 'html'))

# Send email
try:
    print("Connecting to SMTP server...")
    with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
        print("Starting TLS...")
        server.starttls()
        print("Logging in...")
        server.login(sender_email, password)
        print("Sending email...")
        server.send_message(msg)
    
    print("\n" + "="*60)
    print("✅ EMAIL SENT SUCCESSFULLY!")
    print("="*60)
    print(f"📧 Check your inbox: {receiver_email}")
    print("📁 Also check SPAM/JUNK folder!")
    print("📁 Check Sent Items in Outlook web")
    print("="*60 + "\n")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Authentication failed: {e}")
    print("Check your username and password!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()