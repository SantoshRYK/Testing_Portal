"""
Flask application for Test Engineer Portal
Converted from Streamlit
✅ WITH AUDIT REVIEWER SUPPORT
✅ WITH EMAIL CONFIGURATION
"""
from flask import Flask, render_template, redirect, url_for, session
import os
from dotenv import load_dotenv
from config import EmailConfig

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================
# Load email configuration from config.py
email_config = EmailConfig.get_config_dict()
for key, value in email_config.items():
    app.config[key] = value

print("\n" + "="*60)
print("📧 EMAIL CONFIGURATION")
print("="*60)
print(f"Email Enabled: {'✅ Yes' if EmailConfig.EMAIL_ENABLED else '❌ No'}")
print(f"SMTP Server: {EmailConfig.MAIL_SERVER}")
print(f"SMTP Port: {EmailConfig.MAIL_PORT}")
print(f"Email User: {EmailConfig.MAIL_USERNAME or '⚠️  Not configured'}")
print(f"Use TLS: {'✅ Yes' if EmailConfig.MAIL_USE_TLS else '❌ No'}")
if EmailConfig.is_configured():
    print("Status: ✅ Email is properly configured")
else:
    print("Status: ⚠️  Email configuration incomplete - Check .env file")
print("="*60 + "\n")

# Import blueprints
from blueprints.auth import auth_bp
from blueprints.home import home_bp

# Conditionally import other blueprints if they exist
try:
    from blueprints.allocations import allocations_bp
    HAS_ALLOCATIONS = True
except ImportError:
    HAS_ALLOCATIONS = False
    print("⚠️  Allocations blueprint not found - skipping")

try:
    from blueprints.audit import audit_bp
    HAS_AUDIT = True
except ImportError:
    HAS_AUDIT = False
    print("⚠️  Audit blueprint not found - skipping")

try:
    from blueprints.quality import quality_bp
    HAS_QUALITY = True
except ImportError:
    HAS_QUALITY = False
    print("⚠️  Quality blueprint not found - skipping")

try:
    from blueprints.uat import uat_bp
    HAS_UAT = True
except ImportError:
    HAS_UAT = False
    print("⚠️  UAT blueprint not found - skipping")

try:
    from blueprints.change_request import change_request_bp
    HAS_CHANGE_REQUEST = True
except ImportError:
    HAS_CHANGE_REQUEST = False
    print("⚠️  Change Request blueprint not found - skipping")

try:
    from blueprints.admin import admin_bp
    HAS_ADMIN = True
except ImportError:
    HAS_ADMIN = False
    print("⚠️  Admin blueprint not found - skipping")

# Register core blueprints (always required)
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)

# Register optional blueprints if available
if HAS_ALLOCATIONS:
    app.register_blueprint(allocations_bp, url_prefix='/allocations')
    print("✅ Allocations module loaded")

if HAS_AUDIT:
    app.register_blueprint(audit_bp, url_prefix='/audit')
    print("✅ Audit module loaded")

if HAS_QUALITY:
    app.register_blueprint(quality_bp, url_prefix='/quality')
    print("✅ Quality module loaded")

if HAS_UAT:
    app.register_blueprint(uat_bp, url_prefix='/uat')
    print("✅ UAT module loaded")

if HAS_CHANGE_REQUEST:
    app.register_blueprint(change_request_bp, url_prefix='/change-requests')
    print("✅ Change Request module loaded")

if HAS_ADMIN:
    app.register_blueprint(admin_bp, url_prefix='/admin')
    print("✅ Admin module loaded")

# ============================================================================
# ROUTES
# ============================================================================
@app.route('/')
def root():
    """Root route - redirect based on login status"""
    if 'user' in session:
        return redirect(url_for('home.index'))
    return redirect(url_for('auth.login'))

@app.route('/index')
def index():
    """Legacy index route (for backward compatibility)"""
    if 'user' in session:
        return redirect(url_for('home.index'))
    return redirect(url_for('auth.login'))

# ============================================================================
# ERROR HANDLERS
# ============================================================================
@app.errorhandler(403)
def forbidden(e):
    """403 Forbidden handler"""
    try:
        return render_template('errors/403.html'), 403
    except:
        return '''
        <html>
        <head><title>403 Forbidden</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>403 - Forbidden</h1>
            <p>You don't have permission to access this resource.</p>
            <a href="/">Go Home</a>
        </body>
        </html>
        ''', 403

@app.errorhandler(404)
def not_found(e):
    """404 Not Found handler"""
    try:
        return render_template('errors/404.html'), 404
    except:
        return '''
        <html>
        <head><title>404 Not Found</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>404 - Page Not Found</h1>
            <p>The page you're looking for doesn't exist.</p>
            <a href="/">Go Home</a>
        </body>
        </html>
        ''', 404

@app.errorhandler(500)
def server_error(e):
    """500 Server Error handler"""
    import traceback
    print("="*60)
    print("SERVER ERROR:")
    print(traceback.format_exc())
    print("="*60)
    
    try:
        return render_template('errors/500.html'), 500
    except:
        return '''
        <html>
        <head><title>500 Server Error</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>500 - Server Error</h1>
            <p>Something went wrong on our end.</p>
            <a href="/">Go Home</a>
        </body>
        </html>
        ''', 500

# ============================================================================
# CONTEXT PROCESSORS
# ============================================================================
@app.context_processor
def inject_user():
    """Inject user into all templates"""
    user = session.get('user')
    return dict(
        user=user,
        current_user=user
    )

# ============================================================================
# TEMPLATE FILTERS
# ============================================================================
@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """Format datetime string"""
    if value:
        try:
            from datetime import datetime
            if isinstance(value, str):
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime(format)
            return value.strftime(format)
        except:
            return value
    return ''

