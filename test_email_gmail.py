# test_email_gmail.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Gmail settings
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "sykuriyavar@gmail.com"  # ← YOUR GMAIL HERE
password = "bmwe bgzs dxpa uyeh"  # ← APP PASSWORD HERE (no spaces)
receiver_email = "sykuriyavar@gmail.com"  # ← SAME GMAIL

print("="*60)
print("Testing Gmail SMTP Connection")
print("="*60)

# Create message
msg = MIMEMultipart()
msg['From'] = f"Test Engineer Portal <{sender_email}>"
msg['To'] = receiver_email
msg['Subject'] = "🧪 Test Email from UAT Module"

html_body = """
<html>
<body style="font-family: Arial; padding: 20px;">
    <h2 style="color: #0066cc;">✅ Email Working!</h2>
    <p>Gmail SMTP is configured correctly! 🎉</p>
    <p>Sent at: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
</body>
</html>
"""

msg.attach(MIMEText(html_body, 'html'))

# Method 1: Try with STARTTLS
try:
    print("\n📧 Method 1: Trying SMTP with STARTTLS (port 587)...")
    context = ssl.create_default_context()
    
    with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
        server.ehlo()
        print("   Starting TLS...")
        server.starttls(context=context)
        server.ehlo()
        print("   Logging in...")
        server.login(sender_email, password)
        print("   Sending...")
        server.send_message(msg)
    
    print("\n" + "="*60)
    print("✅ EMAIL SENT SUCCESSFULLY! (Method 1)")
    print("="*60)
    print(f"📧 Check inbox: {receiver_email}")
    print("="*60)
    
except Exception as e:
    print(f"   ❌ Method 1 failed: {e}")
    
    # Method 2: Try with SSL directly (port 465)
    try:
        print("\n📧 Method 2: Trying SMTP_SSL (port 465)...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL(smtp_server, 465, context=context, timeout=30) as server:
            print("   Logging in...")
            server.login(sender_email, password)
            print("   Sending...")
            server.send_message(msg)
        
        print("\n" + "="*60)
        print("✅ EMAIL SENT SUCCESSFULLY! (Method 2)")
        print("="*60)
        print(f"📧 Check inbox: {receiver_email}")
        print("="*60)
        
    except Exception as e2:
        print(f"   ❌ Method 2 also failed: {e2}")
        print("\n" + "="*60)
        print("⚠️  BOTH METHODS FAILED")
        print("="*60)
        print("\nPossible issues:")
        print("1. App Password not generated correctly")
        print("2. 2-Step Verification not enabled")
        print("3. Firewall/Proxy blocking SMTP")
        print("4. Antivirus blocking connection")
        print("\nTry:")
        print("- Check App Password: https://myaccount.google.com/apppasswords")
        print("- Disable antivirus temporarily")
        print("- Try from a different network")