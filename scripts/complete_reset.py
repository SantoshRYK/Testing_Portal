# scripts/complete_reset.py
"""
Complete System Reset Script for Test Engineer Portal
⚠️ DANGER: This will reset ALL data to default state!
Requires SUPERUSER authentication
Creates automatic backup before reset
"""
import os
import json
import hashlib
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    """Load existing users from users.json"""
    users_file = Path('data/users.json')
    if not users_file.exists():
        return {}
    try:
        with open(users_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading users: {e}")
        return {}


def authenticate_superuser():
    """Authenticate current superuser before reset"""
    print("\n🔐 SUPERUSER AUTHENTICATION REQUIRED")
    print("=" * 70)
    print("⚠️  You must authenticate as an existing SUPERUSER to proceed")
    print("=" * 70)
    
    users = load_users()
    
    if not users:
        print("\n❌ No users found in database!")
        print("   Cannot verify superuser credentials.")
        response = input("\n⚠️  Proceed anyway? Type 'FORCE RESET' to continue: ")
        if response == 'FORCE RESET':
            return True, None
        return False, None
    
    # Show available superusers
    superusers = [username for username, data in users.items()
                  if data.get('role', '').lower() == 'superuser']
    
    if not superusers:
        print("\n⚠️  No superuser accounts found!")
        print("   Found users:", list(users.keys()))
        response = input("\n⚠️  Proceed anyway? Type 'FORCE RESET' to continue: ")
        if response == 'FORCE RESET':
            return True, None
        return False, None
    
    print(f"\n📋 Found {len(superusers)} superuser account(s):")
    for su in superusers:
        user_data = users[su]
        print(f"   - {su} ({user_data.get('email', 'no email')})")
    
    # Authentication attempts
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔑 Authentication Attempt {attempt}/{max_attempts}")
        print("-" * 70)
        
        username = input("Enter superuser username: ").strip()
        password = input("Enter superuser password: ").strip()
        
        # Verify credentials
        if username in users:
            user_data = users[username]
            stored_password = user_data.get('password', '')
            input_password_hash = hash_password(password)
            
            # Check if user is superuser
            if user_data.get('role', '').lower() != 'superuser':
                print(f"❌ User '{username}' is not a superuser!")
                print(f"   Role: {user_data.get('role', 'Unknown')}")
                continue
            
            # Check password
            if stored_password == input_password_hash:
                print(f"✅ Authentication successful! Welcome, {username}")
                return True, username
            else:
                print("❌ Invalid password!")
        else:
            print(f"❌ User '{username}' not found!")
        
        if attempt < max_attempts:
            print(f"\n⚠️  {max_attempts - attempt} attempt(s) remaining")
    
    print("\n❌ Maximum authentication attempts reached!")
    print("   Reset operation cancelled for security.")
    return False, None


def create_emergency_backup():
    """Create emergency backup before reset"""
    try:
        data_dir = Path('data')
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)
        
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_folder = backup_dir / f'emergency_reset_backup_{backup_timestamp}'
        
        # Copy entire data folder
        if data_dir.exists():
            shutil.copytree(data_dir, backup_folder)
            print(f"✅ Emergency backup created: {backup_folder}")
            return True, backup_folder
        else:
            print("⚠️ No data directory found to backup")
            return False, None
    except Exception as e:
        print(f"❌ Emergency backup failed: {e}")
        return False, None