@app.template_filter('date')
def format_date(value):
    """Format date string"""
    return format_datetime(value, '%Y-%m-%d')

@app.template_filter('time')
def format_time(value):
    """Format time string"""
    return format_datetime(value, '%H:%M:%S')

# ============================================================================
# CLI COMMANDS
# ============================================================================
@app.cli.command()
def init_db():
    """Initialize the database with default data"""
    print("Initializing database...")
    from services.user_service import _ensure_data_file
    _ensure_data_file()
    print("✅ Database initialized!")
    print("📋 Default admin user created:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   Email: admin@novotest.com")
    print("   Role: superuser")
    print("   Audit Reviewer: Yes")

@app.cli.command()
def create_admin():
    """Create or reset admin user"""
    from services.user_service import create_user, get_user_by_username
    
    print("Creating/Resetting admin user...")
    
    # Check if admin exists
    existing_admin = get_user_by_username('admin')
    
    if existing_admin:
        print("⚠️  Admin user already exists!")
        response = input("Do you want to reset the admin password? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ Aborted.")
            return
        
        # Delete existing admin
        from services.user_service import delete_user
        delete_user('admin')
        print("🗑️  Existing admin deleted.")
    
    # Create new admin user
    success, message = create_user(
        username='admin',
        email='admin@novotest.com',
        password='admin123',
        role='superuser',
        created_by='system'
    )
    
    if success:
        # Manually enable audit reviewer access
        from services.user_service import _load_users, _save_users
        users = _load_users()
        if 'admin' in users:
            users['admin']['is_audit_reviewer'] = True
            _save_users(users)
        
        print("✅ Admin user created successfully!")
        print("="*60)
        print("📋 Admin Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Email: admin@novotest.com")
        print("   Role: superuser")
        print("   Audit Reviewer: Yes ✅")
        print("="*60)
    else:
        print(f"❌ Failed: {message}")

@app.cli.command()
def list_users():
    """List all users"""
    from services.user_service import get_all_users
    
    print("\n" + "="*60)
    print("👥 ALL USERS")
    print("="*60)
    
    users = get_all_users()
    
    if not users:
        print("📭 No users found.")
        return
    
    for username, user_data in users.items():
        role = user_data.get('role', 'user')
        email = user_data.get('email', 'N/A')
        status = user_data.get('status', 'active')
        is_reviewer = user_data.get('is_audit_reviewer', False)
        
        role_emoji = {
            'superuser': '👑',
            'admin': '🔧',
            'manager': '👨‍💼',
            'user': '👤',
            'cdp': '📊'
        }.get(role, '👤')
        
        reviewer_badge = ' 🔍' if is_reviewer else ''
        status_badge = '✅' if status == 'active' else '❌'
        
        print(f"\n{role_emoji} {username}{reviewer_badge}")
        print(f"   Email: {email}")
        print(f"   Role: {role}")
        print(f"   Status: {status_badge} {status}")
        if is_reviewer:
            print(f"   Audit Reviewer: Yes ✅")
    
    print("\n" + "="*60)
    print(f"Total Users: {len(users)}")
    print("="*60 + "\n")

@app.cli.command()
def enable_audit_reviewer():
    """Enable audit reviewer access for a user"""
    from services.user_service import approve_audit_reviewer, get_user_by_username
    
    username = input("Enter username: ").strip()
    
    user = get_user_by_username(username)
    
    if not user:
        print(f"❌ User '{username}' not found!")
        return
    
    if user.get('is_audit_reviewer'):
        print(f"ℹ️  User '{username}' already has audit reviewer access.")
        return
    
    success, message = approve_audit_reviewer(username, 'system')
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

@app.cli.command()
def test_email():
    """Test email configuration"""
    from utils.email_handler import test_email_connection, send_test_email
    
    print("\n" + "="*60)
    print("📧 TESTING EMAIL CONFIGURATION")
    print("="*60)
    
    # Test connection
    print("\n1️⃣ Testing SMTP connection...")
    with app.app_context():
        result = test_email_connection()
    
    if result['success']:
        print(f"   ✅ {result['message']}")
        
        # Ask to send test email
        send_test = input("\n2️⃣ Do you want to send a test email? (yes/no): ")
        
        if send_test.lower() == 'yes':
            to_email = input("   Enter recipient email address: ").strip()
            
            if to_email:
                print(f"   Sending test email to {to_email}...")
                with app.app_context():
                    result = send_test_email(to_email)
                
                if result['success']:
                    print(f"   ✅ {result['message']}")
                else:
                    print(f"   ❌ {result['message']}")
            else:
                print("   ❌ Invalid email address")
    else:
        print(f"   ❌ {result['message']}")
    
    print("\n" + "="*60 + "\n")

# ============================================================================
# MAIN
# ============================================================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 TestingHub Portal - Flask Application")
    print("="*60)
    print("📋 Registered Blueprints:")
    print("   ✅ Authentication (auth)")
    print("   ✅ Home (home)")
    
    if HAS_ALLOCATIONS:
        print("   ✅ Allocations")
    if HAS_AUDIT:
        print("   ✅ Audit")
    if HAS_QUALITY:
        print("   ✅ Quality")
    if HAS_UAT:
        print("   ✅ UAT")
    if HAS_CHANGE_REQUEST:
        print("   ✅ Change Requests")
    if HAS_ADMIN:
        print("   ✅ Admin")
    
    print("\n🌐 Starting development server...")
    print("   URL: http://localhost:5000")
    print("   Login: admin / admin123")
    print("="*60 + "\n")
    
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)