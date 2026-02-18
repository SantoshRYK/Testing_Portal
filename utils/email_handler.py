"""
Email handler for sending notifications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Union
from flask import current_app
import traceback
from datetime import datetime


def send_email(
    to_email: Union[str, List[str]], 
    subject: str, 
    body_html: str, 
    from_email: Optional[str] = None,
    cc_emails: Optional[List[str]] = None
) -> dict:
    """
    Send email notification using Outlook/Office 365
    
    Args:
        to_email: Recipient email address or list of addresses
        subject: Email subject
        body_html: HTML body content
        from_email: Sender email (optional, uses config if not provided)
        cc_emails: List of CC email addresses (optional)
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        # Check if email is enabled
        if not current_app.config.get('EMAIL_ENABLED', False):
            print(f"\n{'='*60}")
            print(f"📧 EMAIL NOTIFICATION (Disabled in config)")
            print(f"{'='*60}")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body:\n{body_html[:200]}...")
            print(f"{'='*60}\n")
            return {
                'success': False,
                'message': 'Email is disabled in configuration'
            }
        
        # Get email configuration
        smtp_server = current_app.config.get('MAIL_SERVER')
        smtp_port = current_app.config.get('MAIL_PORT')
        smtp_username = current_app.config.get('MAIL_USERNAME')
        smtp_password = current_app.config.get('MAIL_PASSWORD')
        use_tls = current_app.config.get('MAIL_USE_TLS', True)
        from_name = current_app.config.get('MAIL_FROM_NAME', 'Test Engineer Portal')
        
        # Validate configuration
        if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
            return {
                'success': False,
                'message': 'Email configuration is incomplete. Please check EMAIL_USER and EMAIL_PASSWORD in .env file'
            }
        
        # Type checking for smtp values
        if not isinstance(smtp_server, str):
            return {'success': False, 'message': 'Invalid MAIL_SERVER configuration'}
        if not isinstance(smtp_port, int):
            return {'success': False, 'message': 'Invalid MAIL_PORT configuration'}
        if not isinstance(smtp_username, str):
            return {'success': False, 'message': 'Invalid MAIL_USERNAME configuration'}
        if not isinstance(smtp_password, str):
            return {'success': False, 'message': 'Invalid MAIL_PASSWORD configuration'}
        
        # Prepare sender
        sender_email = from_email or smtp_username
        sender_display = f"{from_name} <{sender_email}>"
        
        # Handle multiple recipients
        if isinstance(to_email, list):
            recipients = [r for r in to_email if r]  # Filter empty strings
        else:
            recipients = [to_email] if to_email else []
        
        if not recipients:
            return {
                'success': False,
                'message': 'No valid recipients specified'
            }
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_display
        msg['To'] = ', '.join(recipients)
        
        if cc_emails:
            cc_list = [cc for cc in cc_emails if cc]
            if cc_list:
                msg['Cc'] = ', '.join(cc_list)
                recipients.extend(cc_list)
        
        # Attach HTML body
        html_part = MIMEText(body_html, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.set_debuglevel(0)  # Set to 1 for debugging
            
            if use_tls:
                server.starttls()
            
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to: {', '.join(recipients)}")
        
        return {
            'success': True,
            'message': f'Email sent successfully to {len(recipients)} recipient(s)'
        }
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = "Email authentication failed. Please check EMAIL_USER and EMAIL_PASSWORD."
        print(f"❌ {error_msg}")
        print(f"Details: {str(e)}")
        return {'success': False, 'message': error_msg}
        
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error occurred: {str(e)}"
        print(f"❌ {error_msg}")
        return {'success': False, 'message': error_msg}
        
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return {'success': False, 'message': error_msg}


def create_uat_email_body(record: dict, action: str = "created", portal_url: str = "") -> str:
    """
    Create HTML email body for UAT record notification
    
    Args:
        record: UAT record dictionary
        action: Action performed (created, updated, submitted, etc.)
        portal_url: URL to the portal (optional)
    
    Returns:
        str: HTML email body
    """
    action_colors = {
        "created": "#2196F3",
        "updated": "#FF9800",
        "submitted": "#4CAF50",
        "approved": "#4CAF50",
        "rejected": "#F44336"
    }
    
    action_color = action_colors.get(action.lower(), "#2196F3")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, {action_color} 0%, {action_color}dd 100%);
                color: white;
                padding: 30px 20px;
                text-align: center;
            }}
            .header h2 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .content {{
                padding: 30px 20px;
            }}
            .greeting {{
                font-size: 16px;
                margin-bottom: 20px;
            }}
            .record-details {{
                background-color: #f9f9f9;
                padding: 20px;
                margin: 20px 0;
                border-left: 4px solid {action_color};
                border-radius: 4px;
            }}
            .detail-row {{
                padding: 8px 0;
                border-bottom: 1px solid #eeeeee;
                display: flex;
                justify-content: space-between;
            }}
            .detail-row:last-child {{
                border-bottom: none;
            }}
            .label {{
                font-weight: 600;
                color: {action_color};
                min-width: 140px;
            }}
            .value {{
                color: #555;
                text-align: right;
                word-break: break-word;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: {action_color};
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: 600;
                transition: background-color 0.3s;
            }}
            .button:hover {{
                background-color: {action_color}dd;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background-color: #f9f9f9;
                border-top: 1px solid #eeeeee;
                font-size: 12px;
                color: #666;
            }}
            .footer p {{
                margin: 5px 0;
            }}
            .badge {{
                display: inline-block;
                padding: 4px 12px;
                background-color: {action_color};
                color: white;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🧪 Test Engineer Portal</h2>
                <p style="margin: 10px 0 0 0; opacity: 0.95;">UAT Record {action.capitalize()}</p>
            </div>
            
            <div class="content">
                <div class="greeting">
                    <p>Hello,</p>
                    <p>A UAT record has been <strong>{action}</strong> in the Test Engineer Portal.</p>
                </div>
                
                <div class="record-details">
                    <div class="detail-row">
                        <span class="label">Record ID:</span>
                        <span class="value">{record.get('id', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Test Case ID:</span>
                        <span class="value">{record.get('test_case_id', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Test Case Name:</span>
                        <span class="value">{record.get('test_case_name', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Status:</span>
                        <span class="value"><span class="badge">{record.get('status', 'N/A')}</span></span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Result:</span>
                        <span class="value">{record.get('result', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Tester:</span>
                        <span class="value">{record.get('tester_name', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Date:</span>
                        <span class="value">{record.get('test_date', 'N/A')}</span>
                    </div>
                    {f'''
                    <div class="detail-row">
                        <span class="label">Comments:</span>
                        <span class="value">{record.get('comments', 'N/A')}</span>
                    </div>
                    ''' if record.get('comments') else ''}
                </div>
                
                <p>Please review the details in the portal.</p>
                
                {f'<div style="text-align: center;"><a href="{portal_url}" class="button">View in Portal</a></div>' if portal_url else ''}
                
                <p style="margin-top: 20px; font-size: 14px; color: #666;">
                    <strong>Action taken:</strong> {action.capitalize()}<br>
                    <strong>Timestamp:</strong> {datetime.now().strftime('%d %b %Y %I:%M %p')}
                </p>
            </div>
            
            <div class="footer">
                <p><strong>Test Engineer Portal - Novo Nordisk</strong></p>
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>If you have questions, please contact your system administrator.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def create_allocation_email_body(allocation: dict, action: str = "created") -> str:
    """Create HTML email body for allocation notification"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
            .header {{ background-color: #667eea; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: white; padding: 20px; border-radius: 0 0 5px 5px; }}
            .record-details {{ background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-left: 4px solid #667eea; }}
            .detail-row {{ padding: 5px 0; }}
            .label {{ font-weight: bold; color: #667eea; }}
            .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Test Engineer Portal - Allocation {action.capitalize()}</h2>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>An allocation has been <strong>{action}</strong>.</p>
                
                <div class="record-details">
                    <div class="detail-row"><span class="label">Trial Number:</span> {allocation.get('trial_number', 'N/A')}</div>
                    <div class="detail-row"><span class="label">System:</span> {allocation.get('system', 'N/A')}</div>
                    <div class="detail-row"><span class="label">Therapeutic Area:</span> {allocation.get('therapeutic_area', 'N/A')}</div>
                    <div class="detail-row"><span class="label">Category:</span> {allocation.get('category', 'N/A')}</div>
                    <div class="detail-row"><span class="label">Assigned To:</span> {allocation.get('assigned_to', 'N/A')}</div>
                </div>
                
                <p>Please review the details in the portal.</p>
            </div>
            <div class="footer">
                <p>This is an automated message from Test Engineer Portal.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def create_change_request_email_body(cr: dict, action: str = "created") -> str:
    """Create HTML email body for change request notification"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
            .header {{ background-color: #764ba2; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: white; padding: 20px; border-radius: 0 0 5px 5px; }}
            .record-details {{ background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-left: 4px solid #764ba2; }}
            .detail-row {{ padding: 5px 0; }}
            .label {{ font-weight: bold; color: #764ba2; }}
            .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Test Engineer Portal - Change Request {action.capitalize()}</h2>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>A change request has been <strong>{action}</strong>.</p>
                
                <div class="record-details">
                    <div class="detail-row"><span class="label">CR Number:</span> {cr.get('cr_number', 'N/A')}</div>
                    <div class="detail-row"><span class="label">Trial Number:</span> {cr.get('trial_number', 'N/A')}</div>
                    <div class="detail-row"><span class="label">Category:</span> {cr.get('category', 'N/A')}</div>
                    <div class="detail-row"><span class="label">Version:</span> {cr.get('version', 'N/A')}</div>
                    <div class="detail-row"><span class="label">Status:</span> {cr.get('status', 'N/A')}</div>
                </div>
                
                <p>Please review the details in the portal.</p>
            </div>
            <div class="footer">
                <p>This is an automated message from Test Engineer Portal.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def test_email_connection() -> dict:
    """
    Test email configuration and connection
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        smtp_server = current_app.config.get('MAIL_SERVER')
        smtp_port = current_app.config.get('MAIL_PORT')
        smtp_username = current_app.config.get('MAIL_USERNAME')
        smtp_password = current_app.config.get('MAIL_PASSWORD')
        use_tls = current_app.config.get('MAIL_USE_TLS', True)
        
        if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
            return {
                'success': False,
                'message': 'Email configuration is incomplete'
            }
        
        # Type checking
        if not isinstance(smtp_server, str):
            return {'success': False, 'message': 'Invalid MAIL_SERVER configuration'}
        if not isinstance(smtp_port, int):
            return {'success': False, 'message': 'Invalid MAIL_PORT configuration'}
        if not isinstance(smtp_username, str):
            return {'success': False, 'message': 'Invalid MAIL_USERNAME configuration'}
        if not isinstance(smtp_password, str):
            return {'success': False, 'message': 'Invalid MAIL_PASSWORD configuration'}
        
        print(f"Testing connection to {smtp_server}:{smtp_port}...")
        
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.set_debuglevel(0)
            if use_tls:
                print("Starting TLS...")
                server.starttls()
            print("Logging in...")
            server.login(smtp_username, smtp_password)
        
        print("✅ Connection test successful!")
        return {
            'success': True,
            'message': 'Email connection test successful'
        }
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f'Authentication failed: {str(e)}'
        print(f"❌ {error_msg}")
        return {'success': False, 'message': error_msg}
    except Exception as e:
        error_msg = f'Connection test failed: {str(e)}'
        print(f"❌ {error_msg}")
        return {'success': False, 'message': error_msg}


def send_test_email(to_email: str) -> dict:
    """
    Send a test email to verify configuration
    
    Args:
        to_email: Recipient email address
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    subject = "Test Email - Test Engineer Portal"
    body = """
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #667eea;">✅ Test Email Successful!</h2>
        <p>This is a test email from the Test Engineer Portal.</p>
        <p>If you received this email, your email configuration is working correctly.</p>
        <hr>
        <p style="font-size: 12px; color: #666;">
            Sent at: {}</p>
    </body>
    </html>
    """.format(datetime.now().strftime('%d %b %Y %I:%M %p'))
    
    return send_email(to_email, subject, body)