def complete_reset():
    """
    Complete reset for Test Engineer Portal
    Requires SUPERUSER authentication before deletion
    Creates automatic backup before reset
    """
    print("=" * 70)
    print("🔥 COMPLETE DATA RESET - TEST ENGINEER PORTAL")
    print("=" * 70)
    print("\n⚠️  WARNING: This will DELETE ALL:")
    print("   ❌ allocations.json (all items)")
    print("   ❌ audit_logs.json (all items)")
    print("   ❌ quality_records.json (all items)")
    print("   ❌ trail_documents.json (all items)")
    print("   ❌ change_requests.json (all items)")
    print("   ❌ uat_records.json (all items)")
    print("   ❌ password_reset_requests.json (all items)")
    print("   ❌ pending_users.json (all items)")
    print("   ❌ users.json (ALL USERS including current superuser)")
    print("   ℹ️  email_config.json will be preserved")
    print("\n   ✅ Create fresh empty data files")
    print("   ✅ Create ONE new SUPERUSER only")
    print("\n" + "=" * 70)
    
    # First confirmation
    response = input("\nType 'DELETE EVERYTHING' to confirm: ")
    if response != 'DELETE EVERYTHING':
        print("❌ Reset cancelled - no changes made")
        return 0
    
    # Authenticate superuser
    authenticated, auth_username = authenticate_superuser()
    if not authenticated:
        print("\n❌ Authentication failed - Reset cancelled")
        print("   No changes were made to the database")
        return 1
    
    # Show who is performing the reset
    if auth_username:
        print(f"\n✅ Authenticated as: {auth_username}")
        print(f"   Proceeding with reset operation...")
    
    # Final confirmation after authentication
    print("\n" + "=" * 70)
    print("⚠️  FINAL CONFIRMATION")
    print("=" * 70)
    print("This is your LAST CHANCE to cancel!")
    print("ALL data will be PERMANENTLY DELETED!")
    
    final_confirm = input("\nType 'YES DELETE NOW' to proceed: ")
    if final_confirm != 'YES DELETE NOW':
        print("❌ Reset cancelled - no changes made")
        return 0
    
    try:
        # Define paths
        data_dir = Path('data')
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)
        
        # Files to reset
        files_to_reset = [
            'allocations.json',
            'audit_logs.json',
            'password_reset_requests.json',
            'pending_users.json',
            'quality_records.json',
            'trail_documents.json',
            'change_requests.json',
            'uat_records.json',
            'users.json'
        ]
        
        # Files to preserve
        files_to_preserve = ['email_config.json']
        
        # Step 1: Create emergency backup
        print("\n📦 Step 1: Creating emergency backup...")
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_folder = backup_dir / f'emergency_reset_backup_{backup_timestamp}'
        backup_folder.mkdir(parents=True, exist_ok=True)
        
        # Log who performed the reset
        reset_log = {
            "reset_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "authenticated_by": auth_username if auth_username else "FORCED",
            "files_deleted": files_to_reset,
            "files_preserved": files_to_preserve
        }
        
        with open(backup_folder / 'reset_log.json', 'w') as f:
            json.dump(reset_log, f, indent=4)
        
        backup_count = 0
        for json_file in files_to_reset + files_to_preserve:
            file_path = data_dir / json_file
            if file_path.exists():
                shutil.copy2(file_path, backup_folder / json_file)
                print(f"   ✅ Backed up: {json_file}")
                backup_count += 1
        
        print(f"   ✅ Total files backed up: {backup_count}")
        print(f"   📁 Backup location: {backup_folder}")
        print(f"   📋 Reset performed by: {auth_username if auth_username else 'FORCED'}")
        
        # Step 2: Get new superuser credentials
        print("\n👤 Step 2: Set up new SUPERUSER credentials")
        print("-" * 70)
        
        # Username
        while True:
            username = input("Enter new superuser username (default: superuser): ").strip()
            if not username:
                username = "superuser"
            if len(username) >= 3:
                break
            print("   ⚠️  Username must be at least 3 characters")
        
        # Password
        while True:
            password = input("Enter new superuser password (min 8 chars): ").strip()
            if len(password) >= 8:
                password_confirm = input("Confirm password: ").strip()
                if password == password_confirm:
                    break
                else:
                    print("   ⚠️  Passwords don't match, try again")
            else:
                print("   ⚠️  Password must be at least 8 characters")
        
        # Email
        email = input("Enter new superuser email (default: superuser@testportal.com): ").strip()
        if not email:
            email = "superuser@testportal.com"
        
        # Step 3: Delete old data files
        print("\n🗑️  Step 3: Deleting old data files...")
        deleted_count = 0
        for json_file in files_to_reset:
            file_path = data_dir / json_file
            if file_path.exists():
                os.remove(file_path)
                print(f"   ✅ Deleted: {json_file}")
                deleted_count += 1
        
        print(f"   ✅ Total files deleted: {deleted_count}")
        
        # Step 4: Create new users.json with ONE SUPERUSER
        print("\n👤 Step 4: Creating new SUPERUSER...")
        users_data = {
            username: {
                "password": hash_password(password),
                "email": email,
                "role": "superuser",
                "status": "active",
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        with open(data_dir / 'users.json', 'w') as f:
            json.dump(users_data, f, indent=4)
        
        print("   ✅ users.json created with ONE SUPERUSER")
        
        # Step 5: Create empty data files
        print("\n📄 Step 5: Creating empty data files...")
        empty_files = {
            'allocations.json': [],
            'audit_logs.json': [],
            'quality_records.json': [],
            'trail_documents.json': [],
            'change_requests.json': [],
            'uat_records.json': [],
            'password_reset_requests.json': [],
            'pending_users.json': []
        }
        
        for filename, content in empty_files.items():
            with open(data_dir / filename, 'w') as f:
                json.dump(content, f, indent=4)
            print(f"   ✅ Created: {filename} (empty)")
        
        # Step 6: Preserve email config
        print("\n📧 Step 6: Email configuration status...")
        email_config_path = data_dir / 'email_config.json'
        if email_config_path.exists():
            print("   ✅ email_config.json preserved (not deleted)")
        else:
            print("   ℹ️  email_config.json not found (will be created by app)")
        
        # Step 7: Save credentials to file
        print("\n💾 Step 7: Saving credentials...")
        creds_file = backup_folder / f'NEW_SUPERUSER_CREDENTIALS.txt'
        with open(creds_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("TEST ENGINEER PORTAL - NEW SUPERUSER CREDENTIALS\n")
            f.write("=" * 70 + "\n")
            f.write(f"Reset Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Reset Performed By: {auth_username if auth_username else 'FORCED'}\n\n")
            f.write(f"Username:  {username}\n")
            f.write(f"Password:  {password}\n")
            f.write(f"Email:     {email}\n")
            f.write(f"Role:      superuser\n")
            f.write(f"Status:    active\n\n")
            f.write("=" * 70 + "\n")
            f.write("IMPORTANT NOTES:\n")
            f.write("- This is the ONLY user in the system\n")
            f.write("- Role: superuser (lowercase)\n")
            f.write("- Status: active\n")
            f.write("- All previous data has been deleted\n")
            f.write("- Change password after first login\n")
            f.write(f"- Backup location: {backup_folder}\n")
            f.write("=" * 70 + "\n")
        
        print(f"   ✅ Credentials saved to: {creds_file}")
        
        # Step 8: Success message
        print("\n" + "=" * 70)
        print("✅ COMPLETE RESET SUCCESSFUL!")
        print("=" * 70)
        print("\n🔐 New SUPERUSER Credentials:")
        print(f"   Username:  {username}")
        print(f"   Password:  {password}")
        print(f"   Email:     {email}")
        print(f"   Role:      superuser")
        print(f"   Status:    active")
        print("\n⚠️  IMPORTANT: Save these credentials securely!")
        print("=" * 70)
        
        # Step 9: Summary
        print("\n📊 Reset Summary:")
        print("-" * 70)
        print(f"   Reset performed by: {auth_username if auth_username else 'FORCED'}")
        print("   Data Status:")
        print("   ├── users.json ................. 1 user (superuser)")
        print("   ├── allocations.json ........... 0 items")
        print("   ├── audit_logs.json ............ 0 items")
        print("   ├── quality_records.json ....... 0 items")
        print("   ├── trail_documents.json ....... 0 items")
        print("   ├── change_requests.json ....... 0 items")
        print("   ├── uat_records.json ........... 0 items")
        print("   ├── password_reset_requests.json  0 items")
        print("   ├── pending_users.json ......... 0 items")
        print("   └── email_config.json .......... PRESERVED")
        print("-" * 70)
        print(f"   📁 Backup: {backup_folder}")
        print(f"   📄 Credentials: {creds_file}")
        print("=" * 70)
        
        print("\n🚀 Next Steps:")
        print("   1. Start your Streamlit app: streamlit run app.py")
        print("   2. Login with new SUPERUSER credentials")
        print("   3. Change password immediately (recommended)")
        print("   4. Create new users:")
        print("      - Admin users")
        print("      - Manager users")
        print("      - CDP users (for Change Request Tracker)")
        print("      - Regular Test Engineer users")
        print("=" * 70)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(complete_reset())
    except KeyboardInterrupt:
        print("\n\n❌ Reset cancelled by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)